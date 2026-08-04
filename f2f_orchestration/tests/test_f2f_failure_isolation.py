"""Regression tests: agent/encounter failures are recorded, never silent."""

from __future__ import annotations

import asyncio
from typing import Any

from f2f_orchestration.agents.agent_factory import AgentOutput
from f2f_orchestration.core.detection import AgentName
from f2f_orchestration.core.output_validator import ValidationResult
from f2f_orchestration.pipelines.f2f_pipeline import F2fPipeline


def _ok_output(agent: AgentName, processed: dict[str, Any]) -> AgentOutput:
    """A successful AgentOutput with a clean (valid) validation result."""
    return AgentOutput(
        agent=str(agent),
        raw=dict(processed),
        processed=dict(processed),
        validation=ValidationResult(agent=str(agent)),
    )


class _RecordingStore:
    """Captures store_encounter_agent calls so we can assert what was persisted."""

    def __init__(self) -> None:
        self.stored: dict[str, Any] = {}
        self.stored_raw: dict[str, Any] = {}
        self.raw_text: dict[str, str] = {}

    def store_encounter_agent(
        self, agent_name: str, encounter_index: int, data: Any, *, raw: Any = None
    ) -> str:
        self.stored[agent_name] = data
        self.stored_raw[agent_name] = raw
        return agent_name

    def store_raw_text(self, agent_name: str, encounter_index: int, raw_text: str) -> str:
        self.raw_text[agent_name] = raw_text
        return agent_name


def test_exception_result_is_recorded_as_failed_not_stored() -> None:
    # Arrange
    store = _RecordingStore()
    agents = [AgentName.HOMEBOUND, AgentName.PRIMARY_DIAGNOSIS]
    results = [RuntimeError("boom"), _ok_output(AgentName.PRIMARY_DIAGNOSIS, {"ok": True})]

    # Act
    summary = F2fPipeline._record_agent_results(1, {"encounter_category": "x"}, agents, results, store)

    # Assert — failure captured, success stored; the exception is never persisted
    assert summary["failed"] == {"homebound": {"error_type": "RuntimeError", "message": "boom"}}
    assert summary["succeeded"] == ["primary-diagnosis"]
    assert "homebound" not in store.stored
    assert store.stored["primary-diagnosis"] == {"ok": True, "encounter_index": 1}
    # Processed and raw are both persisted for traceability
    assert store.stored_raw["primary-diagnosis"] == {"ok": True}
    assert summary["validation"]["primary-diagnosis"]["schema_valid"] is True


def test_unparseable_agent_output_persists_raw_text_and_is_failed() -> None:
    # Arrange — an AgentOutputError carrying the raw (non-JSON) content
    from f2f_orchestration.agents.agent_factory import AgentOutputError

    store = _RecordingStore()
    agents = [AgentName.HOMEBOUND]
    results = [AgentOutputError("not json", raw_content="<<garbled>>")]

    # Act
    summary = F2fPipeline._record_agent_results(3, {"encounter_category": "x"}, agents, results, store)

    # Assert — failed, no processed result, but the raw string is captured
    assert "homebound" in summary["failed"]
    assert summary["succeeded"] == []
    assert "homebound" not in store.stored
    assert store.raw_text["homebound"] == "<<garbled>>"


def test_cancelled_error_is_treated_as_failure_not_success() -> None:
    # Arrange — CancelledError is a BaseException, not an Exception
    store = _RecordingStore()
    agents = [AgentName.HOMEBOUND]
    results = [asyncio.CancelledError()]

    # Act
    summary = F2fPipeline._record_agent_results(1, {"encounter_category": "x"}, agents, results, store)

    # Assert — recorded as failed, and NOT stored as a successful result
    assert "homebound" in summary["failed"]
    assert summary["succeeded"] == []
    assert store.stored == {}


def test_encounter_level_exception_becomes_a_failure_rollup_entry() -> None:
    # Arrange
    encounters = [{"encounter_index": 7, "encounter_category": "skilled_nursing_visit"}]
    outcomes = [ValueError("bad encounter")]

    # Act
    summaries = F2fPipeline._collect_encounter_summaries(encounters, outcomes)

    # Assert
    assert summaries[0]["encounter_index"] == 7
    assert "__encounter__" in summaries[0]["failed"]
    assert summaries[0]["agents_run"] == []
