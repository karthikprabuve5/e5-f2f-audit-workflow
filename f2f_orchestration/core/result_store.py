"""In-memory results plus JSON persistence for one transaction.

``ResultStore`` accumulates every agent's output in an in-memory dict (always
returned to the caller) and, when ``persist_to_disk`` is enabled, mirrors each
result to disk under::

    outputs/<transaction_id>/
      classification/{f2f.json, poc.json}
      poc_485_extraction-results.json
      <agent_name>/encounter_<i>-results.json
      _summary-results.json

Disk persistence is toggleable so production can rely on the returned dict (or a
different sink) instead of the local filesystem.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .logging_setup import get_logger

logger = get_logger(__name__)

POC_EXTRACTION_FILENAME = "poc_485_extraction-results.json"
SUMMARY_FILENAME = "_summary-results.json"
CLASSIFICATION_DIRNAME = "classification"


class ResultStore:
    """Collects results in memory and optionally writes them to disk."""

    def __init__(self, outputs_dir: Path, transaction_id: str, *, persist_to_disk: bool = True) -> None:
        self._transaction_dir = outputs_dir / transaction_id
        self._persist_to_disk = persist_to_disk
        self._results: dict[str, Any] = {
            "transaction_id": transaction_id,
            "classification": {},
            "poc_485_extraction": None,
            "encounters": {},
            "summary": None,
        }

    @property
    def results(self) -> dict[str, Any]:
        """The full in-memory results dict for this transaction."""
        return self._results

    def store_classification(self, document_kind: str, data: dict[str, Any]) -> str:
        """Store a classification result for ``f2f`` or ``poc``."""
        if document_kind not in ("f2f", "poc"):
            raise ValueError(f"document_kind must be 'f2f' or 'poc', got '{document_kind}'.")

        self._results["classification"][document_kind] = data
        return self._write(Path(CLASSIFICATION_DIRNAME) / f"{document_kind}.json", data)

    def store_poc_extraction(self, data: dict[str, Any]) -> str:
        """Store the POC/485 anchor extraction result."""
        self._results["poc_485_extraction"] = data
        return self._write(Path(POC_EXTRACTION_FILENAME), data)

    def store_encounter_agent(self, agent_name: str, encounter_index: int, data: dict[str, Any]) -> str:
        """Store one agent's result for one encounter."""
        encounter = self._results["encounters"].setdefault(encounter_index, {})
        encounter[agent_name] = data
        return self._write(Path(agent_name) / f"encounter_{encounter_index}-results.json", data)

    def store_summary(self, data: dict[str, Any]) -> str:
        """Store the consolidated run summary/manifest."""
        self._results["summary"] = data
        return self._write(Path(SUMMARY_FILENAME), data)

    def _write(self, relative_path: Path, data: dict[str, Any]) -> str:
        """Write ``data`` as JSON (when persisting) and return the relative path."""
        relative_str = relative_path.as_posix()
        if not self._persist_to_disk:
            return relative_str

        absolute_path = self._transaction_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        with absolute_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False, default=str)

        logger.info("Wrote result", extra={"path": relative_str})
        return relative_str
