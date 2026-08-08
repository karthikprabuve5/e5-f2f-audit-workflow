"""Assemble the final ``audit`` contract from merge + selection outputs.

:class:`FinalAuditEngine` is a pure, deterministic transform: given the consolidated
``merge_encounters`` document and the ``encounter-selection`` output, it returns the
**identical merge_encounters format with every encounter kept**, and simply surfaces
the selection headline fields at the top of ``results``. It performs no pruning — the
audit result is a lossless superset, so any downstream consumer can derive its own
view (best-only, drop referrals, show-all) from a single document.

It performs no I/O, reads no environment, and reads no clock (``generated_at`` is
injected) — so it is safe to run inside any orchestrator, including a Temporal
activity. The two input mappings are never mutated.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

# Selection headline fields lifted to the top of ``results`` (order preserved).
_SELECTION_RESULT_KEYS: tuple[str, ...] = (
    "best_encounter_index",
    "best_encounter_score",
    "best_is_date_aligned",
    "date_aligned_encounter",
    "excluded_encounters",
)


class FinalAuditEngine:
    """Builds the final ``audit`` dict (all encounters + selection headline fields)."""

    def build(
        self,
        merged_encounters: Mapping[str, Any],
        selection: Mapping[str, Any],
        *,
        generated_at: str,
    ) -> dict[str, Any]:
        """Return the final audit dict for one transaction.

        Args:
            merged_encounters: The consolidated ``merge_encounters`` contract
                (``MergeEncountersEngine.build`` shape) for the transaction.
            selection: The ``encounter-selection`` output for the same transaction.
            generated_at: ISO-8601 timestamp injected by the caller.

        Returns:
            A deep copy of ``merged_encounters`` in the identical format, with every
            encounter retained, where ``results`` is prefixed with the selection
            headline fields (``best_encounter_index``, ``best_encounter_score``,
            ``best_is_date_aligned``, ``date_aligned_encounter``, ``excluded_encounters``)
            plus ``encounter_selection_summary`` (the selection's ``reasoning.summary``
            auditor narrative, ``None`` when absent).
        """
        self._validate_inputs(merged_encounters, selection)
        result = _selection_result(selection)

        out = copy.deepcopy(dict(merged_encounters))
        out["generated_at"] = generated_at

        topics = out.get("results")
        if not isinstance(topics, dict):
            raise ValueError("merged_encounters['results'] must be an object.")

        additions = {key: result.get(key) for key in _SELECTION_RESULT_KEYS}
        additions["encounter_selection_summary"] = _selection_reasoning_summary(selection)
        # New keys first, then the (unpruned) topic blocks — same topic format.
        out["results"] = {**additions, **topics}
        return out

    @staticmethod
    def _validate_inputs(
        merged_encounters: Mapping[str, Any], selection: Mapping[str, Any]
    ) -> None:
        for name, obj in (("merged_encounters", merged_encounters), ("selection", selection)):
            if not isinstance(obj, Mapping):
                raise TypeError(f"{name} must be a mapping, got {type(obj).__name__}.")
        merged_txn = merged_encounters.get("transaction_id")
        selection_txn = selection.get("transaction_id")
        if merged_txn and selection_txn and merged_txn != selection_txn:
            raise ValueError(
                "transaction_id mismatch between inputs: "
                f"merged '{merged_txn}' vs selection '{selection_txn}'."
            )


def _selection_result(selection: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return ``selection['result']`` or fail loudly if it is missing/malformed."""
    result = selection.get("result")
    if not isinstance(result, Mapping):
        raise ValueError("selection['result'] must be an object.")
    return result


def _selection_reasoning_summary(selection: Mapping[str, Any]) -> str | None:
    """Return the selection's top-level ``reasoning.summary`` (``None`` when absent).

    This is the auditor-voice clinical narrative — distinct from ``result``'s
    structured fields — surfaced as ``encounter_selection_summary`` in the audit.
    """
    reasoning = selection.get("reasoning")
    if not isinstance(reasoning, Mapping):
        return None
    summary = reasoning.get("summary")
    return summary if isinstance(summary, str) else None
