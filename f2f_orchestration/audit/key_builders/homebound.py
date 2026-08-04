"""``homebound`` audit key.

Sources:
- POC 485 ``result.homebound`` — ``full_text`` + evidence (``homebound`` anchor).
- Homebound (per encounter) — ``status``, ``confidence``, ``is_documented``,
  ``prong_1`` / ``prong_2`` objects (each with resolved evidence), and ``reasoning``.
"""

from __future__ import annotations

from typing import Any

from ...core.detection import AgentName
from ..evidence_resolver import EvidenceResolver
from ..transaction_outputs import TransactionOutputs
from .base import build_f2f_encounters, dget, null_reasoning, reasoning_block

_ANCHOR = "homebound"


class HomeboundBuilder:
    """Builds the ``homebound`` topic."""

    key = "homebound"

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "poc_485": {"homebound": self._poc_homebound(outputs.poc_extraction, resolver)},
            "f2f_encounters": build_f2f_encounters(
                outputs,
                AgentName.HOMEBOUND,
                lambda index, output: self._encounter(index, output, resolver),
                self._absent_encounter,
            ),
        }

    @staticmethod
    def _poc_homebound(
        poc: dict[str, Any] | None, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        homebound = dget(poc, "result", "homebound", default={}) or {}
        return {
            "full_text": homebound.get("full_text"),
            "page": homebound.get("page"),
            "not_found": homebound.get("not_found"),
            "evidence": resolver.resolve_poc_anchor(poc, _ANCHOR),
        }

    @classmethod
    def _encounter(
        cls, index: int, output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "encounter_index": index,
            "status": output.get("status"),
            "confidence": output.get("confidence"),
            "is_documented": dget(output, "result", "is_documented"),
            "prong_1": cls._prong_1(output, resolver),
            "prong_2": cls._prong_2(output, resolver),
            "reasoning": reasoning_block(output, resolver, include_status=True),
        }

    @staticmethod
    def _prong_1(
        output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any] | None:
        prong = dget(output, "result", "prong_1")
        if not isinstance(prong, dict):
            return None
        return {
            "met": prong.get("met"),
            "criteria_met": prong.get("criteria_met", []),
            "criteria_evaluated": prong.get("criteria_evaluated", []),
            "evidence": resolver.resolve_agent_refs(output, prong.get("evidence_refs")),
        }

    @staticmethod
    def _prong_2(
        output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any] | None:
        prong = dget(output, "result", "prong_2")
        if not isinstance(prong, dict):
            return None
        return {
            "met": prong.get("met"),
            "normal_inability_met": prong.get("normal_inability_met"),
            "considerable_effort_met": prong.get("considerable_effort_met"),
            "evidence": resolver.resolve_agent_refs(output, prong.get("evidence_refs")),
        }

    @staticmethod
    def _absent_encounter(index: int) -> dict[str, Any]:
        return {
            "encounter_index": index,
            "status": None,
            "confidence": None,
            "is_documented": None,
            "prong_1": None,
            "prong_2": None,
            "reasoning": null_reasoning(include_status=True),
        }
