"""Agent identifiers and per-encounter agent selection.

``AgentName`` is the single source of truth for every agent name in the system.
Each value equals the skill folder name, which the factory also uses to derive
the prompt file and output path by convention.

The five base F2F agents run for every encounter. ``telehealth_identity`` and
``surgical_note`` are added only when the classification output indicates the
encounter is a telehealth or an operative/procedural note — so no manual flags
are needed.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any


class AgentName(StrEnum):
    """All agent identifiers. Each value matches its skill folder name."""

    CLASSIFICATION = "classification"
    POC_485_EXTRACTION = "poc_485_extraction"
    ENCOUNTER_IDENTITY = "encounter_identity"
    PRIMARY_DIAGNOSIS = "primary_diagnosis"
    SKILLED_SERVICES = "skilled_services"
    HOMEBOUND = "homebound"
    INPATIENT_DETECTION = "inpatient_detection"
    TELEHEALTH_IDENTITY = "telehealth_identity"
    SURGICAL_NOTE = "surgical_note"


# Classification signals that switch the conditional agents on.
CATEGORY_TELEHEALTH = "telehealth_encounter"
CATEGORY_OPERATIVE = "operative_procedural_notes"
TELEHEALTH_NOTE_FLAG = "TELEHEALTH"


class EncounterAgentSelector:
    """Decides which agents run for a given classified encounter."""

    _BASE_AGENTS: tuple[AgentName, ...] = (
        AgentName.ENCOUNTER_IDENTITY,
        AgentName.PRIMARY_DIAGNOSIS,
        AgentName.SKILLED_SERVICES,
        AgentName.HOMEBOUND,
        AgentName.INPATIENT_DETECTION,
    )

    def select(self, encounter: Mapping[str, Any]) -> list[AgentName]:
        """Return the agents to run for ``encounter``, in execution order."""
        agents = list(self._BASE_AGENTS)
        if self._is_telehealth(encounter):
            agents.append(AgentName.TELEHEALTH_IDENTITY)
        if self._is_surgical(encounter):
            agents.append(AgentName.SURGICAL_NOTE)
        return agents

    @staticmethod
    def _is_telehealth(encounter: Mapping[str, Any]) -> bool:
        category = encounter.get("encounter_category") or ""
        notes = encounter.get("classification_notes") or ""
        return category == CATEGORY_TELEHEALTH or TELEHEALTH_NOTE_FLAG in notes.upper()

    @staticmethod
    def _is_surgical(encounter: Mapping[str, Any]) -> bool:
        return (encounter.get("encounter_category") or "") == CATEGORY_OPERATIVE
