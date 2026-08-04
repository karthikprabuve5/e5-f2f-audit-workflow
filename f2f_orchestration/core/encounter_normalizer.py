"""Deterministic repair of classification line boundaries before splitting.

The classification agent is supposed to give an encounter a ``line_start`` /
``line_end`` whenever it meets a neighbor on a shared page, so
:class:`EncounterSplitter` can cut the page at the right boundary. When it omits
those (a real failure mode), the splitter falls back to whole-page extraction and
the two encounters' text bleeds together.

``EncounterNormalizer`` runs between classification and splitting and models the
document as a reading-order sequence of encounters, each owning a contiguous
global line range. The only place a boundary is ever needed is the **junction
between two consecutive encounters that meet on the same page**
(``A.page_end == B.page_start``) — this is true whether each encounter spans one
page or many, so a single rule covers both the same-page and multi-page cases.

For each such junction the split line is taken from whichever side the classifier
did provide (``B.line_start``, else ``A.line_end + 1``). Once an encounter is
involved in any junction it must become an explicit range, so its still-missing
outer edge is filled from the page span (header line of ``page_start`` / last line
of ``page_end``).

The repair is purely additive and never raises to the caller:

* It only fills **missing** boundaries — a classifier-provided value is never
  overwritten.
* A junction it cannot resolve (neither side has line info) or that would produce
  an inconsistent/overlapping range is **left exactly as the classifier produced
  it** (logged as a warning) so the splitter uses its prior whole-page behavior.
* Fallback is isolated per junction: one bad junction does not discard repairs
  made elsewhere.

Encounters that never meet a neighbor on a shared page are untouched: their
``line_start`` / ``line_end`` stay ``null`` and whole-page extraction remains
correct.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .logging_setup import get_logger

logger = get_logger(__name__)


class EncounterNormalizationError(RuntimeError):
    """Signals that a junction's line ranges cannot be safely reconstructed.

    Raised internally by the per-junction repair and caught by
    :meth:`EncounterNormalizer.normalize`, which logs a warning and leaves the two
    encounters as-is (whole-page fallback). It is control flow within the
    normalizer, not an error propagated to the caller.
    """


class EncounterNormalizer:
    """Repairs missing line boundaries at shared-page encounter junctions."""

    _PAGE_HEADER_PATTERN = re.compile(r"^###\s+Page\s+(\d+)\s*$")

    def normalize(
        self, document: str, encounters: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        """Return a copy of ``encounters`` with repairable line boundaries filled.

        Never raises: a junction that cannot be safely reconstructed is left
        exactly as the classifier produced it (logged as a warning) so the splitter
        falls back to whole-page extraction for it.
        """
        repaired = [dict(encounter) for encounter in encounters]
        lines = document.splitlines()
        page_header_line = self._build_page_header_map(lines)
        total_lines = len(lines)

        # Reading order == encounter_index order (top-to-bottom through the document).
        order = sorted(
            range(len(repaired)),
            key=lambda i: repaired[i].get("encounter_index") or (i + 1),
        )

        for position in range(len(order) - 1):
            left = repaired[order[position]]
            right = repaired[order[position + 1]]
            if not self._share_boundary(left, right):
                continue
            self._repair_junction(left, right, page_header_line, total_lines)

        return repaired

    @staticmethod
    def _share_boundary(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        """True when ``left`` ends on the same page ``right`` starts on."""
        left_page_end = left.get("page_end") or left.get("page_start")
        right_page_start = right.get("page_start")
        return (
            left_page_end is not None
            and right_page_start is not None
            and left_page_end == right_page_start
        )

    def _repair_junction(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        page_header_line: dict[int, int],
        total_lines: int,
    ) -> None:
        """Fill the boundary between two consecutive encounters sharing a page.

        Snapshots both encounters first: if the junction cannot be resolved into a
        consistent, in-bounds, non-overlapping pair of ranges, everything is
        restored so the classifier's original output stands (whole-page fallback).
        """
        snapshot = {
            "left_start": left.get("line_start"),
            "left_end": left.get("line_end"),
            "right_start": right.get("line_start"),
            "right_end": right.get("line_end"),
        }
        shared_page = right["page_start"]

        try:
            split_line = self._resolve_split_line(left, right, shared_page)
            if left.get("line_end") is None:
                left["line_end"] = split_line - 1
            if right.get("line_start") is None:
                right["line_start"] = split_line

            self._fill_outer_edge(left, page_header_line, total_lines)
            self._fill_outer_edge(right, page_header_line, total_lines)

            self._verify_pair(left, right, page_header_line, total_lines)
        except EncounterNormalizationError as exc:
            left["line_start"] = snapshot["left_start"]
            left["line_end"] = snapshot["left_end"]
            right["line_start"] = snapshot["right_start"]
            right["line_end"] = snapshot["right_end"]
            logger.warning(
                "Encounter junction un-repairable; leaving encounters for whole-page fallback",
                extra={
                    "shared_page": shared_page,
                    "left_encounter": left.get("encounter_index"),
                    "right_encounter": right.get("encounter_index"),
                    "reason": str(exc),
                },
            )

    @staticmethod
    def _resolve_split_line(
        left: Mapping[str, Any], right: Mapping[str, Any], shared_page: int
    ) -> int:
        """Return the first line that belongs to ``right`` on the shared page.

        Prefer the classifier's ``right.line_start``; else derive it from
        ``left.line_end``. If neither side has line info, the junction is ambiguous.
        """
        right_start = right.get("line_start")
        if right_start is not None:
            return right_start
        left_end = left.get("line_end")
        if left_end is not None:
            return left_end + 1
        raise EncounterNormalizationError(
            f"Page {shared_page}: neither encounter "
            f"{left.get('encounter_index')} nor {right.get('encounter_index')} carries "
            f"line information; cannot locate the split."
        )

    def _fill_outer_edge(
        self,
        encounter: dict[str, Any],
        page_header_line: dict[int, int],
        total_lines: int,
    ) -> None:
        """Fill a still-missing outer edge from the encounter's page span."""
        page_start = encounter.get("page_start")
        page_end = encounter.get("page_end") or page_start

        if encounter.get("line_start") is None:
            header_line = page_header_line.get(page_start) if page_start is not None else None
            if header_line is None:
                raise EncounterNormalizationError(
                    f"Encounter {encounter.get('encounter_index')}: page {page_start} header "
                    f"not found; cannot set line_start."
                )
            encounter["line_start"] = header_line

        if encounter.get("line_end") is None:
            if page_end is None:
                raise EncounterNormalizationError(
                    f"Encounter {encounter.get('encounter_index')}: missing page_end; "
                    f"cannot set line_end."
                )
            encounter["line_end"] = self._page_end_line(page_end, page_header_line, total_lines)

    def _verify_pair(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        page_header_line: dict[int, int],
        total_lines: int,
    ) -> None:
        """Ensure both ranges are well-formed, in-bounds, and non-overlapping."""
        for encounter in (left, right):
            self._verify_range_bounds(encounter, page_header_line, total_lines)

        if left["line_end"] >= right["line_start"]:
            raise EncounterNormalizationError(
                f"Encounters {left.get('encounter_index')} and {right.get('encounter_index')} "
                f"overlap: left ends at {left['line_end']}, right starts at {right['line_start']}."
            )

    def _verify_range_bounds(
        self,
        encounter: dict[str, Any],
        page_header_line: dict[int, int],
        total_lines: int,
    ) -> None:
        """Check one encounter's range is ordered and within its page span."""
        line_start = encounter["line_start"]
        line_end = encounter["line_end"]
        encounter_id = encounter.get("encounter_index")

        if line_start > line_end:
            raise EncounterNormalizationError(
                f"Encounter {encounter_id} has line_start {line_start} after line_end {line_end}."
            )

        page_start = encounter.get("page_start")
        page_end = encounter.get("page_end") or page_start
        span_first = page_header_line.get(page_start) if page_start is not None else None
        span_last = (
            self._page_end_line(page_end, page_header_line, total_lines)
            if page_end is not None
            else None
        )
        if span_first is not None and line_start < span_first:
            raise EncounterNormalizationError(
                f"Encounter {encounter_id} line_start {line_start} precedes its page span "
                f"start {span_first}."
            )
        if span_last is not None and line_end > span_last:
            raise EncounterNormalizationError(
                f"Encounter {encounter_id} line_end {line_end} exceeds its page span "
                f"end {span_last}."
            )

    def _build_page_header_map(self, lines: list[str]) -> dict[int, int]:
        """Map each page number to the 1-based line index of its ``### Page N`` marker."""
        header_map: dict[int, int] = {}
        for index, line in enumerate(lines):
            match = self._PAGE_HEADER_PATTERN.match(line.strip())
            if match:
                header_map[int(match.group(1))] = index + 1
        return header_map

    @staticmethod
    def _page_end_line(page: int, page_header_line: dict[int, int], total_lines: int) -> int:
        """Return the last 1-based line index that belongs to ``page``."""
        pages_above = [candidate for candidate in page_header_line if candidate > page]
        if pages_above:
            return page_header_line[min(pages_above)] - 1
        return total_lines
