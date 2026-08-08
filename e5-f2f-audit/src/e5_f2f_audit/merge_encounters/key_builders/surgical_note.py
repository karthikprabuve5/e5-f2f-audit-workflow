"""``surgical_note`` merge key.

``poc_485`` is null. Conditional agent: only encounters classified as
``operative_procedural_notes`` ran, so other encounters carry null values (the base
builder supplies those automatically from the classification roster).
"""

from __future__ import annotations

from ...core.detection import AgentName
from .base import ReasoningOnlyBuilder


class SurgicalNoteBuilder(ReasoningOnlyBuilder):
    """Builds the ``surgical_note`` topic."""

    key = "surgical_note"
    agent_name = AgentName.SURGICAL_NOTE
    include_status = True
