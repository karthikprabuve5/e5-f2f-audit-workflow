"""Unit tests for EncounterSplitter (pure, deterministic)."""

from __future__ import annotations

from e5_f2f_audit.core.encounter_splitter import EncounterSplitter

_DOCUMENT = "\n".join(
    [
        "### Page 1",
        "Alpha line",
        "More alpha",
        "### Page 2",
        "Beta line",
        "### Page 3",
        "Gamma",
    ]
)


def test_extracts_whole_single_page_with_header() -> None:
    # Arrange
    splitter = EncounterSplitter()
    encounters = [{"page_start": 1, "page_end": 1, "line_start": None, "line_end": None}]

    # Act
    chunks = splitter.split(_DOCUMENT, encounters)

    # Assert
    assert chunks == ["### Page 1\nAlpha line\nMore alpha"]


def test_extracts_multi_page_range_up_to_document_end() -> None:
    # Arrange
    splitter = EncounterSplitter()
    encounters = [{"page_start": 2, "page_end": 3, "line_start": None, "line_end": None}]

    # Act
    chunks = splitter.split(_DOCUMENT, encounters)

    # Assert
    assert chunks == ["### Page 2\nBeta line\n### Page 3\nGamma"]


def test_same_page_line_range_prepends_missing_page_header() -> None:
    # Arrange
    splitter = EncounterSplitter()
    encounters = [{"page_start": 1, "page_end": 1, "line_start": 2, "line_end": 3}]

    # Act
    chunks = splitter.split(_DOCUMENT, encounters)

    # Assert — the page header is added back so the chunk is self-contained
    assert chunks == ["### Page 1\nAlpha line\nMore alpha"]


def test_missing_page_header_yields_empty_chunk_not_crash() -> None:
    # Arrange — page 9 has no "### Page 9" marker in the document
    splitter = EncounterSplitter()
    encounters = [{"page_start": 9, "page_end": 9, "line_start": None, "line_end": None}]

    # Act
    chunks = splitter.split(_DOCUMENT, encounters)

    # Assert — degrades to an empty chunk (a warning is logged, not silent)
    assert chunks == [""]


def test_accepts_classification_mapping_and_preserves_order() -> None:
    # Arrange
    splitter = EncounterSplitter()
    classification = {
        "encounters": [
            {"page_start": 2, "page_end": 2, "line_start": None, "line_end": None},
            {"page_start": 1, "page_end": 1, "line_start": None, "line_end": None},
        ]
    }

    # Act
    chunks = splitter.split(_DOCUMENT, classification)

    # Assert — output is aligned with the encounters order given
    assert chunks[0].startswith("### Page 2")
    assert chunks[1].startswith("### Page 1")
