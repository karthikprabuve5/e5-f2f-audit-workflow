"""Regression tests: agent/encounter failures are recorded, never silent."""

from __future__ import annotations

import asyncio
from typing import Any

from f2f_orchestration.core.detection import AgentName
from f2f_orchestration.pipelines.f2f_pipeline import F2fPipeline


class _RecordingStore:
    """Captures store_encounter_agent calls so we can assert what was persisted."""

    def __init__(self) -> None:
        self.stored: dict[str, Any] = {}

    def store_encounter_agent(self, agent_name: str, encounter_index: int, data: Any) -> str:
        self.stored[agent_name] = data
        return agent_name


def test_exception_result_is_recorded_as_failed_not_stored() -> None:
    # Arrange
    store = _RecordingStore()
    agents = [AgentName.HOMEBOUND, AgentName.PRIMARY_DIAGNOSIS]
    results = [RuntimeError("boom"), {"ok": True}]

    # Act
    summary = F2fPipeline._record_agent_results(1, {"encounter_category": "x"}, agents, results, store)

    # Assert — failure captured, success stored; the exception is never persisted
    assert summary["failed"] == {"homebound": {"error_type": "RuntimeError", "message": "boom"}}
    assert summary["succeeded"] == ["primary_diagnosis"]
    assert "homebound" not in store.stored
    assert store.stored["primary_diagnosis"] == {"ok": True}


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
