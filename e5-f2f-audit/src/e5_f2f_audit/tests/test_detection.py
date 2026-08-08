"""Unit tests for EncounterAgentSelector (conditional agent selection)."""

from __future__ import annotations

from e5_f2f_audit.core.detection import AgentName, EncounterAgentSelector

_BASE_AGENTS = [
    AgentName.ENCOUNTER_IDENTITY,
    AgentName.PRIMARY_DIAGNOSIS,
    AgentName.SKILLED_SERVICES,
    AgentName.HOMEBOUND,
    AgentName.INPATIENT_DETECTION,
]


def test_generic_encounter_runs_only_the_base_agents() -> None:
    # Act
    agents = EncounterAgentSelector().select({"encounter_category": "skilled_nursing_visit"})

    # Assert
    assert agents == _BASE_AGENTS


def test_telehealth_category_adds_telehealth_identity() -> None:
    # Act
    agents = EncounterAgentSelector().select({"encounter_category": "telehealth_encounter"})

    # Assert
    assert agents == [*_BASE_AGENTS, AgentName.TELEHEALTH_IDENTITY]


def test_telehealth_note_flag_adds_telehealth_identity() -> None:
    # Act — flag lives in the classification notes, case-insensitive
    agents = EncounterAgentSelector().select(
        {"encounter_category": "skilled_nursing_visit", "classification_notes": "flagged telehealth"}
    )

    # Assert
    assert AgentName.TELEHEALTH_IDENTITY in agents


def test_operative_category_adds_surgical_note() -> None:
    # Act
    agents = EncounterAgentSelector().select({"encounter_category": "operative_procedural_notes"})

    # Assert
    assert agents == [*_BASE_AGENTS, AgentName.SURGICAL_NOTE]
