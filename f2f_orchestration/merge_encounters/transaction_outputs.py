"""Normalized, source-agnostic view of one transaction's agent outputs.

``TransactionOutputs`` is the single bundle the merge engine consumes. It holds
plain, JSON-serializable data only, so it can be produced from any of three
origins and then fed to the same pure engine:

- :meth:`TransactionOutputs.from_mapping` — plain dicts (framework-agnostic; the
  Temporal / external-orchestrator path).
- :meth:`TransactionOutputs.from_disk` — the ``outputs/<txn>/`` ``*-results.json``
  files written by :class:`ResultStore`.

Both loaders yield the identical shape, so the key builders are written once and
work for either. This module performs no verdict logic and no evidence
resolution — it only loads and normalizes.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.detection import AgentName

# Per-encounter F2F agents that the merge engine reads. Classification and the
# document-level poc extraction are handled separately (they are not per-encounter
# agent outputs), so they are excluded from the ``agents`` map.
PER_ENCOUNTER_AGENTS: tuple[AgentName, ...] = (
    AgentName.ENCOUNTER_IDENTITY,
    AgentName.PRIMARY_DIAGNOSIS,
    AgentName.SKILLED_SERVICES,
    AgentName.HOMEBOUND,
    AgentName.INPATIENT_DETECTION,
    AgentName.TELEHEALTH_IDENTITY,
    AgentName.SURGICAL_NOTE,
)

_POC_EXTRACTION_DIRNAME = "poc_485_extraction"
_POC_EXTRACTION_FILENAME = "results.json"
_CLASSIFICATION_DIRNAME = "classification"
_F2F_CLASSIFICATION_FILENAME = "f2f.json"
_ENCOUNTER_FILE_RE = re.compile(r"^encounter_(\d+)-results\.json$")

# Last-resort client id when none is present in any loaded output. Explicit here
# (not silently applied elsewhere) so the fallback is visible and greppable.
_UNKNOWN_CLIENT_ID = "DEFAULT"


@dataclass(frozen=True)
class TransactionOutputs:
    """All agent outputs for one transaction, normalized for the merge engine.

    Attributes:
        transaction_id: The transaction identifier.
        client_id: Client identifier (drives client-scoped display).
        poc_extraction: Processed poc-485 extraction result envelope, or ``None``.
        classification_f2f: Processed F2F classification result, or ``None``.
        agents: ``{agent_name: {encounter_index: processed_output}}`` for the
            per-encounter F2F agents. Absent agents/encounters are simply missing
            keys (never fabricated).
    """

    transaction_id: str
    client_id: str
    poc_extraction: dict[str, Any] | None
    classification_f2f: dict[str, Any] | None
    agents: dict[str, dict[int, dict[str, Any]]]

    # -- Loaders ---------------------------------------------------------------

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TransactionOutputs":
        """Build from a plain mapping (the framework-agnostic / Temporal path).

        Expected keys: ``transaction_id`` (str), ``client_id`` (str, optional),
        ``poc_extraction`` (dict | None), ``classification_f2f`` (dict | None),
        ``agents`` (``{agent_name: {encounter_index: dict}}``; encounter keys may
        be str or int).
        """
        transaction_id = payload.get("transaction_id")
        if not transaction_id:
            raise ValueError("payload is missing required 'transaction_id'.")

        poc_extraction = payload.get("poc_extraction")
        classification_f2f = payload.get("classification_f2f")
        agents = _normalize_agents(payload.get("agents") or {})
        client_id = (
            payload.get("client_id")
            or _derive_client_id(poc_extraction, classification_f2f, agents)
        )
        return cls(
            transaction_id=str(transaction_id),
            client_id=client_id,
            poc_extraction=poc_extraction,
            classification_f2f=classification_f2f,
            agents=agents,
        )

    @classmethod
    def from_disk(cls, outputs_dir: Path, transaction_id: str) -> "TransactionOutputs":
        """Build by reading the ``outputs/<transaction_id>/`` processed files.

        Missing files mean "that agent/encounter did not run" and yield absent
        keys. A file that exists but cannot be parsed raises, so corruption is
        surfaced rather than silently dropped.
        """
        transaction_dir = outputs_dir / transaction_id
        if not transaction_dir.is_dir():
            raise FileNotFoundError(f"Transaction output directory not found: {transaction_dir}")

        poc_extraction = _read_json_or_none(
            transaction_dir / _POC_EXTRACTION_DIRNAME / _POC_EXTRACTION_FILENAME
        )
        classification_f2f = _read_json_or_none(
            transaction_dir / _CLASSIFICATION_DIRNAME / _F2F_CLASSIFICATION_FILENAME
        )
        agents = _load_agents_from_disk(transaction_dir)
        client_id = _derive_client_id(poc_extraction, classification_f2f, agents)
        return cls(
            transaction_id=transaction_id,
            client_id=client_id,
            poc_extraction=poc_extraction,
            classification_f2f=classification_f2f,
            agents=agents,
        )

    # -- Accessors -------------------------------------------------------------

    def encounter_list(self) -> list[dict[str, Any]]:
        """Return the classification encounters, ordered by ``encounter_index``.

        The F2F classification is the authoritative encounter roster. If it is
        absent, fall back to the encounter indices present across agent outputs so
        the engine can still enumerate encounters.
        """
        if self.classification_f2f:
            encounters = self.classification_f2f.get("encounters") or []
            return sorted(encounters, key=lambda enc: enc.get("encounter_index", 0))
        return [{"encounter_index": index} for index in self.encounter_indices()]

    def encounter_indices(self) -> list[int]:
        """Return every encounter index known to this transaction, sorted."""
        indices: set[int] = set()
        if self.classification_f2f:
            for encounter in self.classification_f2f.get("encounters") or []:
                index = encounter.get("encounter_index")
                if isinstance(index, int):
                    indices.add(index)
        for per_encounter in self.agents.values():
            indices.update(per_encounter)
        return sorted(indices)

    def agent(self, agent_name: str, encounter_index: int) -> dict[str, Any] | None:
        """Return one agent's processed output for one encounter, or ``None``."""
        return self.agents.get(agent_name, {}).get(encounter_index)

    def has_agent(self, agent_name: str) -> bool:
        """Return whether any encounter has output for ``agent_name``."""
        return bool(self.agents.get(agent_name))


