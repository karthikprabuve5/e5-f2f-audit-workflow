"""Langfuse v4 tracing.

``LangfuseTracer`` builds one end-to-end, nested trace tree per pipeline run:

    SESSION <transaction_id>-poc / <transaction_id>-f2f
      TRACE  poc / f2f
        SPAN classification
        SPAN encounter_<i>
          SPAN <agent_name>   (deep-agent LLM/tool calls nest underneath)

Trace-level attributes (``session_id``, ``user_id``, ``tags``) are propagated
with :func:`langfuse.propagate_attributes`; span nesting relies on OpenTelemetry
context propagation, which also holds across ``asyncio.gather`` because each task
copies the active context at creation time — so parallel encounters and agents
attach to the correct parent without cross-talk.

When Langfuse credentials are absent the tracer degrades to a no-op: every
context manager yields ``None`` and ``callback_config`` returns an empty config.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Literal

from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler

from .logging_setup import get_logger

logger = get_logger(__name__)

PipelineName = Literal["poc", "f2f", "selection"]


class LangfuseTracer:
    """Creates the nested Langfuse trace tree and per-call callback configs.

    Takes plain arguments (credentials + the ``client_name`` / ``active_model``
    used for trace metadata) — no config object. Tracing is enabled only when
    both Langfuse keys are provided; otherwise it degrades to a no-op.
    """

    def __init__(
        self,
        *,
        public_key: str | None,
        secret_key: str | None,
        host: str,
        client_name: str,
        active_model: str,
    ) -> None:
        self._client_name = client_name
        self._active_model = active_model
        self._client: Langfuse | None = None
        self._handler: CallbackHandler | None = None

        if public_key and secret_key:
            self._client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            self._handler = CallbackHandler()
            logger.info("Langfuse tracing enabled (host=%s)", host)
        else:
            logger.warning("Langfuse credentials missing — tracing disabled (no-op mode).")

    @property
    def is_enabled(self) -> bool:
        return self._client is not None

    def callback_config(
        self,
        *,
        run_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the ``config`` dict passed to a deep agent ``ainvoke``.

        Attaches the Langfuse callback (so the agent's internal LLM/tool calls
        nest under the currently active span) plus an optional run name and
        metadata. Returns an empty dict when tracing is disabled.
        """
        if self._handler is None:
            return {}

        config: dict[str, Any] = {"callbacks": [self._handler]}
        if run_name is not None:
            config["run_name"] = run_name
        if metadata is not None:
            config["metadata"] = metadata
        return config

    @contextmanager
    def pipeline_trace(self, pipeline: PipelineName, transaction_id: str) -> Iterator[Any]:
        """Open the root trace for a pipeline run inside its own session."""
        if self._client is None:
            yield None
            return

        session_id = f"{transaction_id}-{pipeline}"
        trace_metadata = {
            "transaction_id": transaction_id,
            "pipeline": pipeline,
            "client_name": self._client_name,
            "active_model": self._active_model,
        }
        with propagate_attributes(
            session_id=session_id,
            user_id=transaction_id,
            tags=[pipeline],
            trace_name=pipeline,
        ):
            with self._client.start_as_current_observation(
                name=pipeline, as_type="chain", metadata=trace_metadata
            ) as span:
                yield span

    @contextmanager
    def step_span(
        self,
        name: str,
        *,
        as_type: str = "span",
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Open a generic child span under the current context."""
        if self._client is None:
            yield None
            return

        with self._client.start_as_current_observation(
            name=name, as_type=as_type, metadata=metadata
        ) as span:
            yield span

    def encounter_span(
        self, index: int, metadata: dict[str, Any] | None = None
    ) -> AbstractContextManager[Any]:
        """Context manager for an encounter-level span."""
        return self.step_span(f"encounter_{index}", as_type="span", metadata=metadata)

    def agent_span(
        self, agent_name: str, metadata: dict[str, Any] | None = None
    ) -> AbstractContextManager[Any]:
        """Context manager for an agent-level span."""
        return self.step_span(agent_name, as_type="agent", metadata=metadata)

    def current_trace_reference(self) -> dict[str, str | None]:
        """Return the current trace id and URL for the run summary/debugging."""
        if self._client is None:
            return {"trace_id": None, "trace_url": None}

        trace_id = self._client.get_current_trace_id()
        return {
            "trace_id": trace_id,
            "trace_url": self._client.get_trace_url(trace_id=trace_id) if trace_id else None,
        }

    def flush(self) -> None:
        """Flush buffered spans to Langfuse (call at the end of a run)."""
        if self._client is not None:
            self._client.flush()
