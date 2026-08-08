"""Shared execution engine for the POC and F2F pipelines.

``BasePipeline`` owns the machinery that keeps a highly parallel, multi-agent run
safe against Bedrock throttling and transient failures, while every agent call is
wrapped in its own Langfuse span:

* **Concurrency cap** — a single ``asyncio.Semaphore`` bounds the total number of
  in-flight agent calls across *all* encounters and agents (encounters run in
  parallel × agents-per-encounter run in parallel, capped globally).
* **Launch stagger** — consecutive launches are spaced by a small interval so the
  ramp-up does not hit Bedrock as one simultaneous burst.
* **Retry with backoff** — throttling and transient network errors are retried
  with exponential backoff plus jitter; deterministic failures are not retried.

All tuning values are explicit constructor arguments (sourced from the
entrypoint's environment) — the engine has no hidden defaults.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from ..agents.agent_factory import AgentFactory, AgentOutput
from ..core.detection import AgentName
from ..core.logging_setup import get_logger
from ..core.tracing import LangfuseTracer

logger = get_logger(__name__)

# Bedrock error codes that indicate a transient, retryable condition.
_RETRYABLE_ERROR_CODES = frozenset(
    {
        "ThrottlingException",
        "Throttling",
        "TooManyRequestsException",
        "RequestLimitExceeded",
        "ProvisionedThroughputExceededException",
        "ServiceUnavailableException",
        "ModelTimeoutException",
        "ModelNotReadyException",
    }
)


class BasePipeline:
    """Base class providing concurrency-safe, traced, retrying agent execution."""

    def __init__(
        self,
        *,
        agent_factory: AgentFactory,
        tracer: LangfuseTracer,
        max_concurrent_agents: int,
        launch_stagger_seconds: float,
        max_retries: int,
        retry_base_delay_seconds: float,
        retry_max_delay_seconds: float,
    ) -> None:
        self._factory = agent_factory
        self._tracer = tracer
        self._max_retries = max_retries
        self._retry_base_delay_seconds = retry_base_delay_seconds
        self._retry_max_delay_seconds = retry_max_delay_seconds
        self._launch_stagger_seconds = launch_stagger_seconds

        self._semaphore = asyncio.Semaphore(max_concurrent_agents)
        self._launch_lock = asyncio.Lock()
        self._next_launch_at = 0.0

    async def _run_agent(
        self,
        agent_name: AgentName,
        *,
        document_content: str,
        replacements: Mapping[str, str] | None = None,
        span_metadata: dict[str, Any] | None = None,
    ) -> AgentOutput:
        """Run one agent with launch stagger, concurrency cap, retries, and a span.

        The Langfuse span is opened inside the current OpenTelemetry context, so
        it nests under whatever encounter/pipeline span is active on this task.
        """
        await self._await_launch_slot()

        async with self._semaphore:
            with self._tracer.agent_span(str(agent_name), metadata=span_metadata):
                config = self._tracer.callback_config(
                    run_name=str(agent_name), metadata=span_metadata
                )

                async def call() -> AgentOutput:
                    return await self._factory.run(
                        agent_name,
                        document_content=document_content,
                        replacements=replacements,
                        config=config,
                    )

                return await self._invoke_with_retries(call, agent_name=agent_name)

    async def _await_launch_slot(self) -> None:
        """Space out consecutive agent launches by ``launch_stagger_seconds``."""
        if self._launch_stagger_seconds <= 0:
            return

        async with self._launch_lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait_seconds = self._next_launch_at - now
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self._next_launch_at = max(now, self._next_launch_at) + self._launch_stagger_seconds

    async def _invoke_with_retries(
        self,
        operation: Callable[[], Awaitable[AgentOutput]],
        *,
        agent_name: AgentName,
    ) -> AgentOutput:
        """Invoke ``operation``, retrying transient/throttling failures with backoff."""
        attempt = 0
        while True:
            try:
                return await operation()
            except Exception as exc:
                # Broad catch is intentional: we must inspect the error to decide
                # whether it is a retryable throttling/transient failure. Anything
                # non-retryable (or past the retry budget) is re-raised immediately.
                attempt += 1
                if attempt > self._max_retries or not self._is_retryable(exc):
                    logger.error(
                        "Agent call failed",
                        extra={
                            "agent": str(agent_name),
                            "attempts": attempt,
                            "error_type": type(exc).__name__,
                        },
                    )
                    raise

                delay_seconds = self._backoff_delay(attempt)
                logger.warning(
                    "Agent call throttled/transient; retrying after backoff",
                    extra={
                        "agent": str(agent_name),
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                        "delay_seconds": round(delay_seconds, 3),
                        "error_type": type(exc).__name__,
                    },
                )
                await asyncio.sleep(delay_seconds)

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with equal jitter, capped at the max delay."""
        capped = min(
            self._retry_max_delay_seconds,
            self._retry_base_delay_seconds * (2 ** (attempt - 1)),
        )
        half = capped / 2
        return half + random.uniform(0, half)

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """True for Bedrock throttling and transient network errors only."""
        if isinstance(exc, (ConnectTimeoutError, ReadTimeoutError, EndpointConnectionError)):
            return True
        if isinstance(exc, ClientError):
            error_code = exc.response.get("Error", {}).get("Code")
            return error_code in _RETRYABLE_ERROR_CODES
        return False
