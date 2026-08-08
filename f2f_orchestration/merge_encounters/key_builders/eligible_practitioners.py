"""``eligible_practitioners`` merge key.

Sources:
- POC 485 ``result.certification.occurrences`` — primary occurrences only, each
  with its signature metadata and evidence (from the ``certification`` anchor,
  narrowed to the occurrence's page).
- Encounter-identity (per encounter) — ``confidence``, the ``signature`` block
  filtered to conducting-provider signers, the full ``eligible_provider`` object
  (references replaced with inline evidence), and the ``reasoning`` block.
"""

from __future__ import annotations

from typing import Any

from ...core.detection import AgentName
from ..evidence_resolver import EvidenceResolver
from ..transaction_outputs import TransactionOutputs
from .base import build_f2f_encounters, dget, null_reasoning, reasoning_block

_ANCHOR = "certification"

# Signature-occurrence fields carried through, in contract order.
_OCCURRENCE_FIELDS: tuple[str, ...] = (
    "page",
    "is_primary",
    "signature_type",
    "name_raw",
    "name_format",
    "display_name",
    "date_signed",
    "is_signed",
    "is_dated",
)


class EligiblePractitionersBuilder:
    """Builds the ``eligible_practitioners`` topic."""

    key = "eligible_practitioners"

    def build(
        self, outputs: TransactionOutputs, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        return {
            "poc_485": {"certification": self._poc_certification(outputs.poc_extraction, resolver)},
            "f2f_encounters": build_f2f_encounters(
                outputs,
                AgentName.ENCOUNTER_IDENTITY,
                lambda index, output: self._encounter(index, output, resolver),
                self._absent_encounter,
            ),
        }

    @staticmethod
    def _poc_certification(
        poc: dict[str, Any] | None, resolver: EvidenceResolver
    ) -> dict[str, Any]:
        occurrences = dget(poc, "result", "certification", "occurrences", default=[]) or []
        anchor_evidence = resolver.resolve_poc_anchor(poc, _ANCHOR)
        primary: list[dict[str, Any]] = []
        for occurrence in occurrences:
            if not occurrence.get("is_primary"):
                continue
            page = occurrence.get("page")
            projected = {field: occurrence.get(field) for field in _OCCURRENCE_FIELDS}
            projected["evidence"] = (
                [item for item in anchor_evidence if item.get("page") == page]
                if page is not None
                else list(anchor_evidence)
            )
            primary.append(projected)
        return {"occurrences": primary}

    @staticmethod
    def _encounter(
        index: int, output: dict[str, Any], resolver: EvidenceResolver
    ) -> dict[str, Any]:
        signature = dget(output, "result", "signature", default={}) or {}
        conducting_signers = [
            resolver.inline_nested(signer, output)
            for signer in (signature.get("signers") or [])
            if signer.get("is_conducting_provider")
        ]
        eligible_provider = dget(output, "result", "eligible_provider", default=None)
        return {
            "encounter_index": index,
            "confidence": output.get("confidence"),
            "signature": {
                "signed": signature.get("signed"),
                "signers": conducting_signers,
            },
            "eligible_provider": (
                resolver.inline_nested(eligible_provider, output)
                if eligible_provider is not None
                else None
            ),
            "reasoning": reasoning_block(output, resolver, include_status=False),
        }

    @staticmethod
    def _absent_encounter(index: int) -> dict[str, Any]:
        return {
            "encounter_index": index,
            "confidence": None,
            "signature": {"signed": None, "signers": []},
            "eligible_provider": None,
            "reasoning": null_reasoning(include_status=False),
        }
