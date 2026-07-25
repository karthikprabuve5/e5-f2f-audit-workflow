"""Unit tests for PromptRenderer (load + placeholder injection)."""

from __future__ import annotations

from pathlib import Path

import pytest

from f2f_orchestration.core.prompts import PromptRenderer


def test_render_replaces_all_placeholders(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "sample_system_prompt.md").write_text(
        "Client <CLIENT_NAME> code <POC_ICD10_CODE>.", encoding="utf-8"
    )
    renderer = PromptRenderer(tmp_path)

    # Act
    rendered = renderer.render(
        "sample_system_prompt.md",
        {"<CLIENT_NAME>": "CLIENT_A", "<POC_ICD10_CODE>": "I50.9"},
    )

    # Assert
    assert rendered == "Client CLIENT_A code I50.9."


def test_render_without_replacements_returns_raw_text(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "p.md").write_text("no placeholders here", encoding="utf-8")
    renderer = PromptRenderer(tmp_path)

    # Act / Assert
    assert renderer.render("p.md") == "no placeholders here"


def test_missing_prompt_raises_actionable_error(tmp_path: Path) -> None:
    # Arrange
    renderer = PromptRenderer(tmp_path)

    # Act / Assert
    with pytest.raises(FileNotFoundError, match="missing.md"):
        renderer.render("missing.md")
