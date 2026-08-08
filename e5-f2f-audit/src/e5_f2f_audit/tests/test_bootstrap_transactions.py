"""Unit tests for transaction discovery / resolution in bootstrap."""

from __future__ import annotations

from pathlib import Path

import pytest

from e5_f2f_audit import bootstrap
from e5_f2f_audit.core.document_source import DocumentKind


@pytest.fixture
def ocr_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    ocr = tmp_path / "ocr-markdown"
    (ocr / "txn_a").mkdir(parents=True)
    (ocr / "txn_b").mkdir(parents=True)
    (ocr / "txn_f2f_only").mkdir(parents=True)
    (ocr / "txn_a" / "POC.md").write_text("a", encoding="utf-8")
    (ocr / "txn_a" / "F2F.md").write_text("a", encoding="utf-8")
    (ocr / "txn_b" / "POC.md").write_text("b", encoding="utf-8")
    (ocr / "txn_f2f_only" / "F2F.md").write_text("c", encoding="utf-8")
    monkeypatch.setenv("OCR_MARKDOWN_DIR", str(ocr))
    return ocr


def test_list_transactions_is_doc_aware_and_sorted(ocr_dir: Path) -> None:
    assert bootstrap.list_transactions(DocumentKind.POC) == ["txn_a", "txn_b"]
    assert bootstrap.list_transactions(DocumentKind.F2F) == ["txn_a", "txn_f2f_only"]


def test_list_transactions_missing_dir_returns_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OCR_MARKDOWN_DIR", str(tmp_path / "does-not-exist"))
    assert bootstrap.list_transactions(DocumentKind.POC) == []


def test_resolve_full_mode_lists_all_matching(ocr_dir: Path) -> None:
    resolved = bootstrap.resolve_transactions(DocumentKind.POC, bootstrap.RunMode.FULL, [])
    assert resolved == ["txn_a", "txn_b"]


def test_resolve_selected_mode_returns_given_list(ocr_dir: Path) -> None:
    resolved = bootstrap.resolve_transactions(
        DocumentKind.POC, bootstrap.RunMode.SELECTED, ["only_this", "and_this"]
    )
    assert resolved == ["only_this", "and_this"]
