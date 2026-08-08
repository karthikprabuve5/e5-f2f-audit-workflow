"""F2F pipeline — the parallel audit core.

Under one Langfuse ``f2f`` trace: classify ``f2f.md``, split it into per-encounter
chunks, then process every encounter **in parallel** and, within each encounter,
run its selected agents **in parallel** — all against the POC anchors. The global
semaphore in :class:`BasePipeline` bounds the total in-flight Bedrock calls.

Failures are isolated: one agent (or one encounter) failing never cancels its
siblings. Every failure is captured in the per-encounter roll-up and the final
``_summary-results.json``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from ..agents.agent_factory import AgentOutput, AgentOutputError
from ..core.anchors import AnchorSet
from ..core.detection import AgentName, EncounterAgentSelector
from ..core.encounter_normalizer import EncounterNormalizer
from ..core.encounter_splitter import EncounterSplitter
from ..core.logging_setup import get_logger
from ..core.result_store import ResultStore
from .base_pipeline import BasePipeline

logger = get_logger(__name__)


def _persist_raw_on_failure(
    result_store: ResultStore,
    agent_name: str,
    encounter_index: int,
    outcome: BaseException,
) -> None:
    """Persist an agent's raw output when it failed with unparseable JSON.

    Only :class:`AgentOutputError` carries ``raw_content``; other failures (e.g.
    throttling) have no agent output to save.
    """
    raw_content = getattr(outcome, "raw_content", None) if isinstance(outcome, AgentOutputError) else None
    if not raw_content:
        return
    try:
        result_store.store_raw_text(agent_name, encounter_index, raw_content)
    except OSError as write_error:
        # Traceability persistence must never mask the real agent failure; the
        # agent error is already recorded, so we only warn here.
        logger.warning(
            "Failed to persist raw output for failed agent",
            extra={
                "encounter_index": encounter_index,
                "agent": agent_name,
                "error_type": type(write_error).__name__,
            },
        )


class F2fPipeline(BasePipeline):
    """Orchestrates classification and the parallel per-encounter F2F agents."""

    async def run(
        self,
        *,
        transaction_id: str,
        f2f_document_content: str,
        anchors: AnchorSet,
        result_store: ResultStore,
    ) -> dict[str, Any]:
        """Run the full F2F pipeline and return the in-memory results dict."""
        logger.info("Starting F2F pipeline", extra={"transaction_id": transaction_id})
        splitter = EncounterSplitter()
        normalizer = EncounterNormalizer()
        selector = EncounterAgentSelector()
        replacements = anchors.placeholders()

        try:
            with self._tracer.pipeline_trace("f2f", transaction_id):
                classification = await self._run_agent(
                    AgentName.CLASSIFICATION,
                    document_content=f2f_document_content,
                    span_metadata={"transaction_id": transaction_id, "document_kind": "f2f"},
                )

                encounters = list(classification.processed.get("encounters", []))
                if not encounters:
                    # Not an exception, but must not pass silently: a zero-encounter
                    # run almost always means malformed/empty classification output.
                    logger.warning(
                        "Classification returned no encounters; no F2F agents will run",
                        extra={"transaction_id": transaction_id},
                    )

                # Repair shared-page line boundaries before splitting so co-page
                # encounters don't bleed into each other. Never raises: un-repairable
                # pages are left as-is for whole-page fallback. f2f.json holds the
                # (repaired) view; f2f-raw.json holds the untouched agent output.
                encounters = normalizer.normalize(f2f_document_content, encounters)
                classification.processed["encounters"] = encounters
                result_store.store_classification(
                    "f2f", classification.processed, raw=classification.raw
                )

                chunks = splitter.split(f2f_document_content, encounters)

                outcomes = await asyncio.gather(
                    *(
                        self._run_encounter(
                            encounter_index=int(encounter.get("encounter_index") or position),
                            transaction_id=transaction_id,
                            encounter=encounter,
                            chunk=chunk,
                            selector=selector,
                            replacements=replacements,
                            result_store=result_store,
                        )
                        for position, (encounter, chunk) in enumerate(
                            zip(encounters, chunks), start=1
                        )
                    ),
                    return_exceptions=True,
                )
                encounter_summaries = self._collect_encounter_summaries(encounters, outcomes)
                summary = self._build_summary(
                    transaction_id=transaction_id,
                    anchors=anchors,
                    encounter_summaries=encounter_summaries,
                    trace_reference=self._tracer.current_trace_reference(),
                )
                result_store.store_summary(summary)
        finally:
            self._tracer.flush()

        logger.info(
            "F2F pipeline complete",
            extra={
                "transaction_id": transaction_id,
                "encounter_count": len(encounter_summaries),
            },
        )
        return result_store.results

    async def _run_encounter(
        self,
        *,
        encounter_index: int,
        transaction_id: str,
        encounter: Mapping[str, Any],
        chunk: str,
        selector: EncounterAgentSelector,
        replacements: Mapping[str, str],
        result_store: ResultStore,
    ) -> dict[str, Any]:
        """Run all selected agents for one encounter in parallel and record them."""
        agents = selector.select(encounter)
        span_metadata = {
            "transaction_id": transaction_id,
            "encounter_index": encounter_index,
            "encounter_category": encounter.get("encounter_category"),
        }

        with self._tracer.encounter_span(encounter_index, metadata=span_metadata):
            agent_results = await asyncio.gather(
                *(
                    self._run_agent(
                        agent,
                        document_content=chunk,
                        replacements=replacements,
                        span_metadata={**span_metadata, "agent": str(agent)},
                    )
                    for agent in agents
                ),
                return_exceptions=True,
            )

        return self._record_agent_results(
            encounter_index, encounter, agents, agent_results, result_store
        )

    @staticmethod
    def _record_agent_results(
        encounter_index: int,
        encounter: Mapping[str, Any],
        agents: Sequence[AgentName],
        agent_results: Sequence[AgentOutput | BaseException],
        result_store: ResultStore,
    ) -> dict[str, Any]:
        """Store each agent's processed + raw output; collect failures for the roll-up."""
        succeeded: list[str] = []
        failed: dict[str, dict[str, str]] = {}
        validation: dict[str, dict[str, Any]] = {}

        for agent, outcome in zip(agents, agent_results):
            agent_name = str(agent)
            # BaseException (not just Exception): a cancelled task returns
            # CancelledError, which must be recorded as a failure, never stored
            # as a successful result.
            if isinstance(outcome, BaseException):
                failed[agent_name] = {
                    "error_type": type(outcome).__name__,
                    "message": str(outcome),
                }
                _persist_raw_on_failure(result_store, agent_name, encounter_index, outcome)
                logger.error(
                    "Agent failed for encounter",
                    extra={
                        "encounter_index": encounter_index,
                        "agent": agent_name,
                        "error_type": type(outcome).__name__,
                    },
                )
            else:
                processed = outcome.processed
                # The agent only sees its own single-encounter chunk, so it
                # cannot know its position in the document and always emits
                # encounter_index=1. Overwrite it with the real index, which the
                # pipeline knows (and already uses for the filename).
                processed["encounter_index"] = encounter_index
                result_store.store_encounter_agent(
                    agent_name, encounter_index, processed, raw=outcome.raw
                )
                succeeded.append(agent_name)
                validation[agent_name] = {
                    "schema_valid": outcome.validation.schema_valid,
                    "critical": outcome.validation.critical,
                    "missing_keys": outcome.validation.missing_keys,
                    "dangling_refs": outcome.validation.dangling_refs,
                }

        return {
            "encounter_index": encounter_index,
            "encounter_category": encounter.get("encounter_category"),
            "agents_run": [str(agent) for agent in agents],
            "succeeded": succeeded,
            "failed": failed,
            "validation": validation,
        }

    @staticmethod
    def _collect_encounter_summaries(
        encounters: Sequence[Mapping[str, Any]],
        outcomes: Sequence[Any],
    ) -> list[dict[str, Any]]:
        """Turn gather outcomes into roll-up entries, capturing encounter-level errors."""
        summaries: list[dict[str, Any]] = []
        for position, (encounter, outcome) in enumerate(zip(encounters, outcomes), start=1):
            if isinstance(outcome, BaseException):
                index = int(encounter.get("encounter_index") or position)
                logger.error(
                    "Encounter processing failed",
                    extra={"encounter_index": index, "error_type": type(outcome).__name__},
                )
                summaries.append(
                    {
                        "encounter_index": index,
                        "encounter_category": encounter.get("encounter_category"),
                        "agents_run": [],
                        "succeeded": [],
                        "failed": {
                            "__encounter__": {
                                "error_type": type(outcome).__name__,
                                "message": str(outcome),
                            }
                        },
                        "validation": {},
                    }
                )
            else:
                summaries.append(outcome)
        return summaries

    @staticmethod
    def _build_summary(
        *,
        transaction_id: str,
        anchors: AnchorSet,
        encounter_summaries: Sequence[dict[str, Any]],
        trace_reference: Mapping[str, str | None],
    ) -> dict[str, Any]:
        """Assemble the run manifest: metadata, anchors, roll-up, and failure totals."""
        agents_run = sum(len(entry["agents_run"]) for entry in encounter_summaries)
        agents_failed = sum(len(entry["failed"]) for entry in encounter_summaries)

        schema_issues = 0
        schema_critical = 0
        for entry in encounter_summaries:
            for agent_validation in entry.get("validation", {}).values():
                if not agent_validation.get("schema_valid", True):
                    schema_issues += 1
                if agent_validation.get("critical", False):
                    schema_critical += 1

        return {
            "transaction_id": transaction_id,
            "pipeline": "f2f",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "client_name": anchors.client_name,
            "trace": dict(trace_reference),
            "anchors": asdict(anchors),
            "encounter_count": len(encounter_summaries),
            "totals": {
                "agents_run": agents_run,
                "agents_failed": agents_failed,
                "agents_with_schema_issues": schema_issues,
                "agents_with_critical_validation": schema_critical,
            },
            "encounters": list(encounter_summaries),
        }
