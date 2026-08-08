"""Entrypoint: build the consolidated merge-encounters results from agent outputs.

Configure the run below, then execute from the repo root:

    python -m e5_f2f_audit.run_merge_encounters

* ``RUN_MODE = RunMode.FULL``     → merge every transaction found under outputs/.
* ``RUN_MODE = RunMode.SELECTED`` → merge only the ids in ``SELECTED_TRANSACTIONS``.

This entrypoint reads each transaction's processed agent outputs from disk
(``DiskMergeSource``), runs the pure :class:`MergeEncountersEngine`, and writes one
``merge-encounters/results.json`` per transaction. Transactions run one by one; a
failing transaction is logged and skipped, and a batch report is emitted at the end.

An external orchestrator (Temporal, etc.) does not use this entrypoint: it feeds
its own in-memory outputs to the same pure engine via
``MergeEncountersEngine().build(TransactionOutputs.from_mapping(payload), generated_at=...)``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from . import bootstrap
from .bootstrap import RunMode
from .core.logging_setup import get_logger
from .core.result_store import MERGE_ENCOUNTERS_MARKER
from .merge_encounters import MergeEncountersEngine
from .merge_encounters.merge_source import DiskMergeSource

logger = get_logger(__name__)


# ---- Run configuration (edit these) ----
RUN_MODE: RunMode = RunMode.SELECTED
SELECTED_TRANSACTIONS: list[str] = [
    # "transaction_bailey_loretta_p",
    "transaction_kane_paula"
]
# Re-run transactions even if their merge results already exist (overwrites them).
FORCE_RERUN: bool = True


def _build_one(
    engine: MergeEncountersEngine, source: DiskMergeSource, transaction_id: str
) -> None:
    outputs = source.load(transaction_id)
    merged = engine.build(outputs, generated_at=datetime.now(UTC).isoformat())
    result_store = bootstrap.build_result_store(transaction_id)
    result_store.store_merge_encounters(merged)
    logger.info(
        "Merge-encounters results built",
        extra={
            "transaction_id": transaction_id,
            "client_id": merged.get("client_id"),
            "failed_agents": merged.get("data_quality", {}).get("failed_agents"),
            "schema_issue_count": len(merged.get("data_quality", {}).get("schema_issues", [])),
        },
    )


def _resolve_transactions(source: DiskMergeSource) -> list[str]:
    if RUN_MODE is RunMode.SELECTED:
        return list(SELECTED_TRANSACTIONS)
    return source.available_transactions()


def _run_batch() -> None:
    source = bootstrap.build_merge_source()
    engine = MergeEncountersEngine()
    transaction_ids = _resolve_transactions(source)
    if not transaction_ids:
        logger.warning("No transactions to merge", extra={"mode": str(RUN_MODE)})
        return

    succeeded: list[str] = []
    skipped: list[str] = []
    failed: dict[str, str] = {}

    for transaction_id in transaction_ids:
        if not FORCE_RERUN and bootstrap.output_exists(transaction_id, MERGE_ENCOUNTERS_MARKER):
            skipped.append(transaction_id)
            logger.info(
                "Merge already built, skipping",
                extra={"transaction_id": transaction_id, "marker": MERGE_ENCOUNTERS_MARKER},
            )
            continue
        try:
            _build_one(engine, source, transaction_id)
            succeeded.append(transaction_id)
        except Exception as exc:
            # Batch isolation: one bad transaction must not abort the rest.
            failed[transaction_id] = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Merge build failed",
                extra={"transaction_id": transaction_id, "error_type": type(exc).__name__},
            )

    logger.info(
        "Merge batch complete",
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
