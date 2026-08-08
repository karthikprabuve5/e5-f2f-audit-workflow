"""Entrypoint: pick the best F2F encounter per transaction (local dev).

Configure the run below, then execute from the repo root:

    python -m f2f_orchestration.run_selection

* ``RUN_MODE = RunMode.FULL``     → select for every transaction that has both a
  ``merge-encounters/results.json`` and an entry in the SOC date map.
* ``RUN_MODE = RunMode.SELECTED`` → select only for the ids in ``SELECTED_TRANSACTIONS``.

This entrypoint reads each transaction's consolidated ``merge-encounters/results.json``
and its F2F classification roster (``classification/f2f.json``) from disk, deterministically
filters supporting-only encounters (``referral_documents``) out of the candidate
set via :func:`filter_candidates`, looks up its start-of-care date in the local
SOC map (``soc_dates.json`` by default, override via ``SOC_DATES_FILE``), runs the
pure :class:`SelectionPipeline`, and writes ``outputs/<txn>/encounter-selection/results.json``
(+ a ``results-raw.json`` sibling). The excluded referral indices are recorded in
the result. Transactions run one by one; a failing transaction is logged and
skipped, and a batch report is emitted at the end.

SOC is a required selection input. A transaction missing from the SOC map is a
configuration error: it is reported as failed (never silently selected without a
timing window).

An external orchestrator (Temporal, etc.) does not use this entrypoint: it calls
the same two pure primitives — ``filter_candidates(merge_encounters, classification_roster)``
then ``SelectionPipeline(...).run(transaction_id=..., merge_encounters=<filtered>,
soc_date=..., client_name=..., excluded_encounters=...)`` — and persists
``output.processed`` to its own sink.
"""

from __future__ import annotations

import asyncio

from . import bootstrap
from .bootstrap import RunMode
from .core.encounter_filter import filter_candidates
from .core.logging_setup import get_logger
from .core.result_store import MERGE_ENCOUNTERS_MARKER, SELECTION_RESULT_MARKER
from .pipelines.selection_pipeline import SelectionPipeline

logger = get_logger(__name__)


# ---- Run configuration (edit these) ----
RUN_MODE: RunMode = RunMode.SELECTED
SELECTED_TRANSACTIONS: list[str] = [
    "transaction_kane_paula",
]
# Re-run transactions even if their selection result already exists (overwrites it).
FORCE_RERUN: bool = True


async def _select_one(
    pipeline: SelectionPipeline,
    transaction_id: str,
    *,
    soc_date: str,
    client_name: str,
) -> None:
    merge_encounters = bootstrap.load_merge_encounters(transaction_id)
    classification_roster = bootstrap.load_classification_roster(transaction_id)
    # Deterministic pre-filter: strip supporting-only encounters (referral
    # documents) from the candidate set before the agent ranks them. Mirrors the
    # Temporal boundary (merge -> filter -> selection).
    candidate_merge_encounters, excluded_encounters = filter_candidates(
        merge_encounters, classification_roster
    )
    output = await pipeline.run(
        transaction_id=transaction_id,
        merge_encounters=candidate_merge_encounters,
        soc_date=soc_date,
        client_name=client_name,
        excluded_encounters=excluded_encounters,
    )
    result_store = bootstrap.build_result_store(transaction_id)
    result_store.store_selection(output.processed, raw=output.raw)

    selection = output.processed.get("result", {})
    logger.info(
        "Selection result stored",
        extra={
            "transaction_id": transaction_id,
            "best_encounter_index": selection.get("best_encounter_index"),
            "decision": selection.get("decision"),
            "excluded_encounter_indices": selection.get("excluded_encounter_indices", []),
            "schema_valid": output.validation.schema_valid,
        },
    )


def _resolve_transactions(soc_dates: dict[str, str]) -> list[str]:
    if RUN_MODE is RunMode.SELECTED:
        return list(SELECTED_TRANSACTIONS)
    # FULL: every transaction that has an audit result AND a SOC date on file.
    return sorted(
        transaction_id
        for transaction_id in soc_dates
        if bootstrap.output_exists(transaction_id, MERGE_ENCOUNTERS_MARKER)
    )


async def _run_batch() -> None:
    soc_dates = bootstrap.load_soc_dates()
    client_name = bootstrap.client_name()
    transaction_ids = _resolve_transactions(soc_dates)
    if not transaction_ids:
        logger.warning("No transactions to select", extra={"mode": str(RUN_MODE)})
        return

    pipeline = bootstrap.build_selection_pipeline()
    succeeded: list[str] = []
    skipped: list[str] = []
    failed: dict[str, str] = {}

    for transaction_id in transaction_ids:
        if not FORCE_RERUN and bootstrap.output_exists(transaction_id, SELECTION_RESULT_MARKER):
            skipped.append(transaction_id)
            logger.info(
                "Selection already built, skipping",
                extra={"transaction_id": transaction_id, "marker": SELECTION_RESULT_MARKER},
            )
            continue

        soc_date = soc_dates.get(transaction_id)
        if not soc_date:
            # SOC is a required input; a missing entry is a config error, surfaced
            # loudly as a failure rather than selecting without a timing window.
            failed[transaction_id] = "missing_soc_date: no entry in the SOC date map"
            logger.error(
                "Missing SOC date for transaction",
                extra={"transaction_id": transaction_id},
            )
            continue

        try:
            await _select_one(
                pipeline, transaction_id, soc_date=soc_date, client_name=client_name
            )
            succeeded.append(transaction_id)
        except Exception as exc:
            # Batch isolation: one bad transaction must not abort the rest.
            failed[transaction_id] = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Selection failed",
                extra={"transaction_id": transaction_id, "error_type": type(exc).__name__},
            )

    logger.info(
        "Selection batch complete",
        extra={
            "total": len(transaction_ids),
            "succeeded": succeeded,
            "skipped": skipped,
            "failed": failed,
        },
    )


def main() -> None:
    bootstrap.load_environment()
    asyncio.run(_run_batch())


if __name__ == "__main__":
    main()
