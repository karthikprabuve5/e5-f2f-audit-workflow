"""Unit tests for AnchorSet (POC output → prompt placeholders)."""

from __future__ import annotations

import json

from f2f_orchestration.core.anchors import (
    PLACEHOLDER_CLIENT_NAME,
    PLACEHOLDER_POC_DESCRIPTION,
    PLACEHOLDER_POC_ICD10_CODE,
    PLACEHOLDER_POC_SKILLED_SERVICES,
    AnchorSet,
)

_EXTRACTION = {
    "result": {
        "primary_diagnosis": {"icd10_code": "I50.9", "description": "Heart failure"},
        "skilled_services": {"ordered_services": ["skilled nursing", "physical therapy"]},
    }
}


def test_reads_values_from_full_extraction_object() -> None:
    # Act
    anchors = AnchorSet.from_poc_extraction(_EXTRACTION, client_name="CLIENT_A")

    # Assert
    assert anchors.client_name == "CLIENT_A"
    assert anchors.primary_diagnosis_code == "I50.9"
    assert anchors.primary_diagnosis_description == "Heart failure"
    assert anchors.skilled_services == ["skilled nursing", "physical therapy"]


def test_accepts_inner_result_mapping_directly() -> None:
    # Act
    anchors = AnchorSet.from_poc_extraction(_EXTRACTION["result"], client_name="CLIENT_A")

    # Assert
    assert anchors.primary_diagnosis_code == "I50.9"


def test_placeholders_pass_strings_through_and_json_encode_complex_values() -> None:
    # Arrange
    anchors = AnchorSet.from_poc_extraction(_EXTRACTION, client_name="CLIENT_A")

    # Act
    placeholders = anchors.placeholders()

    # Assert
    assert placeholders[PLACEHOLDER_CLIENT_NAME] == "CLIENT_A"
    assert placeholders[PLACEHOLDER_POC_ICD10_CODE] == "I50.9"
    assert placeholders[PLACEHOLDER_POC_DESCRIPTION] == "Heart failure"
    assert placeholders[PLACEHOLDER_POC_SKILLED_SERVICES] == json.dumps(
        ["skilled nursing", "physical therapy"], ensure_ascii=False
    )


def test_missing_values_render_as_empty_string() -> None:
    # Arrange — extraction with no diagnosis/services
    anchors = AnchorSet.from_poc_extraction({"result": {}}, client_name="CLIENT_A")

    # Act
    placeholders = anchors.placeholders()

    # Assert
    assert placeholders[PLACEHOLDER_POC_ICD10_CODE] == ""
    assert placeholders[PLACEHOLDER_POC_SKILLED_SERVICES] == ""
