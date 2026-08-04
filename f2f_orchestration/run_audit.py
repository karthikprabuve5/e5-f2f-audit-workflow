"""Entrypoint: build the consolidated ``audit-results.json`` from agent outputs.

Configure the run below, then execute from the repo root:

    python -m f2f_orchestration.run_audit

* ``RUN_MODE = RunMode.FULL``     → audit every transaction found under outputs/.
* ``RUN_MODE = RunMode.SELECTED`` → audit only the ids in ``SELECTED_TRANSACTIONS``.

This entrypoint reads each transaction's processed agent outputs from disk
(``DiskAuditSource``), runs the pure :class:`AuditEngine`, and writes one
``audit-results.json`` per transaction. Transactions run one by one; a failing
transaction is logged and skipped, and a batch report is emitted at the end.

An external orchestrator (Temporal, etc.) does not use this entrypoint: it feeds
its own in-memory outputs to the same pure engine via
``AuditEngine().build(TransactionOutputs.from_mapping(payload), generated_at=...)``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from . import bootstrap
from .audit import AuditEngine
from .audit.audit_source import DiskAuditSource
from .bootstrap import RunMode
from .core.logging_setup import get_logger
from .core.result_store import AUDIT_RESULTS_FILENAME

logger = get_logger(__name__)


# ---- Run configuration (edit these) ----
RUN_MODE: RunMode = RunMode.FULL
SELECTED_TRANSACTIONS: list[str] = [
    # "transaction_bailey_loretta_p",
]
# Re-run transactions even if their audit-results.json already exists (overwrites it).
FORCE_RERUN: bool = True


def _build_one(engine: AuditEngine, source: DiskAuditSource, transaction_id: str) -> None:
    outputs = source.load(transaction_id)
    audit = engine.build(outputs, generated_at=datetime.now(UTC).isoformat())
    result_store = bootstrap.build_result_store(transaction_id)
    result_store.store_audit_results(audit)
    logger.info(
        "Audit results built",
        extra={
            "transaction_id": transaction_id,
            "client_id": audit.get("client_id"),
            "failed_agents": audit.get("data_quality", {}).get("failed_agents"),
            "schema_issue_count": len(audit.get("data_quality", {}).get("schema_issues", [])),
        },
    )


def _resolve_transactions(source: DiskAuditSource) -> list[str]:
    if RUN_MODE is RunMode.SELECTED:
        return list(SELECTED_TRANSACTIONS)
    return source.available_transactions()


def _run_batch() -> None:
    source = bootstrap.build_audit_source()
    engine = AuditEngine()
    transaction_ids = _resolve_transactions(source)
    if not transaction_ids:
        logger.warning("No transactions to audit", extra={"mode": str(RUN_MODE)})
        return

    succeeded: list[str] = []
    skipped: list[str] = []
    failed: dict[str, str] = {}

    for transaction_id in transaction_ids:
        if not FORCE_RERUN and bootstrap.output_exists(transaction_id, AUDIT_RESULTS_FILENAME):
            skipped.append(transaction_id)
            logger.info(
                "Audit already built, skipping",
                extra={"transaction_id": transaction_id, "marker": AUDIT_RESULTS_FILENAME},
            )
            continue
        try:
            _build_one(engine, source, transaction_id)
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
