"""Structured, streaming logging for the end-to-end pipeline.

Logs are emitted as one JSON object per line to a stream (stdout by default),
so they are machine-parseable in production and stream live during a run. Use
``configure_logging`` once at the entrypoint, ``get_logger`` in modules, and
``bind`` to attach run context (transaction_id, pipeline, encounter, agent) that
is carried on every subsequent log line.

Never log secrets, tokens, or PHI/PII — pass only non-sensitive identifiers and
status fields as context.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import IO, Any

PACKAGE_LOGGER_NAME = "e5_f2f_audit"

# LogRecord attributes that are not user-supplied context.
_RESERVED_RECORD_KEYS = frozenset(
    logging.makeLogRecord({}).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON, including bound context fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(self._extract_context(record))

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)

    @staticmethod
    def _extract_context(record: logging.LogRecord) -> dict[str, Any]:
        return {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_RECORD_KEYS
        }


class BoundLogger(logging.LoggerAdapter):
    """A logger adapter that merges bound context with per-call ``extra``."""

    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        call_extra = kwargs.get("extra") or {}
        kwargs["extra"] = {**self.extra, **call_extra}
        return msg, kwargs


def configure_logging(*, level: int | str, stream: IO[str] | None = None) -> None:
    """Attach a single streaming JSON handler to the package logger.

    ``level`` is supplied by the caller (e.g. ``os.getenv("LOG_LEVEL", "INFO")``
    at the entrypoint). Idempotent: replaces any handlers previously installed
    by this function.
    """
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    package_logger.handlers.clear()
    package_logger.addHandler(handler)
    package_logger.setLevel(level)
    package_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a module logger under the package namespace."""
    return logging.getLogger(name)


def bind(logger: logging.Logger | BoundLogger, **context: Any) -> BoundLogger:
    """Return a logger that adds ``context`` to every log line.

    Binding an already-bound logger merges the new context on top of the old.
    """
    if isinstance(logger, BoundLogger):
        return BoundLogger(logger.logger, {**logger.extra, **context})
    return BoundLogger(logger, context)
