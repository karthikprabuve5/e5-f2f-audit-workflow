"""Unit tests for BasePipeline resilience helpers (backoff, retry class, stagger)."""

from __future__ import annotations

import asyncio
import time

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError

from e5_f2f_audit.pipelines.base_pipeline import BasePipeline


def _make_pipeline(*, stagger: float = 0.0) -> BasePipeline:
    return BasePipeline(
        agent_factory=object(),  # not used by the helpers under test
        tracer=object(),
        max_concurrent_agents=5,
        launch_stagger_seconds=stagger,
        max_retries=6,
        retry_base_delay_seconds=1.0,
        retry_max_delay_seconds=30.0,
    )


@pytest.mark.parametrize("attempt", [1, 2, 3, 4, 5, 6, 10])
def test_backoff_delay_stays_within_equal_jitter_bounds(attempt: int) -> None:
    # Arrange
    pipeline = _make_pipeline()
    capped = min(30.0, 1.0 * (2 ** (attempt - 1)))

    # Act
    delay = pipeline._backoff_delay(attempt)

    # Assert — equal jitter: half the cap, plus up to half the cap
    assert capped / 2 <= delay <= capped


def test_throttling_client_error_is_retryable() -> None:
    error = ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow"}}, "InvokeModel")
    assert BasePipeline._is_retryable(error) is True


def test_non_throttling_client_error_is_not_retryable() -> None:
    error = ClientError({"Error": {"Code": "ValidationException", "Message": "bad"}}, "InvokeModel")
    assert BasePipeline._is_retryable(error) is False


def test_transient_network_errors_are_retryable() -> None:
    assert BasePipeline._is_retryable(ReadTimeoutError(endpoint_url="x")) is True
    assert BasePipeline._is_retryable(EndpointConnectionError(endpoint_url="x")) is True


def test_deterministic_errors_are_not_retryable() -> None:
    assert BasePipeline._is_retryable(ValueError("parse")) is False


def test_launch_stagger_spaces_out_concurrent_launches() -> None:
    # Arrange
    stagger = 0.05
    pipeline = _make_pipeline(stagger=stagger)

    async def acquire_five() -> float:
        start = time.perf_counter()
        await asyncio.gather(*(pipeline._await_launch_slot() for _ in range(5)))
        return time.perf_counter() - start

    # Act
    elapsed = asyncio.run(acquire_five())

    # Assert — 5 launches spaced by `stagger` take at least 4 intervals
    assert elapsed >= 4 * stagger
