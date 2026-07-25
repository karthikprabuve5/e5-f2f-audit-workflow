"""POC anchor values injected into the F2F agent prompts.

``AnchorSet`` carries the anchor values exactly as the POC/485 agent produced
them and maps them to the placeholder tokens used in the F2F prompts (e.g.
``<POC_ICD10_CODE>``). Values are passed through as-is — the only conversion is
serializing non-string values so they can be substituted into prompt text.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

PLACEHOLDER_CLIENT_NAME = "<CLIENT_NAME>"
PLACEHOLDER_POC_ICD10_CODE = "<POC_ICD10_CODE>"
PLACEHOLDER_POC_DESCRIPTION = "<POC_DESCRIPTION>"
PLACEHOLDER_POC_SKILLED_SERVICES = "<POC_SKILLED_SERVICES>"


def _as_text(value: Any) -> str:
    """Text form for prompt substitution: strings unchanged, others as JSON."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


@dataclass(frozen=True)
class AnchorSet:
    """The POC-derived anchor values the F2F prompts consume, kept as-is."""

    client_name: str
    primary_diagnosis_code: Any = None
    primary_diagnosis_description: Any = None
    skilled_services: Any = None

    @classmethod
    def from_poc_extraction(
        cls, poc_extraction: Mapping[str, Any], *, client_name: str
    ) -> "AnchorSet":
        """Read the anchor values straight from the POC/485 output JSON.

        Accepts either the full extraction object (with a ``result`` key) or the
        inner ``result`` mapping directly.
        """
        result = poc_extraction.get("result", poc_extraction)
        primary_diagnosis = result.get("primary_diagnosis") or {}
        skilled_services = result.get("skilled_services") or {}

        return cls(
            client_name=client_name,
            primary_diagnosis_code=primary_diagnosis.get("icd10_code"),
            primary_diagnosis_description=primary_diagnosis.get("description"),
            skilled_services=skilled_services.get("ordered_services"),
        )

    def placeholders(self) -> dict[str, str]:
        """Return the prompt placeholder -> value map for the F2F agents."""
        return {
            PLACEHOLDER_CLIENT_NAME: _as_text(self.client_name),
            PLACEHOLDER_POC_ICD10_CODE: _as_text(self.primary_diagnosis_code),
            PLACEHOLDER_POC_DESCRIPTION: _as_text(self.primary_diagnosis_description),
            PLACEHOLDER_POC_SKILLED_SERVICES: _as_text(self.skilled_services),
        }
