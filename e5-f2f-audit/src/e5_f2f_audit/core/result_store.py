"""In-memory results plus JSON persistence for one transaction.

``ResultStore`` accumulates every agent's normalized output in an in-memory dict
(always returned to the caller) and, when ``persist_to_disk`` is enabled, mirrors
each result to disk under::

    outputs/<transaction_id>/
      classification/{f2f.json, f2f-raw.json, poc.json, poc-raw.json}
      poc_485_extraction/{results.json, results-raw.json}
      <agent_name>/encounter_<i>-results.json, encounter_<i>-raw.json
      _summary-results.json
      merge-encounters/results.json
      encounter-selection/{results.json, results-raw.json}

For every agent result the store writes two files: the canonical ``processed``
output (normalized + validated) and a sibling ``-raw.json`` holding the exact
agent output before normalization. The raw file is the audit trail; the processed
file is what downstream consumes. Disk persistence is toggleable so production can
rely on the returned dict (or a different sink) instead of the local filesystem.

Alongside the processed tree, the in-memory results also carry:

* ``raw``    — the pre-normalization agent output, mirroring the processed layout
  (``classification``/``poc_485_extraction``/``encounters``). This lets an
  in-process caller capture raw for its own sink (e.g. S3) without touching disk.
* ``errors`` — normalized records of the *soft* failures the F2F pipeline isolates
  (per-agent and per-encounter), derived from the run summary. Hard failures (a
  raised exception) never reach the store; the caller catches those directly.

Both keys are additive: existing consumers and the merge engine ignore them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .logging_setup import get_logger

logger = get_logger(__name__)

POC_EXTRACTION_DIRNAME = "poc_485_extraction"
POC_EXTRACTION_FILENAME = "results.json"
# Skip-marker used by run_poc: outputs/<txn>/poc_485_extraction/results.json
POC_EXTRACTION_RESULT_MARKER = f"{POC_EXTRACTION_DIRNAME}/{POC_EXTRACTION_FILENAME}"
SUMMARY_FILENAME = "_summary-results.json"
MERGE_ENCOUNTERS_DIRNAME = "merge-encounters"
MERGE_ENCOUNTERS_FILENAME = "results.json"
# Skip-marker used by run_merge_encounters / run_selection:
# outputs/<txn>/merge-encounters/results.json
MERGE_ENCOUNTERS_MARKER = f"{MERGE_ENCOUNTERS_DIRNAME}/{MERGE_ENCOUNTERS_FILENAME}"
CLASSIFICATION_DIRNAME = "classification"
CLASSIFICATION_F2F_FILENAME = "f2f.json"
SELECTION_DIRNAME = "encounter-selection"
SELECTION_FILENAME = "results.json"
# Skip-marker used by the selection entrypoint: outputs/<txn>/encounter-selection/results.json
SELECTION_RESULT_MARKER = f"{SELECTION_DIRNAME}/{SELECTION_FILENAME}"
AUDIT_DIRNAME = "audit"
AUDIT_FILENAME = "results.json"
# Skip-marker used by run_audit: outputs/<txn>/audit/results.json
AUDIT_MARKER = f"{AUDIT_DIRNAME}/{AUDIT_FILENAME}"


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
            "merge_encounters": None,
            "selection": None,
            "audit": None,
            "raw": {
                "classification": {},
                "poc_485_extraction": None,
                "encounters": {},
                "selection": None,
            },
            "errors": [],
        }

    @property
    def results(self) -> dict[str, Any]:
        """The full in-memory results dict for this transaction."""
        return self._results

    def store_classification(
        self, document_kind: str, data: dict[str, Any], *, raw: dict[str, Any] | None = None
    ) -> str:
        """Store a classification result for ``f2f`` or ``poc`` (processed + raw)."""
        if document_kind not in ("f2f", "poc"):
            raise ValueError(f"document_kind must be 'f2f' or 'poc', got '{document_kind}'.")

        self._results["classification"][document_kind] = data
        if raw is not None:
            self._results["raw"]["classification"][document_kind] = raw
        path = Path(CLASSIFICATION_DIRNAME) / f"{document_kind}.json"
        self._write_raw(path, raw)
        return self._write(path, data)

    def store_poc_extraction(
        self, data: dict[str, Any], *, raw: dict[str, Any] | None = None
    ) -> str:
        """Store the POC/485 anchor extraction result (processed + raw)."""
        self._results["poc_485_extraction"] = data
        if raw is not None:
            self._results["raw"]["poc_485_extraction"] = raw
        path = Path(POC_EXTRACTION_DIRNAME) / POC_EXTRACTION_FILENAME
        self._write_raw(path, raw)
        return self._write(path, data)

    def store_encounter_agent(
        self,
        agent_name: str,
        encounter_index: int,
        data: dict[str, Any],
        *,
        raw: dict[str, Any] | None = None,
    ) -> str:
        """Store one agent's result for one encounter (processed + raw)."""
        encounter = self._results["encounters"].setdefault(encounter_index, {})
        encounter[agent_name] = data
        if raw is not None:
            raw_encounter = self._results["raw"]["encounters"].setdefault(encounter_index, {})
            raw_encounter[agent_name] = raw
        path = Path(agent_name) / f"encounter_{encounter_index}-results.json"
        self._write_raw(path, raw)
        return self._write(path, data)

    def store_raw_text(self, agent_name: str, encounter_index: int, raw_text: str) -> str:
        """Persist an unparseable agent output verbatim, for failure traceability.

        Used when an encounter agent produced non-JSON output: there is no
        processed result to store, but the raw string is still captured so the
        failure can be inspected. The raw string is kept in memory (under the
        ``raw`` tree) regardless of ``persist_to_disk`` so an in-process caller can
        capture it even when disk mirroring is off.
        """
        raw_encounter = self._results["raw"]["encounters"].setdefault(encounter_index, {})
        raw_encounter[agent_name] = raw_text

        relative_path = Path(agent_name) / f"encounter_{encounter_index}-raw.json"
        relative_str = relative_path.as_posix()
        if not self._persist_to_disk:
            return relative_str

        absolute_path = self._transaction_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(raw_text, encoding="utf-8")
        logger.info("Wrote raw (unparseable) output", extra={"path": relative_str})
        return relative_str

    def store_summary(self, data: dict[str, Any]) -> str:
        """Store the consolidated run summary/manifest and derive ``errors``.

        The summary already carries the pipeline's isolated (soft) failures per
        encounter. We flatten them here into ``results['errors']`` so a caller can
        branch on failures without re-parsing the nested roll-up. Hard failures are
        not present here — they were raised out of the pipeline and caught upstream.
        """
        self._results["summary"] = data
        self._results["errors"] = _extract_errors(data)
        return self._write(Path(SUMMARY_FILENAME), data)

    def store_merge_encounters(self, data: dict[str, Any]) -> str:
        """Store the consolidated ``merge_encounters`` contract for this transaction.

        Written under ``outputs/<txn>/merge-encounters/results.json`` and kept in the
        in-memory results map so an in-process caller can read it back without
        touching disk.
        """
        self._results["merge_encounters"] = data
        return self._write(Path(MERGE_ENCOUNTERS_DIRNAME) / MERGE_ENCOUNTERS_FILENAME, data)

    def store_selection(
        self, data: dict[str, Any], *, raw: dict[str, Any] | None = None
    ) -> str:
        """Store the transaction-level encounter-selection result (processed + raw).

        Written under ``outputs/<txn>/encounter-selection/results.json`` with a
        ``results-raw.json`` sibling, and kept in the in-memory results map (under
        ``selection``) so an in-process/Temporal caller can read it back without
        touching disk.
        """
        self._results["selection"] = data
        if raw is not None:
            self._results["raw"]["selection"] = raw
        path = Path(SELECTION_DIRNAME) / SELECTION_FILENAME
        self._write_raw(path, raw)
        return self._write(path, data)

    def store_audit(self, data: dict[str, Any]) -> str:
        """Store the final ``audit`` contract for this transaction.

        Written under ``outputs/<txn>/audit/results.json`` and kept in the in-memory
        results map (under ``audit``) so an in-process/Temporal caller can read it
        back without touching disk.
        """
        self._results["audit"] = data
        return self._write(Path(AUDIT_DIRNAME) / AUDIT_FILENAME, data)

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

    def _write_raw(self, processed_path: Path, raw: dict[str, Any] | None) -> None:
        """Write the raw sibling (``-raw.json``) next to a processed result file."""
        if raw is None:
            return
        self._write(_raw_sibling(processed_path), raw)


