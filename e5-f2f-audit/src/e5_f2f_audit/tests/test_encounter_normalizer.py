"""Tests for deterministic shared-page line-boundary repair before splitting."""

from __future__ import annotations

from e5_f2f_audit.core.encounter_normalizer import EncounterNormalizer

# Page 1 spans lines 1..5, Page 2 spans lines 6..7.
_DOCUMENT = "\n".join(
    [
        "### Page 1",  # line 1
        "A1",  # line 2
        "A2",  # line 3
        "B1",  # line 4
        "B2",  # line 5
        "### Page 2",  # line 6
        "C1",  # line 7
    ]
)


def _encounter(index: int, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "encounter_index": index,
        "page_start": 1,
        "page_end": 1,
        "line_start": None,
        "line_end": None,
    }
    base.update(overrides)
    return base


def test_exclusive_page_encounters_are_untouched() -> None:
    encounters = [
        _encounter(1, page_start=1, page_end=1),
        _encounter(2, page_start=2, page_end=2),
    ]

    repaired = EncounterNormalizer().normalize(_DOCUMENT, encounters)

    # No shared page, so line fields stay null (whole-page extraction is correct).
    assert repaired[0]["line_start"] is None and repaired[0]["line_end"] is None
    assert repaired[1]["line_start"] is None and repaired[1]["line_end"] is None


def test_shared_page_fills_missing_ends_from_neighbors_and_span() -> None:
    encounters = [
        _encounter(1, line_start=2, line_end=None),
        _encounter(2, line_start=4, line_end=None),
    ]

    repaired = EncounterNormalizer().normalize(_DOCUMENT, encounters)

    # First end = next start - 1; last end = page span end (line 5).
    assert (repaired[0]["line_start"], repaired[0]["line_end"]) == (2, 3)
    assert (repaired[1]["line_start"], repaired[1]["line_end"]) == (4, 5)


def test_shared_page_fills_missing_first_start_from_page_header() -> None:
    encounters = [
        _encounter(1, line_start=None, line_end=None),
        _encounter(2, line_start=4, line_end=None),
    ]

    repaired = EncounterNormalizer().normalize(_DOCUMENT, encounters)

    # First start defaults to the page header line (1); its end = next start - 1.
    assert (repaired[0]["line_start"], repaired[0]["line_end"]) == (1, 3)
    assert (repaired[1]["line_start"], repaired[1]["line_end"]) == (4, 5)


def test_unrepairable_shared_page_falls_back_untouched() -> None:
    # Two co-page encounters with no interior boundary information at all: cannot
    # be split, so both are left as-is (null) for whole-page fallback.
    encounters = [
        _encounter(1, line_start=None, line_end=None),
        _encounter(2, line_start=None, line_end=None),
    ]

    repaired = EncounterNormalizer().normalize(_DOCUMENT, encounters)

    assert repaired[0]["line_start"] is None and repaired[0]["line_end"] is None
    assert repaired[1]["line_start"] is None and repaired[1]["line_end"] is None


def test_multi_page_encounter_sharing_a_page_falls_back_untouched() -> None:
    encounters = [
        _encounter(1, page_start=1, page_end=2, line_start=None, line_end=None),
        _encounter(2, page_start=2, page_end=2, line_start=None, line_end=None),
    ]

    repaired = EncounterNormalizer().normalize(_DOCUMENT, encounters)

    assert repaired[0]["line_start"] is None and repaired[0]["line_end"] is None
    assert repaired[1]["line_start"] is None and repaired[1]["line_end"] is None


def test_overlapping_provided_ranges_fall_back_untouched() -> None:
    # Provided ranges overlap; rather than "fix" them, leave them exactly as-is.
    encounters = [
        _encounter(1, line_start=2, line_end=4),
        _encounter(2, line_start=3, line_end=5),
    ]

    repaired = EncounterNormalizer().normalize(_DOCUMENT, encounters)

    assert (repaired[0]["line_start"], repaired[0]["line_end"]) == (2, 4)
    assert (repaired[1]["line_start"], repaired[1]["line_end"]) == (3, 5)


def test_reeves_style_multi_page_junction_uses_neighbor_line_start() -> None:
    # E_A spans pages 1-2, E_B spans pages 2-3, meeting on page 2. E_B carries a
    # known line_start (as reeves' E3 did), so E_A's end is derived from it.
    document = "\n".join(
        [
            "### Page 1",  # 1
            "A1",  # 2
            "A2",  # 3
            "### Page 2",  # 4
            "A3",  # 5  (still encounter A)
            "B1",  # 6  (encounter B begins)
            "B2",  # 7
            "### Page 3",  # 8
            "B3",  # 9
        ]
    )
    encounters = [
        _encounter(1, page_start=1, page_end=2, line_start=None, line_end=None),
        _encounter(2, page_start=2, page_end=3, line_start=6, line_end=9),
    ]

    repaired = EncounterNormalizer().normalize(document, encounters)

    # A = page-1 header through the line before B; B unchanged.
    assert (repaired[0]["line_start"], repaired[0]["line_end"]) == (1, 5)
    assert (repaired[1]["line_start"], repaired[1]["line_end"]) == (6, 9)


def test_multi_page_junction_derives_right_start_from_left_end() -> None:
    # Mirror image: the left (multi-page) encounter carries line info, the right
    # does not, so the right's start is derived from the left's end.
    document = "\n".join(
        [
            "### Page 1",  # 1
            "A1",  # 2
            "### Page 2",  # 3
            "A2",  # 4
            "B1",  # 5
            "### Page 3",  # 6
            "B2",  # 7
        ]
    )
    encounters = [
        _encounter(1, page_start=1, page_end=2, line_start=1, line_end=4),
        _encounter(2, page_start=2, page_end=3, line_start=None, line_end=None),
    ]

    repaired = EncounterNormalizer().normalize(document, encounters)

    assert (repaired[0]["line_start"], repaired[0]["line_end"]) == (1, 4)
    assert (repaired[1]["line_start"], repaired[1]["line_end"]) == (5, 7)


def test_unrepairable_page_does_not_discard_repairs_on_other_pages() -> None:
    # Page 1 is repairable; page 2 is not. Page 1 must still be aligned.
    document = "\n".join(
        [
            "### Page 1",  # line 1
            "A1",  # line 2
            "A2",  # line 3
            "B1",  # line 4
            "### Page 2",  # line 5
            "C1",  # line 6
            "D1",  # line 7
        ]
    )
    encounters = [
        _encounter(1, page_start=1, page_end=1, line_start=2, line_end=None),
        _encounter(2, page_start=1, page_end=1, line_start=4, line_end=None),
        # Page 2: two co-page encounters with no boundary info -> un-repairable.
        _encounter(3, page_start=2, page_end=2, line_start=None, line_end=None),
        _encounter(4, page_start=2, page_end=2, line_start=None, line_end=None),
    ]

    repaired = EncounterNormalizer().normalize(document, encounters)

    # Page 1 aligned...
    assert (repaired[0]["line_start"], repaired[0]["line_end"]) == (2, 3)
    assert (repaired[1]["line_start"], repaired[1]["line_end"]) == (4, 4)
    # ...page 2 left untouched for whole-page fallback.
    assert repaired[2]["line_start"] is None and repaired[2]["line_end"] is None
    assert repaired[3]["line_start"] is None and repaired[3]["line_end"] is None