# -- Module helpers ------------------------------------------------------------


def _read_json_or_none(path: Path) -> dict[str, Any] | None:
    """Read and parse a JSON object, returning ``None`` if the file is absent.

    A present-but-unparseable file raises ``ValueError`` with the path, so
    corruption is never silently swallowed.
    """
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Failed to parse JSON at {path}: {error}") from error


def _load_agents_from_disk(transaction_dir: Path) -> dict[str, dict[int, dict[str, Any]]]:
    """Load ``{agent_name: {encounter_index: processed}}`` from disk."""
    agents: dict[str, dict[int, dict[str, Any]]] = {}
    for agent in PER_ENCOUNTER_AGENTS:
        agent_dir = transaction_dir / agent.value
        if not agent_dir.is_dir():
            continue
        per_encounter: dict[int, dict[str, Any]] = {}
        for result_file in sorted(agent_dir.glob("encounter_*-results.json")):
            match = _ENCOUNTER_FILE_RE.match(result_file.name)
            if match is None:
                continue
            parsed = _read_json_or_none(result_file)
            if parsed is not None:
                per_encounter[int(match.group(1))] = parsed
        if per_encounter:
            agents[agent.value] = per_encounter
    return agents


def _normalize_agents(
    raw_agents: Mapping[str, Mapping[Any, Mapping[str, Any]]],
) -> dict[str, dict[int, dict[str, Any]]]:
    """Coerce a raw ``agents`` mapping so encounter keys are ints."""
    agents: dict[str, dict[int, dict[str, Any]]] = {}
    for agent_name, per_encounter in raw_agents.items():
        normalized: dict[int, dict[str, Any]] = {}
        for raw_index, output in (per_encounter or {}).items():
            normalized[int(raw_index)] = output
        agents[agent_name] = normalized
    return agents


def _derive_client_id(
    poc_extraction: Mapping[str, Any] | None,
    classification_f2f: Mapping[str, Any] | None,
    agents: Mapping[str, Mapping[int, Mapping[str, Any]]],
) -> str:
    """Derive ``client_id`` from any available output, else the unknown fallback.

    Order of preference: poc extraction, then F2F classification, then the first
    agent output found. Falls back to ``_UNKNOWN_CLIENT_ID`` only if none carry it.
    """
    for source in (poc_extraction, classification_f2f):
        client_id = (source or {}).get("client_id")
        if client_id:
            return str(client_id)
    for per_encounter in agents.values():
        for output in per_encounter.values():
            client_id = (output or {}).get("client_id")
            if client_id:
                return str(client_id)
    return _UNKNOWN_CLIENT_ID
