"""POC/485 pipeline — produces the anchors the F2F pipeline runs against.

Runs, under one Langfuse ``poc`` trace, two sequential agents on the POC
document: ``classification`` (stored for parity with the F2F flow) and
``poc_485_extraction`` (the anchor source). Both results are recorded in the
shared ``ResultStore``; the parsed anchors are returned for the F2F pipeline.
"""

from __future__ import annotations

from ..core.anchors import AnchorSet
from ..core.detection import AgentName
from ..core.logging_setup import get_logger
from ..core.result_store import ResultStore
from .base_pipeline import BasePipeline

logger = get_logger(__name__)


class PocPipeline(BasePipeline):
    """Orchestrates the POC classification and 485 anchor extraction."""

    async def run(
        self,
        *,
        transaction_id: str,
        poc_document_content: str,
        client_name: str,
        result_store: ResultStore,
    ) -> AnchorSet:
        """Run the POC pipeline and return the anchors for the F2F pipeline."""
        logger.info("Starting POC pipeline", extra={"transaction_id": transaction_id})
        span_metadata = {"transaction_id": transaction_id, "document_kind": "poc"}

        try:
            with self._tracer.pipeline_trace("poc", transaction_id):
                classification = await self._run_agent(
                    AgentName.CLASSIFICATION,
                    document_content=poc_document_content,
                    span_metadata=span_metadata,
                )
                result_store.store_classification("poc", classification)

                extraction = await self._run_agent(
                    AgentName.POC_485_EXTRACTION,
                    document_content=poc_document_content,
                    span_metadata=span_metadata,
                )
                result_store.store_poc_extraction(extraction)

                anchors = AnchorSet.from_poc_extraction(extraction, client_name=client_name)
        finally:
            self._tracer.flush()

        logger.info(
            "POC pipeline complete",
            extra={"transaction_id": transaction_id, "client_name": client_name},
        )
        return anchors
