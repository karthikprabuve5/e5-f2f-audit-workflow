"""End-to-end smoke test for the library reuse path: POC -> F2F -> merge.

Drives the *real* ``PocPipeline`` and ``F2fPipeline`` (with their real splitter,
normalizer, selector, and ``ResultStore``) but stubs the agent factory and tracer
so no Bedrock / network / Langfuse is touched. It proves the whole orchestration
chain an external package would use:

    PocPipeline.run -> AnchorSet + poc_store.results
    F2fPipeline.run -> f2f_store.results
    build_merge_encounters_payload(...) -> TransactionOutputs.from_mapping -> MergeEncountersEngine.build

This is a wiring/contract test, not a model-quality test.
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any

from f2f_orchestration.agents.agent_factory import AgentOutput
from f2f_orchestration.merge_encounters import (
    MergeEncountersEngine,
    TransactionOutputs,
    build_merge_encounters_payload,
)
from f2f_orchestration.merge_encounters.key_builders import BUILDERS
from f2f_orchestration.core.detection import AgentName
from f2f_orchestration.core.output_validator import ValidationResult
from f2f_orchestration.core.result_store import ResultStore
from f2f_orchestration.pipelines.f2f_pipeline import F2fPipeline
from f2f_orchestration.pipelines.poc_pipeline import PocPipeline

_CLIENT = "CLIENT_A"
_TXN = "transaction_smoke"
_GENERATED_AT = "2026-07-30T00:00:00+00:00"

_F2F_DOCUMENT = "### Page 1\nHistory and physical. Patient is homebound.\n"

_BASE_AGENTS = (
    AgentName.ENCOUNTER_IDENTITY,
    AgentName.PRIMARY_DIAGNOSIS,
    AgentName.SKILLED_SERVICES,
    AgentName.HOMEBOUND,
    AgentName.INPATIENT_DETECTION,
)


def _agent_envelope() -> dict[str, Any]:
    """The minimal agent-output envelope the merge key builders accept."""
    return {
        "status": "COMPLETE",
        "confidence": "high",
        "client_id": _CLIENT,
        "result": {},
        "evidence": [],
        "reasoning": {"summary": None, "missing": None, "evidence_refs": []},
    }


class _NoopTracer:
    """A tracer that satisfies the pipeline interface without emitting spans."""

    @contextlib.contextmanager
    def pipeline_trace(self, name: str, transaction_id: str):
        yield None

    @contextlib.contextmanager
    def agent_span(self, name: str, metadata: dict[str, Any] | None = None):
        yield None

    @contextlib.contextmanager
    def encounter_span(self, index: int, metadata: dict[str, Any] | None = None):
        yield None

    def callback_config(self, run_name: str | None = None, metadata: dict[str, Any] | None = None):
        return {}

    def current_trace_reference(self):
        return {}

    def flush(self) -> None:
        pass


class _StubAgentFactory:
    """Returns canned ``AgentOutput`` per agent — no model calls."""

    def __init__(self, outputs: dict[AgentName, dict[str, Any]]) -> None:
        self._outputs = outputs

    async def run(
        self,
        agent_name: AgentName,
        *,
        document_content: str,
        replacements: Any = None,
        config: Any = None,
    ) -> AgentOutput:
        processed = dict(self._outputs[agent_name])
        return AgentOutput(
            agent=str(agent_name),
            raw=dict(processed),
            processed=processed,
            validation=ValidationResult(agent=str(agent_name)),
        )


def _pipeline(cls, factory: _StubAgentFactory):
    return cls(
        agent_factory=factory,
        tracer=_NoopTracer(),
        max_concurrent_agents=5,
        launch_stagger_seconds=0.0,
        max_retries=0,
        retry_base_delay_seconds=0.0,
        retry_max_delay_seconds=0.0,
    )


def _poc_factory() -> _StubAgentFactory:
    return _StubAgentFactory(
        {
            AgentName.CLASSIFICATION: {
                "client_id": _CLIENT,
                "encounters": [
                    {
                        "encounter_index": 1,
                        "encounter_category": "poc_485",
                        "encounter_subcategory": "2.1",
                        "page_start": 1,
                        "page_end": 1,
                    }
                ],
            },
            AgentName.POC_485_EXTRACTION: {
                "client_id": _CLIENT,
                "result": {
                    "primary_diagnosis": {"icd10_code": "I50.9", "description": "Heart failure"},
                    "skilled_services": {"ordered_services": ["skilled nursing"]},
                },
            },
        }
    )


def _f2f_factory() -> _StubAgentFactory:
    outputs: dict[AgentName, dict[str, Any]] = {
        AgentName.CLASSIFICATION: {
            "client_id": _CLIENT,
            "encounters": [
                {
                    "encounter_index": 1,
                    "encounter_category": "clinical_encounter_notes",
                    "encounter_subcategory": "6.1",
                    "page_start": 1,
                    "page_end": 1,
                    "line_start": None,
                    "line_end": None,
                }
            ],
        },
    }
    for agent in _BASE_AGENTS:
        outputs[agent] = _agent_envelope()
    return _StubAgentFactory(outputs)


async def _orchestrate() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    poc_pipeline = _pipeline(PocPipeline, _poc_factory())
    f2f_pipeline = _pipeline(F2fPipeline, _f2f_factory())

    poc_store = ResultStore(Path("."), _TXN, persist_to_disk=False)
    anchors = await poc_pipeline.run(
        transaction_id=_TXN,
        poc_document_content="poc content",
        client_name=_CLIENT,
        result_store=poc_store,
    )

    f2f_store = ResultStore(Path("."), _TXN, persist_to_disk=False)
    await f2f_pipeline.run(
        transaction_id=_TXN,
        f2f_document_content=_F2F_DOCUMENT,
        anchors=anchors,
        result_store=f2f_store,
    )

    payload = build_merge_encounters_payload(
        poc_store.results, f2f_store.results, transaction_id=_TXN, client_id=_CLIENT
    )
    merged = MergeEncountersEngine().build(
        TransactionOutputs.from_mapping(payload), generated_at=_GENERATED_AT
    )
    return poc_store.results, f2f_store.results, merged


def test_end_to_end_poc_f2f_merge_chain() -> None:
    # Act
    poc_results, f2f_results, merged = asyncio.run(_orchestrate())

    # Assert — POC produced anchors + extraction, captured in memory
    assert poc_results["poc_485_extraction"]["result"]["primary_diagnosis"]["icd10_code"] == "I50.9"

    # Assert — F2F ran all five base agents for encounter 1, no soft failures
    encounter_1 = f2f_results["encounters"][1]
    assert set(encounter_1) == {agent.value for agent in _BASE_AGENTS}
    assert f2f_results["errors"] == []
    # raw captured in memory alongside processed
    assert set(f2f_results["raw"]["encounters"][1]) == {agent.value for agent in _BASE_AGENTS}

    # Assert — merge envelope is well-formed and complete
    assert merged["parameter_id"] == "merge_encounters"
    assert merged["transaction_id"] == _TXN
    assert merged["client_id"] == _CLIENT
    assert merged["generated_at"] == _GENERATED_AT
    assert list(merged["results"].keys()) == [builder.key for builder in BUILDERS]
    # every expected agent ran, so no gaps flagged
    assert merged["data_quality"]["failed_agents"] == {}


def test_build_merge_encounters_payload_transposes_and_maps_keys() -> None:
    # Arrange — shapes as the two stores would produce
    poc_results = {"transaction_id": _TXN, "poc_485_extraction": {"result": {}}}
    f2f_results = {
        "transaction_id": _TXN,
        "classification": {"f2f": {"encounters": []}},
        "encounters": {1: {"homebound": {"status": "COMPLETE"}}},
    }

    # Act
    payload = build_merge_encounters_payload(poc_results, f2f_results, client_id=_CLIENT)

    # Assert — keys renamed and encounters transposed to {agent: {index: data}}
    assert payload["poc_extraction"] == {"result": {}}
    assert payload["classification_f2f"] == {"encounters": []}
    assert payload["agents"] == {"homebound": {1: {"status": "COMPLETE"}}}
    assert payload["client_id"] == _CLIENT
    assert payload["transaction_id"] == _TXN
