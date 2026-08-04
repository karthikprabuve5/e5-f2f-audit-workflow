"""Unit tests for the post-processing SchemaValidator and its per-agent registry.

Two kinds of tests:

* **Behavioral** — normalization, repair, and critical-failure detection for the
  envelope, POC, and classification shapes.
* **Drift guard** — parses each agent's ``references/output-schema.md`` and asserts
  the machine-readable registry stays in sync with the documented contract, so the
  two cannot silently diverge.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from f2f_orchestration.core.detection import AgentName
from f2f_orchestration.core.output_validator import (
    AGENT_SCHEMA_SPECS,
    SHAPE_ENVELOPE,
    SchemaValidator,
)

_SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"


def _schema_doc(agent: AgentName) -> Path:
    return _SKILLS_ROOT / str(agent) / str(agent) / "references" / "output-schema.md"


def _first_json_block(text: str) -> dict:
    match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    assert match, "output-schema.md must contain a ```json example block"
    return json.loads(match.group(1))


# --- Behavioral ----------------------------------------------------------------


def test_envelope_fills_missing_keys_and_flags_them() -> None:
    validator = SchemaValidator()
    raw = {"status": "COMPLETE", "result": {"encounter_date": "2026-01-01"}, "evidence": []}

    processed, result = validator.validate(AgentName.ENCOUNTER_IDENTITY, raw)

    # Missing envelope + result keys are filled and recorded
    assert "schema_version" in processed
    assert processed["result"]["signature"] is None
    assert "result.signature" in result.missing_keys
    assert "encounter_index" in processed  # F2F agents carry an index
    assert processed["validation"] == result.as_dict()


def test_envelope_missing_status_is_critical() -> None:
    validator = SchemaValidator()
    raw = {"result": {}, "evidence": []}

    _, result = validator.validate(AgentName.HOMEBOUND, raw)

    assert result.critical is True
    assert result.schema_valid is False


def test_dangling_evidence_ref_is_critical() -> None:
    validator = SchemaValidator()
    raw = {
        "status": "COMPLETE",
        "result": {"prong_1": {"evidence_refs": ["E999"]}},
        "evidence": [{"evidence_id": "E001"}],
        "reasoning": {"evidence_refs": []},
    }

    _, result = validator.validate(AgentName.HOMEBOUND, raw)

    assert result.dangling_refs == ["E999"]
    assert result.critical is True


def test_resolvable_evidence_ref_is_not_dangling() -> None:
    validator = SchemaValidator()
    raw = {
        "status": "COMPLETE",
        "result": {"prong_1": {"evidence_refs": ["E001"]}},
        "evidence": [{"evidence_id": "E001", "field": "prong_1", "verbiage": "x",
                      "page": 1, "line_start": 1, "line_end": 1}],
        "reasoning": {"evidence_refs": ["E001"]},
    }

    _, result = validator.validate(AgentName.HOMEBOUND, raw)

    assert result.dangling_refs == []


def test_top_level_agency_warnings_is_moved_under_reasoning() -> None:
    validator = SchemaValidator()
    raw = {
        "status": "COMPLETE",
        "result": {},
        "evidence": [],
        "reasoning": {"summary": "s"},
        "agency_warnings": ["EXTEND failed"],
    }

    processed, result = validator.validate(AgentName.HOMEBOUND, raw)

    assert "agency_warnings" not in processed
    assert processed["reasoning"]["agency_warnings"] == ["EXTEND failed"]
    assert "reasoning.agency_warnings" in result.repaired_keys


def test_poc_uses_sources_linkage_for_ref_integrity() -> None:
    validator = SchemaValidator()
    raw = {
        "status": "EXTRACTED",
        "result": {},
        "evidence": [{"evidence_id": "E001", "anchor": "primary_diagnosis"}],
        "reasoning": {"sources": [{"evidence_id": "E001"}]},
    }

    _, result = validator.validate(AgentName.POC_485_EXTRACTION, raw)

    assert result.dangling_refs == []


def test_encounter_index_is_filled_but_not_flagged() -> None:
    """Pipeline-owned ``encounter_index`` is normalized silently, never flagged.

    The per-encounter agents see a single-encounter chunk and cannot know their
    position; the pipeline injects the authoritative index. So a missing index must
    not appear as a schema issue (it previously leaked into ``data_quality``).
    """
    validator = SchemaValidator()
    raw = {
        "schema_version": "1.0",
        "parameter_id": "encounter_identity",
        "client_id": "DEFAULT",
        "evaluated_at": "2026-01-15T00:00:00Z",
        "status": "MET",
        "confidence": 0.9,
        "result": {"encounter_date": None, "signature": None, "eligible_provider": None},
        "evidence": [],
        "rules_applied": {"cms": [], "client": []},
        "reasoning": {"status": "MET", "summary": "s", "evidence_refs": [], "missing": None},
    }

    processed, result = validator.validate(AgentName.ENCOUNTER_IDENTITY, raw)

    assert processed["encounter_index"] == 0  # placeholder filled for ordering/shape
    assert "encounter_index" not in result.missing_keys
    assert "encounter_index" not in result.repaired_keys
    assert result.schema_valid is True


def test_poc_does_not_require_encounter_index() -> None:
    validator = SchemaValidator()
    processed, _ = validator.validate(
        AgentName.POC_485_EXTRACTION,
        {"status": "EXTRACTED", "result": {}, "evidence": []},
    )
    assert "encounter_index" not in processed


def test_classification_derives_total_and_fills_encounter_keys() -> None:
    validator = SchemaValidator()
    processed, result = validator.validate(
        AgentName.CLASSIFICATION, {"encounters": [{"encounter_index": 1}]}
    )

    assert processed["total_encounters"] == 1
    assert processed["encounters"][0]["encounter_category"] == ""
    assert "encounters[0].encounter_category" in result.missing_keys


def test_classification_missing_encounters_is_critical() -> None:
    validator = SchemaValidator()
    _, result = validator.validate(AgentName.CLASSIFICATION, {})
    assert result.critical is True


def test_raw_input_is_never_mutated() -> None:
    validator = SchemaValidator()
    raw = {"status": "COMPLETE", "result": {}, "evidence": []}
    snapshot = json.dumps(raw, sort_keys=True)

    validator.validate(AgentName.HOMEBOUND, raw)

    assert json.dumps(raw, sort_keys=True) == snapshot


# --- Drift guard ---------------------------------------------------------------


@pytest.mark.parametrize("agent", list(AGENT_SCHEMA_SPECS))
def test_registry_result_keys_match_schema_doc(agent: AgentName) -> None:
    """The registry's result keys must equal the documented example's result keys."""
    spec = AGENT_SCHEMA_SPECS[agent]
    if spec.shape != SHAPE_ENVELOPE:
        pytest.skip("classification has no `result` block")

    example = _first_json_block(_schema_doc(agent).read_text(encoding="utf-8"))
    assert set(example["result"].keys()) == set(spec.result_keys)


def test_classification_registry_keys_are_documented() -> None:
    """Every classification encounter key in the registry must appear in the doc."""
    spec = AGENT_SCHEMA_SPECS[AgentName.CLASSIFICATION]
    example = _first_json_block(_schema_doc(AgentName.CLASSIFICATION).read_text(encoding="utf-8"))
    documented = set(example["encounters"][0].keys())
    assert set(spec.encounter_item_keys) <= documented
