"""Tests: ResultStore captures raw outputs and soft-failure errors in memory.

All tests run with ``persist_to_disk=False`` so they assert purely on the
in-memory ``results`` dict and never touch the filesystem.
"""

from __future__ import annotations

from pathlib import Path

from f2f_orchestration.core.result_store import ResultStore

_OUTPUTS_DIR = Path("unused-when-not-persisting")


def _store() -> ResultStore:
    return ResultStore(_OUTPUTS_DIR, "transaction_test", persist_to_disk=False)


def test_new_results_have_raw_and_errors_scaffold() -> None:
    # Arrange / Act
    results = _store().results

    # Assert — the additive keys exist and start empty
    assert results["raw"] == {
        "classification": {},
        "poc_485_extraction": None,
        "encounters": {},
    }
    assert results["errors"] == []


def test_store_classification_captures_raw_in_memory() -> None:
    # Arrange
    store = _store()

    # Act
    store.store_classification("f2f", {"processed": True}, raw={"raw": True})

    # Assert — processed and raw land in their respective trees
    assert store.results["classification"]["f2f"] == {"processed": True}
    assert store.results["raw"]["classification"]["f2f"] == {"raw": True}


def test_store_poc_extraction_captures_raw_in_memory() -> None:
    # Arrange
    store = _store()

    # Act
    store.store_poc_extraction({"processed": True}, raw={"raw": True})

    # Assert
    assert store.results["poc_485_extraction"] == {"processed": True}
    assert store.results["raw"]["poc_485_extraction"] == {"raw": True}


def test_store_encounter_agent_captures_raw_per_encounter() -> None:
    # Arrange
    store = _store()

    # Act
    store.store_encounter_agent("homebound", 2, {"processed": True}, raw={"raw": True})

    # Assert — keyed {encounter_index: {agent_name: ...}} in both trees
    assert store.results["encounters"][2]["homebound"] == {"processed": True}
    assert store.results["raw"]["encounters"][2]["homebound"] == {"raw": True}


def test_missing_raw_does_not_populate_raw_tree() -> None:
    # Arrange
    store = _store()

    # Act — no raw supplied
    store.store_encounter_agent("homebound", 1, {"processed": True})

    # Assert — processed stored, raw tree untouched (no fabricated entry)
    assert store.results["encounters"][1]["homebound"] == {"processed": True}
    assert store.results["raw"]["encounters"] == {}


def test_store_raw_text_keeps_unparseable_raw_in_memory() -> None:
    # Arrange
    store = _store()

    # Act — the unparseable-failure path, with disk mirroring off
    store.store_raw_text("homebound", 3, "<<garbled>>")

    # Assert — raw string captured in memory even without disk
    assert store.results["raw"]["encounters"][3]["homebound"] == "<<garbled>>"


def test_store_summary_derives_agent_and_encounter_level_errors() -> None:
    # Arrange — a summary shaped like the F2F roll-up, with both failure kinds
    summary = {
        "encounters": [
            {
                "encounter_index": 1,
                "failed": {
                    "homebound": {"error_type": "AgentOutputError", "message": "bad json"},
                },
            },
            {
                "encounter_index": 2,
                "failed": {
                    "__encounter__": {"error_type": "ValueError", "message": "bad encounter"},
                },
            },
            {"encounter_index": 3, "failed": {}},
        ],
    }
    store = _store()

    # Act
    store.store_summary(summary)

    # Assert — agent failure keeps its name; encounter-level failure has agent=None
    assert store.results["errors"] == [
        {
            "encounter_index": 1,
            "agent": "homebound",
            "error_type": "AgentOutputError",
            "message": "bad json",
        },
        {
            "encounter_index": 2,
            "agent": None,
            "error_type": "ValueError",
            "message": "bad encounter",
        },
    ]


def test_store_summary_with_no_failures_leaves_errors_empty() -> None:
    # Arrange
    summary = {"encounters": [{"encounter_index": 1, "failed": {}}]}
    store = _store()

    # Act
    store.store_summary(summary)

    # Assert
    assert store.results["errors"] == []
