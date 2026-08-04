"""Assemble the ``audit-results`` contract from one transaction's outputs.

:class:`AuditEngine` is the pure core: given a :class:`TransactionOutputs` and a
``generated_at`` timestamp, it emits the stable envelope, runs every key builder in
registry order, and derives a ``data_quality`` section. It performs no I/O, reads no
environment, and reads no clock — so it is deterministic and safe to run inside any
orchestrator (including a Temporal activity).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..core.detection import EncounterAgentSelector
from .evidence_resolver import EvidenceResolver
from .key_builders import BUILDERS, AuditKeyBuilder
from .transaction_outputs import TransactionOutputs

PARAMETER_ID = "audit_results"
_DEFAULT_SCHEMA_VERSION = "1.0"

# Document-level (non per-encounter) outputs whose validation blocks are surfaced.
_DOCUMENT_AGENTS: tuple[str, ...] = ("poc-485-extraction", "classification")


class AuditEngine:
    """Builds the consolidated ``audit-results`` dict for one transaction."""

    def __init__(
        self,
        *,
        schema_version: str = _DEFAULT_SCHEMA_VERSION,
        builders: Sequence[AuditKeyBuilder] = BUILDERS,
        resolver: EvidenceResolver | None = None,
        selector: EncounterAgentSelector | None = None,
    ) -> None:
        self._schema_version = schema_version
        self._builders = tuple(builders)
        self._resolver = resolver or EvidenceResolver()
        self._selector = selector or EncounterAgentSelector()

    def build(self, outputs: TransactionOutputs, *, generated_at: str) -> dict[str, Any]:
        """Return the full ``audit-results`` dict. ``generated_at`` is injected (ISO 8601)."""
        results = {builder.key: builder.build(outputs, self._resolver) for builder in self._builders}
        return {
            "schema_version": self._schema_version,
            "parameter_id": PARAMETER_ID,
            "client_id": outputs.client_id,
            "transaction_id": outputs.transaction_id,
            "generated_at": generated_at,
            "results": results,
            "data_quality": self._collect_data_quality(outputs),
        }

    # -- data quality ----------------------------------------------------------

    def _collect_data_quality(self, outputs: TransactionOutputs) -> dict[str, Any]:
        """Surface gaps so a false PASS is never shown for incomplete data.

        ``failed_agents`` maps an agent to the encounter indices where an *expected*
        agent (per the classification-driven selector) produced no output or a
        ``critical`` validation. ``schema_issues`` lists every non-empty validation
        signal (missing / repaired / dangling) across per-encounter and
        document-level outputs.
        """
        failed_agents: dict[str, list[int]] = {}
        schema_issues: list[dict[str, Any]] = []

        for encounter in outputs.encounter_list():
            index = encounter.get("encounter_index")
            if index is None:
                continue
            for agent in self._selector.select(encounter):
                agent_name = agent.value
                output = outputs.agent(agent_name, index)
                if output is None:
                    failed_agents.setdefault(agent_name, []).append(index)
                    continue
                validation = output.get("validation") or {}
                if validation.get("critical"):
                    failed_agents.setdefault(agent_name, []).append(index)
                issue = _validation_issue(agent_name, index, validation)
                if issue is not None:
                    schema_issues.append(issue)

        for agent_name, document in (
            (_DOCUMENT_AGENTS[0], outputs.poc_extraction),
            (_DOCUMENT_AGENTS[1], outputs.classification_f2f),
        ):
            if document:
                issue = _validation_issue(agent_name, None, document.get("validation") or {})
                if issue is not None:
                    schema_issues.append(issue)

        return {
            "failed_agents": {name: sorted(indices) for name, indices in sorted(failed_agents.items())},
            "schema_issues": schema_issues,
        }


def _validation_issue(
    agent_name: str, encounter_index: int | None, validation: dict[str, Any]
) -> dict[str, Any] | None:
    """Build a schema-issue record if a validation block has any non-empty signal."""
    missing_keys = validation.get("missing_keys") or []
    repaired_keys = validation.get("repaired_keys") or []
    dangling_refs = validation.get("dangling_refs") or []
    if not (missing_keys or repaired_keys or dangling_refs):
        return None
    return {
        "agent": agent_name,
        "encounter_index": encounter_index,
        "missing_keys": missing_keys,
        "repaired_keys": repaired_keys,
        "dangling_refs": dangling_refs,
    }
