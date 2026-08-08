"""Resolve ``evidence_refs`` / POC anchors into inline evidence objects.

Agent outputs keep location data in a single ``evidence[]`` array and reference it
elsewhere by ``evidence_id`` (F2F agents) or ``anchor`` (poc-485 extraction). The
merge_encounters contract instead inlines the *resolved* evidence wherever it is
cited, so the downstream consumer never has to chase references.

This module is the one place that performs that resolution. It is pure (no I/O),
and it never emits a dangling reference: an id/anchor with no matching entry simply
contributes nothing.

Projected evidence shape:
- F2F:  ``{verbiage, page, line_start, line_end, signal_strength}``
- POC:  ``{verbiage, page, line_start, line_end}`` (poc anchors carry no signal)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

_REFS_SUFFIX = "_refs"


class EvidenceResolver:
    """Turns evidence references into inline evidence objects."""

    def resolve_agent_refs(
        self,
        agent_output: dict[str, Any] | None,
        refs: Sequence[str] | None,
        *,
        include_signal_strength: bool = True,
    ) -> list[dict[str, Any]]:
        """Resolve F2F ``evidence_refs`` against an agent output's ``evidence[]``."""
        index = _index_by_evidence_id(agent_output)
        return self._resolve(index, refs, include_signal_strength=include_signal_strength)

    def resolve_poc_anchor(
        self, poc_extraction: dict[str, Any] | None, anchor: str
    ) -> list[dict[str, Any]]:
        """Resolve every poc ``evidence[]`` entry tagged with ``anchor``."""
        entries = (poc_extraction or {}).get("evidence") or []
        return [
            self._project(entry, include_signal_strength=False)
            for entry in entries
            if isinstance(entry, dict) and entry.get("anchor") == anchor
        ]

    def inline_nested(
        self,
        node: Any,
        agent_output: dict[str, Any] | None,
        *,
        include_signal_strength: bool = True,
    ) -> Any:
        """Deep-copy ``node``, replacing every ``*evidence_refs`` with resolved evidence.

        Each ``<name>_evidence_refs`` (or bare ``evidence_refs``) list is replaced
        by ``<name>_evidence`` (or ``evidence``) holding the resolved objects. All
        other keys/values are preserved. Used for pass-through objects such as
        ``eligible_provider`` that embed references at several depths.
        """
        index = _index_by_evidence_id(agent_output)
        return self._inline(node, index, include_signal_strength=include_signal_strength)

    # -- Internals -------------------------------------------------------------

    def _inline(
        self, node: Any, index: dict[str, dict[str, Any]], *, include_signal_strength: bool
    ) -> Any:
        if isinstance(node, dict):
            result: dict[str, Any] = {}
            for key, value in node.items():
                if key.endswith("evidence_refs") and isinstance(value, list):
                    resolved_key = key[: -len(_REFS_SUFFIX)]  # ..._refs -> ...
                    result[resolved_key] = self._resolve(
                        index, value, include_signal_strength=include_signal_strength
                    )
                else:
                    result[key] = self._inline(
                        value, index, include_signal_strength=include_signal_strength
                    )
            return result
        if isinstance(node, list):
            return [
                self._inline(item, index, include_signal_strength=include_signal_strength)
                for item in node
            ]
        return node

    def _resolve(
        self,
        index: dict[str, dict[str, Any]],
        refs: Sequence[str] | None,
        *,
        include_signal_strength: bool,
    ) -> list[dict[str, Any]]:
        resolved: list[dict[str, Any]] = []
        for ref in refs or []:
            entry = index.get(ref)
            if entry is not None:
                resolved.append(
                    self._project(entry, include_signal_strength=include_signal_strength)
                )
        return resolved

    @staticmethod
    def _project(entry: dict[str, Any], *, include_signal_strength: bool) -> dict[str, Any]:
        """Reduce a raw evidence entry to the inline merge shape (stable key order)."""
        projected: dict[str, Any] = {
            "verbiage": entry.get("verbiage"),
            "page": entry.get("page"),
            "line_start": entry.get("line_start"),
            "line_end": entry.get("line_end"),
        }
        if include_signal_strength:
            projected["signal_strength"] = entry.get("signal_strength")
        return projected


def _index_by_evidence_id(agent_output: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Build an ``{evidence_id: entry}`` index from an agent output's ``evidence[]``."""
    index: dict[str, dict[str, Any]] = {}
    for entry in (agent_output or {}).get("evidence") or []:
        if isinstance(entry, dict):
            evidence_id = entry.get("evidence_id")
            if evidence_id is not None:
                index[str(evidence_id)] = entry
    return index
