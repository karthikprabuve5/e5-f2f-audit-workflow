"""Unit tests for SelectionPipeline's required-input guards.

SOC date and client name are required runtime inputs; a blank/absent value is a
caller contract violation and must fail fast before any agent is invoked.
"""

from __future__ import annotations

import asyncio

import pytest

from f2f_orchestration.pipelines.selection_pipeline import SelectionPipeline


def _make_pipeline() -> SelectionPipeline:
    # agent_factory/tracer are never reached: the input guards raise first.
    return SelectionPipeline(
        agent_factory=object(),
        tracer=object(),
        max_concurrent_agents=1,
        launch_stagger_seconds=0.0,
        max_retries=0,
        retry_base_delay_seconds=0.0,
        retry_max_delay_seconds=0.0,
    )


@pytest.mark.parametrize("soc_date", ["", "   ", None])
def test_missing_soc_date_fails_fast(soc_date) -> None:
    pipeline = _make_pipeline()
    with pytest.raises(ValueError, match="soc_date is required"):
        asyncio.run(
            pipeline.run(
                transaction_id="t1",
                merge_encounters={},
                soc_date=soc_date,
                client_name="DEFAULT",
            )
        )


@pytest.mark.parametrize("client_name", ["", "   ", None])
def test_missing_client_name_fails_fast(client_name) -> None:
    pipeline = _make_pipeline()
    with pytest.raises(ValueError, match="client_name is required"):
        asyncio.run(
            pipeline.run(
                transaction_id="t1",
                merge_encounters={},
                soc_date="2026-07-15",
                client_name=client_name,
            )
        )


def test_embed_exclusions_records_excluded_encounters() -> None:
    processed = {"result": {"best_encounter_index": 1, "decision": "SELECTED"}}
    excluded = [
        {
            "encounter_index": 3,
            "encounter_category": "referral_documents",
            "encounter_subcategory": "15.2",
            "reason": "referral_document_supporting_only",
        }
    ]

    SelectionPipeline._embed_exclusions(processed, excluded, "t1")

    assert processed["result"]["excluded_encounters"] == excluded
    assert processed["result"]["excluded_encounter_indices"] == [3]


def test_embed_exclusions_defaults_to_empty_when_none() -> None:
    processed = {"result": {"best_encounter_index": 2}}
    SelectionPipeline._embed_exclusions(processed, None, "t1")

    assert processed["result"]["excluded_encounters"] == []
    assert processed["result"]["excluded_encounter_indices"] == []


def test_embed_exclusions_rejects_excluded_best_index() -> None:
    processed = {"result": {"best_encounter_index": 3, "decision": "SELECTED"}}
    excluded = [{"encounter_index": 3, "encounter_category": "referral_documents"}]

    with pytest.raises(ValueError, match="excluded referral index"):
        SelectionPipeline._embed_exclusions(processed, excluded, "t1")
