"""``timely_encounter`` audit key.

Sources:
- POC 485 ``result.f2f_encounter_date`` — the ``i_certify`` and ``undersigned``
  statements, each with its own ``encounter_date`` value, verbiage, and evidence
  (from the ``f2f_encounter_date`` anchor, narrowed to the statement by line).
- Encounter-identity (per encounter) — ``result.encounter_date`` value plus its
  resolved evidence.
"""

from __future__ import annotations

from typing import Any

from ...core.detection import AgentName
from ..evidence_resolver import EvidenceResolver
from ..transaction_outputs import TransactionOutputs
from .base import build_f2f_encounters, dget

_ANCHOR = "f2f_encounter_date"


class TimelyEncounterBuilder:
    """Builds the ``timely_encounter`` topic."""

    key = "timely_encounter"

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        poc = outputs.poc_extraction
        return {
            "poc_485": {
                "i_certify": self._poc_statement(poc, resolver, "i_certify"),
                "undersigned": self._poc_statement(poc, resolver, "undersigned"),
            },
            "f2f_encounters": build_f2f_encounters(
                outputs,
                AgentName.ENCOUNTER_IDENTITY,
                lambda index, output: self._encounter(index, output, resolver),
                self._absent_encounter,
            ),
        }

    @staticmethod
    def _poc_statement(
        poc: dict[str, Any] | None, resolver: EvidenceResolver, statement: str
    ) -> dict[str, Any]:
        """Project one f2f_encounter_date statement (i_certify / undersigned)."""
        node = dget(poc, "result", "f2f_encounter_date", statement, default={}) or {}
        line_start = node.get("line_start")
        anchor_evidence = resolver.resolve_poc_anchor(poc, _ANCHOR)
        # The anchor may cover both statements; keep only evidence on this
        # statement's line. A statement with no line (e.g. not_found) gets none.
        evidence = (
            [item for item in anchor_evidence if item.get("line_start") == line_start]
            if line_start is not None
            else []
        )
        return {
            "encounter_date": node.get("value"),
            "verbiage": node.get("verbiage"),
            "evidence": evidence,
        }

    @staticmethod
    def _encounter(
        index: int, output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any]:
        encounter_date = dget(output, "result", "encounter_date", default={}) or {}
        return {
            "encounter_index": index,
            "encounter_date": encounter_date.get("value"),
            "evidence": resolver.resolve_agent_refs(
                output, encounter_date.get("evidence_refs")
            ),
        }

    @staticmethod
    def _absent_encounter(index: int) -> dict[str, Any]:
        return {"encounter_index": index, "encounter_date": None, "evidence": []}
