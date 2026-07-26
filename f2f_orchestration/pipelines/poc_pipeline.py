"""POC/485 pipeline — produces the anchors the F2F pipeline runs against.

Runs, under one Langfuse ``poc`` trace, two sequential agents on the POC
document: ``classification`` (stored for parity with the F2F flow) and
``poc_485_extraction`` (the anchor source). Both results are recorded in the
shared ``ResultStore``; the parsed anchors are returned for the F2F pipeline.

Extraction only runs when classification found the CMS-485 plan-of-care
encounter — category ``poc_485`` and subcategory ``2.1``. If none is present,
``POCClassificationError`` is raised so the transaction fails cleanly rather than
extracting anchors from a document that is not a plan of care.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..core.anchors import AnchorSet
from ..core.detection import CATEGORY_POC_485, SUBCATEGORY_POC_485, AgentName
from ..core.logging_setup import get_logger
from ..core.result_store import ResultStore
from .base_pipeline import BasePipeline

logger = get_logger(__name__)


class POCClassificationError(RuntimeError):
    """Raised when the POC document has no ``poc_485`` encounter to extract from."""


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

                self._select_poc_encounter(classification, transaction_id)

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

    @staticmethod
    def _select_poc_encounter(
        classification: Mapping[str, Any], transaction_id: str
    ) -> Mapping[str, Any]:
        """Return the first plan-of-care encounter, or raise if none is present.

        A match requires both category ``poc_485`` and subcategory ``2.1``.
        Extraction is gated on this: a POC document without the CMS-485
        plan-of-care encounter must not proceed to anchor extraction.
        """
        encounters = classification.get("encounters", [])
        for encounter in encounters:
            is_poc_485 = (
                encounter.get("encounter_category") == CATEGORY_POC_485
                and encounter.get("encounter_subcategory") == SUBCATEGORY_POC_485
            )
            if is_poc_485:
                logger.info(
                    "Selected POC 485 encounter",
                    extra={
                        "transaction_id": transaction_id,
                        "encounter_index": encounter.get("encounter_index"),
                    },
                )
                return encounter

        found = [
            (encounter.get("encounter_category"), encounter.get("encounter_subcategory"))
            for encounter in encounters
        ]
        logger.error(
            "No matching poc_485 / 2.1 encounter in POC classification",
            extra={
                "transaction_id": transaction_id,
                "encounter_count": len(encounters),
                "found_category_subcategory": found,
            },
        )
        raise POCClassificationError(
            f"POC classification for '{transaction_id}' has no "
            f"'{CATEGORY_POC_485}' / '{SUBCATEGORY_POC_485}' encounter "
            f"(found {len(encounters)}: {found})."
        )
