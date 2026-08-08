"""Encounter-selection pipeline — picks the best F2F encounter for the claim.

This is the framework-agnostic core: it takes the consolidated ``merge_encounters``
as an in-memory dict plus the runtime ``soc_date`` and ``client_name``, runs the
single transaction-level ``encounter-selection`` agent under one Langfuse trace,
and returns its :class:`AgentOutput` (raw + processed + validation). It performs
no disk I/O, so a local batch entrypoint and an external orchestrator (Temporal)
call the exact same method — the caller decides where the result is persisted.

It reuses :class:`BasePipeline` for the production-grade retry/throttling and
tracing machinery, so selection is protected against Bedrock throttling like
every other agent call.

``soc_date`` is a required runtime input; a blank/absent value is a caller
contract violation and fails fast with a ``ValueError`` rather than running the
agent with no timing window.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from ..agents.agent_factory import AgentOutput
from ..core.detection import AgentName
from ..core.logging_setup import get_logger
from .base_pipeline import BasePipeline

logger = get_logger(__name__)

CLIENT_NAME_PLACEHOLDER = "<CLIENT_NAME>"
SOC_DATE_PLACEHOLDER = "<SOC_DATE>"


class SelectionPipeline(BasePipeline):
    """Runs the transaction-level encounter-selection agent over merge_encounters."""

    async def run(
        self,
        *,
        transaction_id: str,
        merge_encounters: Mapping[str, Any],
        soc_date: str,
        client_name: str,
        excluded_encounters: Sequence[Mapping[str, Any]] | None = None,
    ) -> AgentOutput:
        """Select the best encounter for one transaction and return its output.

        ``merge_encounters`` is the consolidated, already-validated merge contract
        (the same shape ``MergeEncountersEngine.build`` produces), already narrowed
        to the selection candidate set by :func:`encounter_filter.filter_candidates`.
        It is serialized to JSON and handed to the agent as its
        ``MERGE_ENCOUNTERS.json`` input document.

        ``excluded_encounters`` is the deterministic list of supporting-only
        encounters (e.g. ``referral_documents``) that the filter removed from the
        candidate set. It never reaches the agent; it is recorded verbatim in the
        returned ``processed`` result so the output states exactly which indices
        were excluded and why.
        """
        if not soc_date or not str(soc_date).strip():
            raise ValueError(
                f"soc_date is required for encounter selection "
                f"(transaction '{transaction_id}'); received {soc_date!r}."
            )
        if not client_name or not str(client_name).strip():
            raise ValueError(
                f"client_name is required for encounter selection "
                f"(transaction '{transaction_id}'); received {client_name!r}."
            )

        logger.info(
            "Starting selection pipeline",
            extra={"transaction_id": transaction_id, "soc_date": soc_date},
        )
        document_content = json.dumps(merge_encounters, ensure_ascii=False, default=str)
        replacements = {
            CLIENT_NAME_PLACEHOLDER: client_name,
            SOC_DATE_PLACEHOLDER: soc_date,
        }
        span_metadata = {"transaction_id": transaction_id, "soc_date": soc_date}

        with self._tracer.pipeline_trace("selection", transaction_id):
            output = await self._run_agent(
                AgentName.ENCOUNTER_SELECTION,
                document_content=document_content,
                replacements=replacements,
                span_metadata=span_metadata,
            )

        self._embed_exclusions(output.processed, excluded_encounters, transaction_id)

        selection = output.processed.get("result", {}) if isinstance(output.processed, dict) else {}
        logger.info(
            "Selection pipeline finished",
            extra={
                "transaction_id": transaction_id,
                "best_encounter_index": selection.get("best_encounter_index"),
                "decision": selection.get("decision"),
                "excluded_encounter_indices": selection.get("excluded_encounter_indices", []),
            },
        )
        return output

    @staticmethod
    def _embed_exclusions(
        processed: Any,
        excluded_encounters: Sequence[Mapping[str, Any]] | None,
        transaction_id: str,
    ) -> None:
        """Record the excluded referral encounters in the agent's ``result`` block.

        This is orchestration metadata added after validation, so it never affects
        the agent's schema check. It also enforces the compliance invariant: an
        excluded (supporting-only) index can never be the selected best encounter;
        a violation is a defect and fails loudly rather than silently selecting a
        referral document.
        """
        excluded = [dict(entry) for entry in (excluded_encounters or [])]
        excluded_indices = [
            entry["encounter_index"] for entry in excluded if "encounter_index" in entry
        ]
        if not isinstance(processed, dict):
            return
        result = processed.setdefault("result", {})
        if not isinstance(result, dict):
            return
        result["excluded_encounters"] = excluded
        result["excluded_encounter_indices"] = excluded_indices

        best_index = result.get("best_encounter_index")
        if best_index is not None and best_index in excluded_indices:
            raise ValueError(
                f"Encounter selection returned excluded referral index "
                f"{best_index} as the best encounter for transaction "
                f"'{transaction_id}'. Excluded indices: {excluded_indices}."
            )
