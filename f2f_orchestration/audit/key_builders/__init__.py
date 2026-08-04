"""Audit key builders: one small class per audit topic.

``BUILDERS`` fixes the order of topics under ``results`` and is what
:class:`AuditEngine` iterates.
"""

from .base import (
    AuditKeyBuilder,
    ReasoningOnlyBuilder,
    build_f2f_encounters,
    dget,
    null_reasoning,
    reasoning_block,
)
from .eligible_practitioners import EligiblePractitionersBuilder
from .homebound import HomeboundBuilder
from .inpatient import InpatientBuilder
from .primary_hh_reason import PrimaryHhReasonBuilder
from .skilled_services import SkilledServicesBuilder
from .surgical_note import SurgicalNoteBuilder
from .telehealth import TelehealthBuilder
from .timely_encounter import TimelyEncounterBuilder

# Order here is the order of topics under ``results`` in audit-results.json.
BUILDERS: tuple[AuditKeyBuilder, ...] = (
    TimelyEncounterBuilder(),
    EligiblePractitionersBuilder(),
    PrimaryHhReasonBuilder(),
    HomeboundBuilder(),
    SkilledServicesBuilder(),
    InpatientBuilder(),
    TelehealthBuilder(),
    SurgicalNoteBuilder(),
)

__all__ = [
    "AuditKeyBuilder",
    "ReasoningOnlyBuilder",
    "build_f2f_encounters",
    "dget",
    "null_reasoning",
    "reasoning_block",
    "BUILDERS",
    "TimelyEncounterBuilder",
    "EligiblePractitionersBuilder",
    "PrimaryHhReasonBuilder",
    "HomeboundBuilder",
    "SkilledServicesBuilder",
    "InpatientBuilder",
    "TelehealthBuilder",
    "SurgicalNoteBuilder",
]
