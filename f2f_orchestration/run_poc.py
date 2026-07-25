"""Entrypoint: run the POC/485 pipeline (local dev).

Configure the run below, then execute from the repo root:

    python -m f2f_orchestration.run_poc

* ``RUN_MODE = RunMode.FULL``     → run every transaction found under ocr-markdown/.
* ``RUN_MODE = RunMode.SELECTED`` → run only the ids in ``SELECTED_TRANSACTIONS``.

Transactions run one by one (each already fans out internally). A failing
transaction is logged and skipped; a batch report is emitted at the end.
"""

from __future__ import annotations

import asyncio

from . import bootstrap
from .bootstrap import RunMode
from .core.document_source import DocumentKind, DocumentSource
from .core.logging_setup import get_logger
from .pipelines.poc_pipeline import PocPipeline

logger = get_logger(__name__)

# ---- Run configuration (edit these) ----
RUN_MODE: RunMode = RunMode.SELECTED
SELECTED_TRANSACTIONS: list[str] = [
    "transaction_aguero_baltazar",
]


async def _run_one(
    pipeline: PocPipeline, document_source: DocumentSource, transaction_id: str
) -> None:
    poc_content = document_source.load(transaction_id, DocumentKind.POC)
    result_store = bootstrap.build_result_store(transaction_id)
    anchors = await pipeline.run(
        transaction_id=transaction_id,
        poc_document_content=poc_content,
        client_name=bootstrap.client_name(),
        result_store=result_store,
    )
    logger.info(
        "POC pipeline finished",
        extra={"transaction_id": transaction_id, "anchors": anchors.placeholders()},
    )


async def _run_batch(transaction_ids: list[str]) -> None:
    if not transaction_ids:
        logger.warning("No transactions to run", extra={"mode": str(RUN_MODE)})
        return

    pipeline = bootstrap.build_poc_pipeline()
    document_source = bootstrap.build_document_source()
    succeeded: list[str] = []
    failed: dict[str, str] = {}

    for transaction_id in transaction_ids:
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
        "POC batch complete",
        extra={"total": len(transaction_ids), "succeeded": succeeded, "failed": failed},
    )


def main() -> None:
    bootstrap.load_environment()
    transaction_ids = bootstrap.resolve_transactions(
        DocumentKind.POC, RUN_MODE, SELECTED_TRANSACTIONS
    )
    asyncio.run(_run_batch(transaction_ids))


if __name__ == "__main__":
    main()
