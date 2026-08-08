"""``telehealth`` merge key.

``poc_485`` is null. Conditional agent: only encounters classified as
``telehealth_encounter`` ran, so other encounters carry null values (the base
builder supplies those automatically from the classification roster).
"""

from __future__ import annotations

from ...core.detection import AgentName
from .base import ReasoningOnlyBuilder


class TelehealthBuilder(ReasoningOnlyBuilder):
    """Builds the ``telehealth`` topic."""

    key = "telehealth"
    agent_name = AgentName.TELEHEALTH_IDENTITY
    include_status = True
