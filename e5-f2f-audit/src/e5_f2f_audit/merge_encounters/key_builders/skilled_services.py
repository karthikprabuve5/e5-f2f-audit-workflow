"""``skilled_services`` merge key.

Sources:
- POC 485 ``result.skilled_services`` — ordered services + evidence
  (``skilled_services`` anchor).
- Skilled-services (per encounter) — ``status``, ``confidence``, ``is_documented``,
  the ``services`` list (references replaced with inline evidence), and ``reasoning``
  (including ``reasoning.status``, kept consistent with the other clinical pillars).
"""

from __future__ import annotations

from typing import Any

from ...core.detection import AgentName
from ..evidence_resolver import EvidenceResolver
from ..transaction_outputs import TransactionOutputs
from .base import build_f2f_encounters, dget, null_reasoning, reasoning_block

_ANCHOR = "skilled_services"


class SkilledServicesBuilder:
    """Builds the ``skilled_services`` topic."""

    key = "skilled_services"

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "poc_485": {
                "skilled_services": self._poc_skilled_services(outputs.poc_extraction, resolver)
            },
            "f2f_encounters": build_f2f_encounters(
                outputs,
                AgentName.SKILLED_SERVICES,
                lambda index, output: self._encounter(index, output, resolver),
                self._absent_encounter,
            ),
        }

    @staticmethod
    def _poc_skilled_services(
        poc: dict[str, Any] | None, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        skilled = dget(poc, "result", "skilled_services", default={}) or {}
        return {
            "ordered_services": skilled.get("ordered_services", []),
            "page": skilled.get("page"),
            "not_found": skilled.get("not_found"),
            "evidence": resolver.resolve_poc_anchor(poc, _ANCHOR),
        }

    @staticmethod
    def _encounter(
        index: int, output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any]:
        services = [
            resolver.inline_nested(service, output)
            for service in (dget(output, "result", "services", default=[]) or [])
        ]
        return {
            "encounter_index": index,
            "status": output.get("status"),
            "confidence": output.get("confidence"),
            "is_documented": dget(output, "result", "is_documented"),
            "services": services,
            "reasoning": reasoning_block(output, resolver, include_status=True),
        }

    @staticmethod
    def _absent_encounter(index: int) -> dict[str, Any]:
        return {
            "encounter_index": index,
            "status": None,
            "confidence": None,
            "is_documented": None,
            "services": [],
            "reasoning": null_reasoning(include_status=True),
        }