_ENCOUNTER_LEVEL_FAILURE_KEY = "__encounter__"


def _extract_errors(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a run summary's per-encounter ``failed`` maps into error records.

    Each record is ``{encounter_index, agent, error_type, message}``. Encounter-level
    failures (keyed ``__encounter__`` in the roll-up) are reported with ``agent`` set
    to ``None`` so callers can distinguish a whole-encounter failure from a single
    agent failure.
    """
    errors: list[dict[str, Any]] = []
    for encounter in summary.get("encounters", []):
        encounter_index = encounter.get("encounter_index")
        for failed_key, detail in (encounter.get("failed") or {}).items():
            agent = None if failed_key == _ENCOUNTER_LEVEL_FAILURE_KEY else failed_key
            errors.append(
                {
                    "encounter_index": encounter_index,
                    "agent": agent,
                    "error_type": (detail or {}).get("error_type"),
                    "message": (detail or {}).get("message"),
                }
            )
    return errors


def _raw_sibling(processed_path: Path) -> Path:
    """Derive the ``-raw.json`` sibling path for a processed result path.

    ``encounter_1-results.json`` -> ``encounter_1-raw.json``
    ``f2f.json``                 -> ``f2f-raw.json``
    ``results.json``             -> ``results-raw.json``
    """
    stem = processed_path.stem
    base = stem[: -len("-results")] if stem.endswith("-results") else stem
    return processed_path.with_name(f"{base}-raw.json")
