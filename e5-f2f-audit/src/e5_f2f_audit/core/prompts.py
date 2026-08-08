"""System prompt loading and placeholder injection.

``PromptRenderer`` reads a system prompt from the ``prompts/`` directory and
substitutes anchor placeholders (e.g. ``<CLIENT_NAME>``, ``<POC_ICD10_CODE>``)
with their resolved values.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


class PromptRenderer:
    """Loads system prompts from disk and injects placeholder values."""

    def __init__(self, prompts_dir: Path) -> None:
        self._prompts_dir = prompts_dir

    def load(self, filename: str) -> str:
        """Return the raw prompt text for ``filename``."""
        prompt_path = self._prompts_dir / filename
        try:
            return prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"System prompt '{filename}' not found in {self._prompts_dir}."
            ) from exc

    def render(self, filename: str, replacements: Mapping[str, str] | None = None) -> str:
        """Return the prompt with each placeholder replaced by its value."""
        prompt = self.load(filename)
        for placeholder, value in (replacements or {}).items():
            prompt = prompt.replace(placeholder, value)
        return prompt
