"""Tests for the POC 485-encounter gate before extraction.

A match requires both category ``poc_485`` and subcategory ``2.1``.
"""

from __future__ import annotations

import pytest

from f2f_orchestration.pipelines.poc_pipeline import POCClassificationError, PocPipeline


def test_selects_the_only_poc_485_encounter() -> None:
    classification = {
        "encounters": [
            {"encounter_index": 1, "encounter_category": "poc_485", "encounter_subcategory": "2.1"}
        ]
    }
    selected = PocPipeline._select_poc_encounter(classification, "txn")
    assert selected["encounter_index"] == 1


def test_selects_first_when_multiple_poc_485_present() -> None:
    classification = {
        "encounters": [
            {"encounter_index": 1, "encounter_category": "other", "encounter_subcategory": "1.0"},
            {"encounter_index": 2, "encounter_category": "poc_485", "encounter_subcategory": "2.1"},
            {"encounter_index": 3, "encounter_category": "poc_485", "encounter_subcategory": "2.1"},
        ]
    }
    selected = PocPipeline._select_poc_encounter(classification, "txn")
    assert selected["encounter_index"] == 2


def test_raises_when_category_matches_but_subcategory_differs() -> None:
    classification = {
        "encounters": [
            {"encounter_index": 1, "encounter_category": "poc_485", "encounter_subcategory": "2.2"}
        ]
    }
    with pytest.raises(POCClassificationError, match="2.1"):
        PocPipeline._select_poc_encounter(classification, "txn")


def test_raises_when_no_poc_485_category() -> None:
    classification = {
        "encounters": [
            {"encounter_index": 1, "encounter_category": "progress_note", "encounter_subcategory": "2.1"}
        ]
    }
    with pytest.raises(POCClassificationError, match="poc_485"):
        PocPipeline._select_poc_encounter(classification, "txn")


def test_raises_when_no_encounters_at_all() -> None:
    with pytest.raises(POCClassificationError):
        PocPipeline._select_poc_encounter({"encounters": []}, "txn")
