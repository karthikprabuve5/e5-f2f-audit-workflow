"""``inpatient`` merge key.

``poc_485`` is null (no 485 source). Per encounter, carries ``status``,
``confidence`` and ``reasoning`` from the inpatient-detection agent.
"""

from __future__ import annotations

from ...core.detection import AgentName
from .base import ReasoningOnlyBuilder


class InpatientBuilder(ReasoningOnlyBuilder):
    """Builds the ``inpatient`` topic."""

    key = "inpatient"
    agent_name = AgentName.INPATIENT_DETECTION
    include_status = True
