"""Shared contract and helpers for audit key builders.

Each audit topic (``timely_encounter``, ``primary_hh_reason``, ...) is produced by
one small :class:`AuditKeyBuilder`. A builder returns a ``{poc_485, f2f_encounters}``
object; the engine assembles them under ``results``. Builders are pure functions of
``TransactionOutputs`` + :class:`EvidenceResolver` — no I/O, no verdicts.

This module holds only the protocol and the helpers common to several builders, so
each builder stays focused on its own field mapping.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from ..evidence_resolver import EvidenceResolver
from ..transaction_outputs import TransactionOutputs


@runtime_checkable
class AuditKeyBuilder(Protocol):
    """One audit topic. ``key`` is the top-level name under ``results``."""

    key: str

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]: ...


def dget(node: Any, *path: str, default: Any = None) -> Any:
    """Safely walk nested mappings; return ``default`` on any missing/non-dict hop."""
    current = node
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def build_f2f_encounters(
    outputs: TransactionOutputs,
    agent_name: str,
    present: Callable[[int, dict[str, Any]], dict[str, Any]],
    absent: Callable[[int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the per-encounter list for one agent, over the full encounter roster.

    Every encounter from the classification roster is included, in order. When the
    agent produced output for an encounter, ``present(index, output)`` maps it;
    otherwise ``absent(index)`` supplies the null-valued entry. This keeps encounter
    indices aligned across every audit key and never silently drops an encounter.
    """
    encounters: list[dict[str, Any]] = []
    for encounter in outputs.encounter_list():
        index = encounter.get("encounter_index")
        if index is None:
            continue
        output = outputs.agent(agent_name, index)
        encounters.append(present(index, output) if output is not None else absent(index))
    return encounters


def reasoning_block(
    agent_output: dict[str, Any],
    resolver: EvidenceResolver,
    *,
    include_status: bool,
) -> dict[str, Any]:
    """Project ``reasoning`` to ``{status?, summary, missing, evidence}`` with resolved evidence."""
    reasoning = dget(agent_output, "reasoning", default={}) or {}
    block: dict[str, Any] = {}
    if include_status:
        block["status"] = reasoning.get("status")
    block["summary"] = reasoning.get("summary")
    block["missing"] = reasoning.get("missing")
    block["evidence"] = resolver.resolve_agent_refs(agent_output, reasoning.get("evidence_refs"))
    return block


def null_reasoning(*, include_status: bool) -> dict[str, Any]:
    """The null-valued ``reasoning`` block for an encounter an agent did not run/produce."""
    block: dict[str, Any] = {}
    if include_status:
        block["status"] = None
    block["summary"] = None
    block["missing"] = None
    block["evidence"] = []
    return block


class ReasoningOnlyBuilder:
    """Base for ``poc_485: null`` topics carried entirely by one per-encounter agent.

    Emits, per encounter, ``{encounter_index, status, confidence, reasoning}`` where
    ``reasoning`` is ``{summary, missing, evidence}`` (envelope ``status`` already
    carries verdict, so ``reasoning.status`` is omitted). Encounters the agent did
    not run (e.g. conditional telehealth / surgical, or a failure) get null values.
    Subclasses set ``key`` and ``agent_name``.
    """

    key: str
    agent_name: str

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "poc_485": None,
            "f2f_encounters": build_f2f_encounters(
                outputs,
                self.agent_name,
                lambda index, output: {
                    "encounter_index": index,
                    "status": output.get("status"),
                    "confidence": output.get("confidence"),
                    "reasoning": reasoning_block(output, resolver, include_status=False),
                },
                lambda index: {
                    "encounter_index": index,
                    "status": None,
                    "confidence": None,
                    "reasoning": null_reasoning(include_status=False),
                },
            ),
        }
