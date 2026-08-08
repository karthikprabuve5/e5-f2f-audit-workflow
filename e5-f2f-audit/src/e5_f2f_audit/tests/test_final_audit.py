"""Unit tests for the final-audit engine.

The engine must return the identical merge-encounters format with every encounter
retained (lossless superset), surface the selection headline fields at the top of
``results``, inject ``generated_at``, never mutate its inputs, and fail loudly on
malformed inputs.
"""

from __future__ import annotations

import copy

import pytest

from e5_f2f_audit.audit import FinalAuditEngine

GENERATED_AT = "2026-08-08T00:00:00+00:00"


def _merged() -> dict:
    """A merge-encounters contract with three encounters (indices 1, 2, 3) per topic."""
    return {
        "transaction_id": "transaction_x",
        "client_id": "CLIENT_A",
        "parameter_id": "merge_encounters",
        "generated_at": "2026-08-01T00:00:00+00:00",
        "data_quality": {"failed_agents": [], "schema_issues": []},
        "results": {
            "timely_encounter": {
                "poc_485": {"i_certify": {"encounter_date": "2026-07-21"}},
                "f2f_encounters": [
                    {"encounter_index": 1, "encounter_date": "2026-07-21"},
                    {"encounter_index": 2, "encounter_date": "2026-07-10"},
                    {"encounter_index": 3, "encounter_date": "2026-06-01"},
                ],
            },
            "skilled_services": {
                "poc_485": None,
                "f2f_encounters": [
                    {"encounter_index": 1, "status": "MET"},
                    {"encounter_index": 2, "status": "MET"},
                    {"encounter_index": 3, "status": "NOT_MET"},
                ],
            },
        },
    }


def _selection(best_index: int = 1, excluded_index: int = 3) -> dict:
    return {
        "transaction_id": "transaction_x",
        "result": {
            "best_encounter_index": best_index,
            "best_encounter_score": 87,
            "best_is_date_aligned": True,
            "date_aligned_encounter": {"encounter_index": 1, "encounter_date": "2026-07-21"},
            "excluded_encounter_indices": [excluded_index],
            "excluded_encounters": [
                {"encounter_index": excluded_index, "category": "referral_documents"},
            ],
        },
        "reasoning": {
            "status": "SELECTED",
            "summary": "Encounter 1 is the most defensible: it substantiates the certified diagnosis and homebound status.",
        },
    }


def test_keeps_all_encounters_per_topic() -> None:
    audit = FinalAuditEngine().build(_merged(), _selection(), generated_at=GENERATED_AT)

    for topic in ("timely_encounter", "skilled_services"):
        indices = [
            encounter["encounter_index"]
            for encounter in audit["results"][topic]["f2f_encounters"]
        ]
        assert indices == [1, 2, 3]


def test_results_prefixed_with_selection_headline_fields_in_order() -> None:
    audit = FinalAuditEngine().build(_merged(), _selection(), generated_at=GENERATED_AT)

    keys = list(audit["results"].keys())
    assert keys[:6] == [
        "best_encounter_index",
        "best_encounter_score",
        "best_is_date_aligned",
        "date_aligned_encounter",
        "excluded_encounters",
        "encounter_selection_summary",
    ]
    # Topic blocks follow the headline fields, format unchanged.
    assert keys[6:] == ["timely_encounter", "skilled_services"]
    assert audit["results"]["best_encounter_index"] == 1
    assert audit["results"]["best_encounter_score"] == 87
    assert audit["results"]["best_is_date_aligned"] is True
    assert audit["results"]["excluded_encounters"] == [
        {"encounter_index": 3, "category": "referral_documents"}
    ]
    assert audit["results"]["encounter_selection_summary"].startswith("Encounter 1 is the most")


def test_preserves_format_and_injects_generated_at() -> None:
    audit = FinalAuditEngine().build(_merged(), _selection(), generated_at=GENERATED_AT)

    assert audit["transaction_id"] == "transaction_x"
    assert audit["parameter_id"] == "merge_encounters"
    assert audit["generated_at"] == GENERATED_AT
    # data_quality carried through unchanged.
    assert audit["data_quality"] == {"failed_agents": [], "schema_issues": []}
    # poc_485 blocks left intact.
    assert audit["results"]["timely_encounter"]["poc_485"] == {
        "i_certify": {"encounter_date": "2026-07-21"}
    }


def test_does_not_mutate_inputs() -> None:
    merged = _merged()
    selection = _selection()
    merged_before = copy.deepcopy(merged)
    selection_before = copy.deepcopy(selection)

    FinalAuditEngine().build(merged, selection, generated_at=GENERATED_AT)

    assert merged == merged_before
    assert selection == selection_before


def test_encounter_selection_summary_is_null_when_reasoning_absent() -> None:
    selection = _selection()
    del selection["reasoning"]

    audit = FinalAuditEngine().build(_merged(), selection, generated_at=GENERATED_AT)

    assert audit["results"]["encounter_selection_summary"] is None


def test_transaction_id_mismatch_raises() -> None:
    selection = _selection()
    selection["transaction_id"] = "transaction_other"

    with pytest.raises(ValueError, match="transaction_id mismatch"):
        FinalAuditEngine().build(_merged(), selection, generated_at=GENERATED_AT)


def test_missing_selection_result_raises() -> None:
    with pytest.raises(ValueError, match="selection\\['result'\\]"):
        FinalAuditEngine().build(_merged(), {"transaction_id": "transaction_x"}, generated_at=GENERATED_AT)


def test_non_mapping_input_raises() -> None:
    with pytest.raises(TypeError):
        FinalAuditEngine().build([], _selection(), generated_at=GENERATED_AT)
