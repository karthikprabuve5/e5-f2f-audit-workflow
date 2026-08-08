"""Split a classified document into per-encounter text chunks.

``EncounterSplitter`` turns the classification output (encounters with page /
line boundaries) into one markdown chunk per encounter, using the ``### Page N``
markers as the authoritative page anchors. Encounters that share a page are
split on 1-based line numbers, and the page header is prepended so each chunk is
self-contained.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .logging_setup import get_logger

logger = get_logger(__name__)


class EncounterSplitter:
    """Splits a document into per-encounter chunks from classification metadata."""

    _PAGE_HEADER_PATTERN = re.compile(r"^###\s+Page\s+(\d+)\s*$")

    def split(
        self,
        document: str,
        encounters: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    ) -> list[str]:
        """Return one chunk per encounter, aligned with the encounters order."""
        encounter_list = self._normalize_encounters(encounters)
        lines = document.splitlines()
        page_header_line = self._build_page_header_map(lines)

        chunks = [
            self._extract_chunk(encounter, lines, page_header_line)
            for encounter in encounter_list
        ]
        logger.debug("Split document into encounter chunks", extra={"chunk_count": len(chunks)})
        return chunks

    @staticmethod
    def _normalize_encounters(
        encounters: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    ) -> Sequence[Mapping[str, Any]]:
        if isinstance(encounters, Mapping):
            return encounters.get("encounters", [])
        return encounters

    def _build_page_header_map(self, lines: list[str]) -> dict[int, int]:
        """Map each page number to the 1-based line index of its ``### Page N`` marker."""
        header_map: dict[int, int] = {}
        for index, line in enumerate(lines):
            match = self._PAGE_HEADER_PATTERN.match(line.strip())
            if match:
                header_map[int(match.group(1))] = index + 1
        return header_map

    def _extract_chunk(
        self,
        encounter: Mapping[str, Any],
        lines: list[str],
        page_header_line: dict[int, int],
    ) -> str:
        page_start = encounter["page_start"]
        page_end = encounter["page_end"]
        line_start = encounter.get("line_start")
        line_end = encounter.get("line_end")

        if line_start is None or line_end is None:
            return self._extract_whole_pages(page_start, page_end, lines, page_header_line)
        return self._extract_line_range(page_start, line_start, line_end, lines, page_header_line)

    def _extract_whole_pages(
        self,
        page_start: int,
        page_end: int,
        lines: list[str],
        page_header_line: dict[int, int],
    ) -> str:
        first_line = page_header_line.get(page_start)
        if first_line is None:
            logger.warning(
                "Page header not found; encounter chunk is empty",
                extra={"page_start": page_start, "page_end": page_end},
            )
            return ""
        last_line = self._page_end_line(page_end, page_header_line, len(lines))
        return self._join_lines(lines, first_line, last_line).strip()

    def _extract_line_range(
        self,
        page_start: int,
        line_start: int,
        line_end: int,
        lines: list[str],
        page_header_line: dict[int, int],
    ) -> str:
        chunk_lines = [lines[i - 1] for i in range(line_start, line_end + 1) if 1 <= i <= len(lines)]
        if not chunk_lines:
            logger.warning(
                "Encounter line range out of bounds; chunk has header only",
                extra={"page_start": page_start, "line_start": line_start, "line_end": line_end},
            )

        expected_header = f"### Page {page_start}"
        first_non_blank = next((line.strip() for line in chunk_lines if line.strip()), "")
        if first_non_blank != expected_header:
            chunk_lines = [expected_header, *chunk_lines]

        return "\n".join(chunk_lines).strip()

    @staticmethod
    def _page_end_line(page: int, page_header_line: dict[int, int], total_lines: int) -> int:
        """Return the last 1-based line index that belongs to ``page``."""
        pages_above = [candidate for candidate in page_header_line if candidate > page]
        if pages_above:
            return page_header_line[min(pages_above)] - 1
        return total_lines

    @staticmethod
    def _join_lines(lines: list[str], first_line: int, last_line: int) -> str:
        return "\n".join(
            lines[i - 1] for i in range(first_line, last_line + 1) if 1 <= i <= len(lines)
        )
