"""Unit tests for the merge-encounters engine (pure ``merge_encounters`` assembly).

These exercise the framework-agnostic path (``TransactionOutputs.from_mapping``) so
the engine is tested with no disk, no clock, and no environment — the same core a
Temporal activity would call. Coverage:

* Envelope shape, injected ``generated_at``, and determinism.
* Topic set/order matches the builder registry; every topic carries the roster.
* Encounter alignment across topics (one entry per classified encounter, in order).
* Evidence references resolve to inline evidence objects.
* Conditional agents (telehealth/surgical) yield present vs. null per encounter.
* ``data_quality.failed_agents`` flags an *expected* agent that produced no output.
"""

from __future__ import annotations

from typing import Any

import pytest

from f2f_orchestration.core.detection import AgentName
from f2f_orchestration.merge_encounters import MergeEncountersEngine, TransactionOutputs
from f2f_orchestration.merge_encounters.key_builders import BUILDERS

_GENERATED_AT = "2026-07-30T00:00:00+00:00"


def _agent_output(**overrides: Any) -> dict[str, Any]:
    """A minimal agent-output envelope; overrides merge onto the defaults."""
    base: dict[str, Any] = {
        "status": "COMPLETE",
        "confidence": "high",
        "result": {},
        "evidence": [],
        "reasoning": {"summary": None, "missing": None, "evidence_refs": []},
    }
    base.update(overrides)
    return base


def _payload() -> dict[str, Any]:
    """Two encounters: #1 telehealth (full roster), #2 skilled (homebound missing)."""
    inpatient_e1 = _agent_output(
        evidence=[
            {
                "evidence_id": "E1",
                "verbiage": "no inpatient stay documented",
                "page": 3,
                "line_start": 10,
                "line_end": 11,
                "signal_strength": "strong",
            }
        ],
        reasoning={"summary": "No admission found.", "missing": None, "evidence_refs": ["E1"]},
    )

    base_agents = {
        AgentName.ENCOUNTER_IDENTITY.value: {1: _agent_output(), 2: _agent_output()},
        AgentName.PRIMARY_DIAGNOSIS.value: {1: _agent_output(), 2: _agent_output()},
        AgentName.SKILLED_SERVICES.value: {1: _agent_output(), 2: _agent_output()},
        # homebound present only for encounter 1 -> encounter 2 is an expected gap.
        AgentName.HOMEBOUND.value: {1: _agent_output()},
        AgentName.INPATIENT_DETECTION.value: {1: inpatient_e1, 2: _agent_output()},
        # telehealth ran only for the telehealth encounter (#1).
        AgentName.TELEHEALTH_IDENTITY.value: {1: _agent_output()},
    }

    return {
        "transaction_id": "txn_test",
        "poc_extraction": None,
        "classification_f2f": {
            "client_id": "CLIENT_A",
            "encounters": [
                {"encounter_index": 1, "encounter_category": "telehealth_encounter"},
                {"encounter_index": 2, "encounter_category": "skilled_nursing_visit"},
            ],
        },
        "agents": base_agents,
    }


@pytest.fixture
def audit() -> dict[str, Any]:
    outputs = TransactionOutputs.from_mapping(_payload())
    return MergeEncountersEngine().build(outputs, generated_at=_GENERATED_AT)


def test_envelope_carries_injected_metadata(audit: dict[str, Any]) -> None:
    assert audit["parameter_id"] == "merge_encounters"
    assert audit["schema_version"] == "1.0"
    assert audit["transaction_id"] == "txn_test"
    assert audit["client_id"] == "CLIENT_A"
    assert audit["generated_at"] == _GENERATED_AT


def test_build_is_deterministic() -> None:
    outputs = TransactionOutputs.from_mapping(_payload())
    first = MergeEncountersEngine().build(outputs, generated_at=_GENERATED_AT)
    second = MergeEncountersEngine().build(outputs, generated_at=_GENERATED_AT)
    assert first == second


def test_topics_match_builder_registry_in_order(audit: dict[str, Any]) -> None:
    expected = [builder.key for builder in BUILDERS]
    assert list(audit["results"].keys()) == expected


def test_every_topic_carries_full_encounter_roster(audit: dict[str, Any]) -> None:
    for key, section in audit["results"].items():
        assert "poc_485" in section, key
        indices = [entry["encounter_index"] for entry in section["f2f_encounters"]]
        assert indices == [1, 2], f"topic {key} lost encounter alignment"


def test_evidence_refs_resolve_inline(audit: dict[str, Any]) -> None:
    inpatient_e1 = audit["results"]["inpatient"]["f2f_encounters"][0]
    evidence = inpatient_e1["reasoning"]["evidence"]
    assert evidence == [
        {
            "verbiage": "no inpatient stay documented",
            "page": 3,
            "line_start": 10,
            "line_end": 11,
            "signal_strength": "strong",
        }
    ]


def test_conditional_agent_present_and_null_per_encounter(audit: dict[str, Any]) -> None:
    telehealth = audit["results"]["telehealth"]["f2f_encounters"]
    assert telehealth[0]["status"] == "COMPLETE"  # encounter 1 ran
    assert telehealth[1]["status"] is None  # encounter 2 never ran
    assert telehealth[1]["reasoning"]["evidence"] == []

    surgical = audit["results"]["surgical_note"]["f2f_encounters"]
    assert all(entry["status"] is None for entry in surgical)  # neither is operative


def test_data_quality_flags_expected_but_missing_agent(audit: dict[str, Any]) -> None:
    failed = audit["data_quality"]["failed_agents"]
    assert failed == {AgentName.HOMEBOUND.value: [2]}
    assert audit["data_quality"]["schema_issues"] == []
