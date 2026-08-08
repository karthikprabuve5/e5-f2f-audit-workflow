"""Entrypoint: build the final audit results per transaction (local dev).

Configure the run below, then execute from the repo root:

    python -m f2f_orchestration.run_audit

* ``RUN_MODE = RunMode.FULL``     → audit every transaction that has both a
  ``merge-encounters/results.json`` and an ``encounter-selection/results.json``.
* ``RUN_MODE = RunMode.SELECTED`` → audit only the ids in ``SELECTED_TRANSACTIONS``.

This entrypoint reads each transaction's consolidated ``merge-encounters/results.json``
and its ``encounter-selection/results.json`` from disk, runs the pure
:class:`FinalAuditEngine`, and writes one ``outputs/<txn>/audit/results.json`` per
transaction. The final audit keeps the identical merge-encounters format but retains
only the selected best encounter plus the excluded (referral) encounters, and
surfaces the selection headline fields at the top of ``results``. Transactions run
one by one; a failing transaction is logged and skipped, and a batch report is
emitted at the end.

An external orchestrator (Temporal, etc.) does not use this entrypoint: it feeds its
own in-memory merge + selection payloads to the same pure engine via
``FinalAuditEngine().build(merged, selection, generated_at=...)``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from . import bootstrap
from .audit import FinalAuditEngine
from .bootstrap import RunMode
from .core.logging_setup import get_logger
from .core.result_store import (
    AUDIT_MARKER,
    MERGE_ENCOUNTERS_MARKER,
    SELECTION_RESULT_MARKER,
)

logger = get_logger(__name__)


# ---- Run configuration (edit these) ----
RUN_MODE: RunMode = RunMode.SELECTED
SELECTED_TRANSACTIONS: list[str] = [
    "transaction_kane_paula",
]
# Re-run transactions even if their audit result already exists (overwrites it).
FORCE_RERUN: bool = True


def _build_one(engine: FinalAuditEngine, transaction_id: str) -> None:
    merged = bootstrap.load_merge_encounters(transaction_id)
    selection = bootstrap.load_selection(transaction_id)
    audit = engine.build(merged, selection, generated_at=datetime.now(UTC).isoformat())
    result_store = bootstrap.build_result_store(transaction_id)
    result_store.store_audit(audit)

    results = audit.get("results", {})
    logger.info(
        "Final audit results built",
        extra={
            "transaction_id": transaction_id,
            "client_id": audit.get("client_id"),
            "best_encounter_index": results.get("best_encounter_index"),
            "excluded_encounter_count": len(results.get("excluded_encounters", [])),
        },
    )


def _resolve_transactions() -> list[str]:
    if RUN_MODE is RunMode.SELECTED:
        return list(SELECTED_TRANSACTIONS)
    # FULL: every transaction that has both a merge and a selection result on disk.
    source = bootstrap.build_merge_source()
    return sorted(
        transaction_id
        for transaction_id in source.available_transactions()
        if bootstrap.output_exists(transaction_id, MERGE_ENCOUNTERS_MARKER)
        and bootstrap.output_exists(transaction_id, SELECTION_RESULT_MARKER)
    )


def _run_batch() -> None:
    transaction_ids = _resolve_transactions()
    if not transaction_ids:
        logger.warning("No transactions to audit", extra={"mode": str(RUN_MODE)})
        return

    engine = bootstrap.build_final_audit_engine()
    succeeded: list[str] = []
    skipped: list[str] = []
    failed: dict[str, str] = {}

    for transaction_id in transaction_ids:
        if not FORCE_RERUN and bootstrap.output_exists(transaction_id, AUDIT_MARKER):
            skipped.append(transaction_id)
            logger.info(
                "Audit already built, skipping",
                extra={"transaction_id": transaction_id, "marker": AUDIT_MARKER},
            )
            continue
        try:
            _build_one(engine, transaction_id)
            succeeded.append(transaction_id)
        except Exception as exc:
            # Batch isolation: one bad transaction must not abort the rest.
            failed[transaction_id] = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Audit build failed",
                extra={"transaction_id": transaction_id, "error_type": type(exc).__name__},
            )

    logger.info(
        "Audit batch complete",
        extra={
            "total": len(transaction_ids),
            "succeeded": succeeded,
            "skipped": skipped,
            "failed": failed,
        },
    )


def main() -> None:
    bootstrap.load_environment()
    _run_batch()


if __name__ == "__main__":
    main()
