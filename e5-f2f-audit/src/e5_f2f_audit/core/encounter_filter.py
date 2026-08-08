"""Deterministic pre-selection filter: drop non-candidate encounters.

Encounter selection ranks the *clinical* F2F encounters against the claim. Some
classified documents are supporting-only — a ``referral_documents`` note can
corroborate skilled services or the primary reason for home health, but it can
never itself be the face-to-face encounter (CMS: the F2F must be a clinical
encounter performed by a physician or allowed NPP). Letting such a document into
the selection candidate set risks it being scored or picked as the best
encounter, which is a compliance error.

This module removes those encounters from the consolidated ``merge_encounters``
*before* the selection agent sees them, keying purely on the classification
roster's ``encounter_category``. It is a pure function — no I/O, no environment,
no LLM, no global state — so it is reusable identically by the local entrypoint
and by an external orchestrator (e.g. a Temporal activity: ``merge -> filter ->
selection``), and is deterministic/replay-safe.

The excluded encounters are returned alongside the filtered merge results so the
caller can record exactly which indices were dropped (and why) in the final
selection output. The full, unfiltered ``merge-encounters/results.json`` on disk
still retains every encounter's extracted verdicts for the human audit trail; only the
selection *input* is narrowed.

Scope is intentionally a single category today (``referral_documents``); it is a
frozenset so extending it later is a one-line change.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .logging_setup import get_logger

logger = get_logger(__name__)

REFERRAL_CATEGORY = "referral_documents"
EXCLUDED_SELECTION_CATEGORIES: frozenset[str] = frozenset({REFERRAL_CATEGORY})
EXCLUSION_REASON = "referral_document_supporting_only"


def filter_candidates(
    merge_encounters: Mapping[str, Any],
    classification_roster: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Remove supporting-only encounters from the selection candidate set.

    Args:
        merge_encounters: The consolidated merge contract (``MergeEncountersEngine.build``
            shape) whose ``results.<topic>.f2f_encounters[]`` lists carry the
            per-encounter verdicts keyed by ``encounter_index``.
        classification_roster: The F2F classification output — either the full
            object with an ``encounters`` list or a bare list of encounter dicts.
            Each entry must carry ``encounter_index`` and ``encounter_category``.

    Returns:
        A ``(valid_merge_encounters, excluded_encounters)`` tuple. ``valid_merge_encounters``
        is a deep copy of ``merge_encounters`` with every excluded ``encounter_index``
        pruned from each topic's ``f2f_encounters`` list (``poc_485`` blocks are
        left untouched). ``excluded_encounters`` is a list of
        ``{encounter_index, encounter_category, encounter_subcategory, reason}``
        objects, ordered by index, for the caller to surface in the selection
        output.

    The input mappings are never mutated.
    """
    excluded_by_index = _excluded_encounters_by_index(classification_roster)
    excluded_indices = set(excluded_by_index)

    filtered = copy.deepcopy(dict(merge_encounters))
    if excluded_indices:
        _prune_topics(filtered, excluded_indices)

    excluded_encounters = [excluded_by_index[index] for index in sorted(excluded_by_index)]

    logger.info(
        "Filtered selection candidates",
        extra={
            "excluded_categories": sorted(EXCLUDED_SELECTION_CATEGORIES),
            "excluded_encounter_indices": sorted(excluded_indices),
            "excluded_count": len(excluded_indices),
        },
    )
    return filtered, excluded_encounters


def _excluded_encounters_by_index(
    classification_roster: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Map each excluded ``encounter_index`` to its exclusion record."""
    excluded: dict[int, dict[str, Any]] = {}
    for entry in _roster_encounters(classification_roster):
        category = entry.get("encounter_category")
        if category not in EXCLUDED_SELECTION_CATEGORIES:
            continue
        index = _coerce_index(entry.get("encounter_index"))
        if index is None:
            logger.warning(
                "Skipping excluded encounter with unusable index",
                extra={"encounter_category": category, "encounter_index": entry.get("encounter_index")},
            )
            continue
        excluded[index] = {
            "encounter_index": index,
            "encounter_category": category,
            "encounter_subcategory": entry.get("encounter_subcategory"),
            "reason": EXCLUSION_REASON,
        }
    return excluded


def _roster_encounters(
    classification_roster: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Return the list of encounter dicts from either roster shape."""
    if isinstance(classification_roster, Mapping):
        encounters = classification_roster.get("encounters", [])
    else:
        encounters = classification_roster
    if not isinstance(encounters, Sequence):
        raise ValueError(
            "classification_roster must be a list of encounters or an object with "
            f"an 'encounters' list; got {type(encounters).__name__}."
        )
    return [entry for entry in encounters if isinstance(entry, Mapping)]


def _prune_topics(merge_encounters: dict[str, Any], excluded_indices: set[int]) -> None:
    """Drop excluded indices from every topic's ``f2f_encounters`` list in place."""
    results = merge_encounters.get("results")
    if not isinstance(results, dict):
        return
    for topic in results.values():
        if not isinstance(topic, dict):
            continue
        encounters = topic.get("f2f_encounters")
        if not isinstance(encounters, list):
            continue
        topic["f2f_encounters"] = [
            encounter
            for encounter in encounters
            if _coerce_index(
                encounter.get("encounter_index") if isinstance(encounter, Mapping) else None
            )
            not in excluded_indices
        ]


def _coerce_index(value: Any) -> int | None:
    """Best-effort coercion of an ``encounter_index`` to ``int`` (``None`` if unusable)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None
