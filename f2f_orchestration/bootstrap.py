"""Local-dev wiring: build collaborators and pipelines from the environment.

This is the one place that reads ``os.getenv`` and turns environment values into
constructed objects. Modules themselves take plain arguments and hold no
defaults; the defaults live here (second arg to ``os.getenv``) so a production
layer can supply the same values another way without touching the modules.

Keeping this shared keeps ``run_poc.py`` and ``run_f2f.py`` thin and identical in
their setup — each entrypoint just loads its document and calls one pipeline.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

from .agents.agent_factory import AgentFactory
from .core.anchors import AnchorSet
from .core.document_source import DocumentKind, LocalDirectoryDocumentSource
from .core.logging_setup import configure_logging, get_logger
from .core.models import ModelName, ModelProvider
from .core.prompts import PromptRenderer
from .core.result_store import POC_EXTRACTION_FILENAME, ResultStore
from .core.tracing import LangfuseTracer
from .pipelines.f2f_pipeline import F2fPipeline
from .pipelines.poc_pipeline import PocPipeline

logger = get_logger(__name__)


class RunMode(StrEnum):
    """Which transactions an entrypoint should process."""

    FULL = "full"  # every transaction found under ocr-markdown/
    SELECTED = "selected"  # only the explicitly listed transactions


def list_transactions(kind: DocumentKind) -> list[str]:
    """Return sorted transaction ids under ocr-markdown/ that have the given doc."""
    base = _ocr_markdown_dir()
    if not base.is_dir():
        return []
    return sorted(
        entry.name
        for entry in base.iterdir()
        if entry.is_dir() and (entry / f"{kind}.md").is_file()
    )


def resolve_transactions(
    kind: DocumentKind, mode: RunMode, selected: Sequence[str]
) -> list[str]:
    """Resolve the transaction ids to run for the chosen mode."""
    if mode is RunMode.FULL:
        return list_transactions(kind)
    return list(selected)


def load_environment() -> None:
    """Load ``.env`` (local dev) and configure structured logging. Call first."""
    load_dotenv()
    configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))


def client_name() -> str:
    return os.getenv("CLIENT_NAME", "DEFAULT")


def active_model() -> ModelName:
    return cast(ModelName, os.getenv("ACTIVE_MODEL", "kimi"))


def build_model_provider() -> ModelProvider:
    return ModelProvider(
        active_model=active_model(),
        kimi_model_id=_require_env("MODEL_KIMI"),
        anthropic_model_id=_require_env("MODEL_ANTHROPIC"),
        kimi_provider=os.getenv("MODEL_KIMI_PROVIDER", "moonshotai"),
        anthropic_provider=os.getenv("MODEL_ANTHROPIC_PROVIDER", "anthropic"),
        temperature=_float_env("MODEL_TEMPERATURE", 0.0),
        read_timeout_seconds=_int_env("BEDROCK_READ_TIMEOUT", 1000),
        connect_timeout_seconds=_int_env("BEDROCK_CONNECT_TIMEOUT", 60),
        max_attempts=_int_env("BEDROCK_MAX_ATTEMPTS", 5),
        retry_mode=os.getenv("BEDROCK_RETRY_MODE", "adaptive"),
    )


def build_tracer() -> LangfuseTracer:
    return LangfuseTracer(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        client_name=client_name(),
        active_model=active_model(),
    )


def build_agent_factory(model_provider: ModelProvider) -> AgentFactory:
    return AgentFactory(
        model_provider=model_provider,
        prompt_renderer=PromptRenderer(_prompts_dir()),
        skills_root=_skills_dir(),
    )


def build_document_source() -> LocalDirectoryDocumentSource:
    return LocalDirectoryDocumentSource(_ocr_markdown_dir())


def build_result_store(transaction_id: str) -> ResultStore:
    return ResultStore(
        _outputs_dir(),
        transaction_id,
        persist_to_disk=_bool_env("PERSIST_TO_DISK", True),
    )


def build_poc_pipeline() -> PocPipeline:
    return _build_pipeline(PocPipeline)


def build_f2f_pipeline() -> F2fPipeline:
    return _build_pipeline(F2fPipeline)


def load_saved_anchors(transaction_id: str) -> AnchorSet:
    """Rebuild the POC anchors from the extraction result saved by ``run_poc``.

    Lets F2F be iterated on independently of the (slower) POC run.
    """
    poc_path = _outputs_dir() / transaction_id / POC_EXTRACTION_FILENAME
    try:
        extraction = json.loads(poc_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"POC anchors not found at {poc_path}. "
            f"Run run_poc for transaction '{transaction_id}' first."
        ) from exc
    return AnchorSet.from_poc_extraction(extraction, client_name=client_name())


def _build_pipeline[PipelineT: (PocPipeline, F2fPipeline)](
    pipeline_cls: type[PipelineT],
) -> PipelineT:
    """Construct a pipeline with a fresh factory/tracer and the concurrency knobs."""
    model_provider = build_model_provider()
    return pipeline_cls(
        agent_factory=build_agent_factory(model_provider),
        tracer=build_tracer(),
        max_concurrent_agents=_int_env("MAX_CONCURRENT_AGENTS", 5),
        launch_stagger_seconds=_float_env("AGENT_LAUNCH_STAGGER_SECONDS", 0.0),
        max_retries=_int_env("AGENT_MAX_RETRIES", 6),
        retry_base_delay_seconds=_float_env("AGENT_RETRY_BASE_DELAY_SECONDS", 1.0),
        retry_max_delay_seconds=_float_env("AGENT_RETRY_MAX_DELAY_SECONDS", 30.0),
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _prompts_dir() -> Path:
    return Path(os.getenv("PROMPTS_DIR", str(_project_root() / "prompts")))


def _skills_dir() -> Path:
    return Path(os.getenv("SKILLS_DIR", str(_project_root() / "skills")))


def _ocr_markdown_dir() -> Path:
    return Path(os.getenv("OCR_MARKDOWN_DIR", str(_project_root() / "ocr-markdown")))


def _outputs_dir() -> Path:
    return Path(os.getenv("OUTPUTS_DIR", str(_project_root() / "outputs")))


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return value


def _int_env(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _float_env(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _bool_env(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")
