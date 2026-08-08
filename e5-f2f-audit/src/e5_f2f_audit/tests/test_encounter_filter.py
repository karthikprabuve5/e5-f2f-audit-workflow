"""Unit tests for the deterministic pre-selection encounter filter.

The filter must remove only ``referral_documents`` encounters from the selection
candidate set, leave every other encounter and the ``poc_485`` blocks untouched,
never mutate its inputs, and report exactly which indices were excluded.
"""

from __future__ import annotations

import copy

import pytest

from e5_f2f_audit.core.encounter_filter import (
    EXCLUDED_SELECTION_CATEGORIES,
    EXCLUSION_REASON,
    REFERRAL_CATEGORY,
    filter_candidates,
)


def _merge_encounters() -> dict:
    """Two topics, each carrying three encounters (indices 1, 2, 3) plus a poc block."""
    return {
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
        }
    }


def _roster() -> dict:
    """Index 3 is a referral document; 1 and 2 are real encounters."""
    return {
        "total_encounters": 3,
        "encounters": [
            {"encounter_index": 1, "encounter_category": "f2f_encounter", "encounter_subcategory": "1.1"},
            {"encounter_index": 2, "encounter_category": "clinical_encounter_notes", "encounter_subcategory": "6.3"},
            {"encounter_index": 3, "encounter_category": REFERRAL_CATEGORY, "encounter_subcategory": "15.2"},
        ],
    }


def test_only_referral_category_is_excluded() -> None:
    assert EXCLUDED_SELECTION_CATEGORIES == frozenset({"referral_documents"})


def test_referral_encounter_dropped_from_every_topic() -> None:
    filtered, excluded = filter_candidates(_merge_encounters(), _roster())

    for topic in filtered["results"].values():
        indices = [enc["encounter_index"] for enc in topic["f2f_encounters"]]
        assert indices == [1, 2]

    assert [entry["encounter_index"] for entry in excluded] == [3]
    assert excluded[0] == {
        "encounter_index": 3,
        "encounter_category": REFERRAL_CATEGORY,
        "encounter_subcategory": "15.2",
        "reason": EXCLUSION_REASON,
    }


def test_poc_485_block_is_untouched() -> None:
    filtered, _ = filter_candidates(_merge_encounters(), _roster())
    assert filtered["results"]["timely_encounter"]["poc_485"] == {
        "i_certify": {"encounter_date": "2026-07-21"}
    }


def test_inputs_are_not_mutated() -> None:
    merged = _merge_encounters()
    roster = _roster()
    merged_snapshot = copy.deepcopy(merged)
    roster_snapshot = copy.deepcopy(roster)

    filter_candidates(merged, roster)

    assert merged == merged_snapshot
    assert roster == roster_snapshot


def test_no_referral_is_a_noop() -> None:
    roster = {
        "encounters": [
            {"encounter_index": 1, "encounter_category": "f2f_encounter"},
            {"encounter_index": 2, "encounter_category": "clinical_encounter_notes"},
        ]
    }
    filtered, excluded = filter_candidates(_merge_encounters(), roster)

    assert excluded == []
    for topic in filtered["results"].values():
        assert [enc["encounter_index"] for enc in topic["f2f_encounters"]] == [1, 2, 3]


def test_bare_list_roster_is_accepted() -> None:
    roster = _roster()["encounters"]
    _, excluded = filter_candidates(_merge_encounters(), roster)
    assert [entry["encounter_index"] for entry in excluded] == [3]


def test_string_encounter_index_is_coerced() -> None:
    roster = {"encounters": [{"encounter_index": "3", "encounter_category": REFERRAL_CATEGORY}]}
    filtered, excluded = filter_candidates(_merge_encounters(), roster)

    assert [entry["encounter_index"] for entry in excluded] == [3]
    for topic in filtered["results"].values():
        assert 3 not in [enc["encounter_index"] for enc in topic["f2f_encounters"]]


def test_invalid_roster_shape_raises() -> None:
    with pytest.raises(ValueError, match="classification_roster must be"):
        filter_candidates(_merge_encounters(), {"encounters": 123})
