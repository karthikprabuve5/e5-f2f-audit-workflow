"""``primary_hh_reason`` audit key.

Sources:
- POC 485 ``result.primary_diagnosis`` — full object + evidence (``primary_diagnosis``
  anchor).
- Primary-diagnosis (per encounter) — ``confidence``, ``is_documented``,
  ``f2f_primary_diagnosis`` (with evidence), ``alignment``, ``pathways_met``, the
  ``clinical`` object (findings ``summary`` + union ``evidence`` + per-pathway
  ``pathways[]``, each with its own evidence), and ``reasoning``.
"""

from __future__ import annotations

from typing import Any

from ...core.detection import AgentName
from ..evidence_resolver import EvidenceResolver
from ..transaction_outputs import TransactionOutputs
from .base import build_f2f_encounters, dget, null_reasoning, reasoning_block

_ANCHOR = "primary_diagnosis"

_POC_DIAGNOSIS_FIELDS: tuple[str, ...] = (
    "icd10_code",
    "description",
    "onset_or_exacerbation",
    "oe_date",
    "page",
    "not_found",
)


class PrimaryHhReasonBuilder:
    """Builds the ``primary_hh_reason`` topic."""

    key = "primary_hh_reason"

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "poc_485": {
                "primary_diagnosis": self._poc_primary_diagnosis(outputs.poc_extraction, resolver)
            },
            "f2f_encounters": build_f2f_encounters(
                outputs,
                AgentName.PRIMARY_DIAGNOSIS,
                lambda index, output: self._encounter(index, output, resolver),
                self._absent_encounter,
            ),
        }

    @staticmethod
    def _poc_primary_diagnosis(
        poc: dict[str, Any] | None, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        diagnosis = dget(poc, "result", "primary_diagnosis", default={}) or {}
        projected = {field: diagnosis.get(field) for field in _POC_DIAGNOSIS_FIELDS}
        projected["evidence"] = resolver.resolve_poc_anchor(poc, _ANCHOR)
        return projected

    @classmethod
    def _encounter(
        cls, index: int, output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "encounter_index": index,
            "confidence": output.get("confidence"),
            "is_documented": dget(output, "result", "is_documented"),
            "f2f_primary_diagnosis": cls._f2f_primary_diagnosis(output, resolver),
            "alignment": dget(output, "result", "alignment"),
            "pathways_met": dget(output, "result", "pathways_met", default=[]),
            "clinical": cls._clinical(output, resolver),
            "reasoning": reasoning_block(output, resolver, include_status=True),
        }

    @staticmethod
    def _f2f_primary_diagnosis(
        output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any] | None:
        diagnosis = dget(output, "result", "f2f_primary_diagnosis")
        if not isinstance(diagnosis, dict):
            return None
        return {
            "verbatim": diagnosis.get("verbatim"),
            "icd10_code": diagnosis.get("icd10_code"),
            "specificity": diagnosis.get("specificity"),
            "evidence": resolver.resolve_agent_refs(output, diagnosis.get("evidence_refs")),
        }

    @staticmethod
    def _clinical(
        output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any] | None:
        clinical = dget(output, "rules_applied", "clinical")
        if not isinstance(clinical, dict):
            return None
        return {
            "summary": clinical.get("summary"),
            "evidence": resolver.resolve_agent_refs(output, clinical.get("evidence_refs")),
            "pathways": [
                {
                    "pathway": pathway.get("pathway"),
                    "outcome": pathway.get("outcome"),
                    "detail": pathway.get("detail"),
                    "negative_finding": pathway.get("negative_finding"),
                    "evidence": resolver.resolve_agent_refs(output, pathway.get("evidence_refs")),
                }
                for pathway in (clinical.get("pathways") or [])
            ],
        }

    @staticmethod
    def _absent_encounter(index: int) -> dict[str, Any]:
        return {
            "encounter_index": index,
            "confidence": None,
            "is_documented": None,
            "f2f_primary_diagnosis": None,
            "alignment": None,
            "pathways_met": [],
            "clinical": None,
            "reasoning": null_reasoning(include_status=True),
        }
