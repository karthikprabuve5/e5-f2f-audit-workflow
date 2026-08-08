"""Entrypoint: run the F2F audit pipeline (local dev).

Configure the run below, then execute from the repo root:

    python -m f2f_orchestration.run_f2f

* ``RUN_MODE = RunMode.FULL``     → run every transaction found under ocr-markdown/.
* ``RUN_MODE = RunMode.SELECTED`` → run only the ids in ``SELECTED_TRANSACTIONS``.

Each transaction reads its F2F.md and the POC anchors saved by ``run_poc``, so
F2F can be iterated independently. Transactions run one by one; a failing
transaction is logged and skipped, and a batch report is emitted at the end.
"""

from __future__ import annotations

import asyncio

from . import bootstrap
from .bootstrap import RunMode
from .core.document_source import DocumentKind, DocumentSource
from .core.logging_setup import get_logger
from .core.result_store import SUMMARY_FILENAME
from .pipelines.f2f_pipeline import F2fPipeline

logger = get_logger(__name__)

# ---- Run configuration (edit these) ----
RUN_MODE: RunMode = RunMode.SELECTED
SELECTED_TRANSACTIONS: list[str] = [
# "transaction_anzaldua_esther",
# "transaction_fisk_rolana",
# "transaction_brewer_judy",
# "transaction_narvaez_jose_a",
# "transaction_reeves_maudie",
"transaction_kane_paula",
]
# Re-run transactions even if their F2F summary already exists (overwrites it).
FORCE_RERUN: bool = False


async def _run_one(
    pipeline: F2fPipeline, document_source: DocumentSource, transaction_id: str
) -> None:
    f2f_content = document_source.load(transaction_id, DocumentKind.F2F)
    anchors = bootstrap.load_saved_anchors(transaction_id)
    result_store = bootstrap.build_result_store(transaction_id)
    results = await pipeline.run(
        transaction_id=f"{transaction_id}_run2",
        f2f_document_content=f2f_content,
        anchors=anchors,
        result_store=result_store,
    )
    summary = results.get("summary") or {}
    logger.info(
        "F2F pipeline finished",
        extra={
            "transaction_id": transaction_id,
            "encounter_count": summary.get("encounter_count"),
            "totals": summary.get("totals"),
        },
    )


async def _run_batch(transaction_ids: list[str]) -> None:
    if not transaction_ids:
        logger.warning("No transactions to run", extra={"mode": str(RUN_MODE)})
        return

    pipeline = bootstrap.build_f2f_pipeline()
    document_source = bootstrap.build_document_source()
    succeeded: list[str] = []
    skipped: list[str] = []
    failed: dict[str, str] = {}

    for transaction_id in transaction_ids:
        if not FORCE_RERUN and bootstrap.output_exists(transaction_id, SUMMARY_FILENAME):
            skipped.append(transaction_id)
            logger.info(
                "Transaction already processed, skipping",
                extra={"transaction_id": transaction_id, "marker": SUMMARY_FILENAME},
            )
            continue
        try:
            await _run_one(pipeline, document_source, transaction_id)
            succeeded.append(transaction_id)
        except Exception as exc:
            # Batch isolation: one bad transaction must not abort the rest.
            failed[transaction_id] = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Transaction failed",
                extra={"transaction_id": transaction_id, "error_type": type(exc).__name__},
            )

    logger.info(
        "F2F batch complete",
        extra={
            "total": len(transaction_ids),
            "succeeded": succeeded,
            "skipped": skipped,
            "failed": failed,
        },
    )


def main() -> None:
    bootstrap.load_environment()
    transaction_ids = bootstrap.resolve_transactions(
        DocumentKind.F2F, RUN_MODE, SELECTED_TRANSACTIONS
    )
    asyncio.run(_run_batch(transaction_ids))


if __name__ == "__main__":
    main()
