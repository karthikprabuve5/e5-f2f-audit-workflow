"""Local-dev wiring: build collaborators and pipelines from configuration.

The agentic (Tier 2) values are grouped in :class:`~e5_f2f_audit.config.OrchestrationConfig`.
The ``build_*`` helpers take that config and turn it into constructed objects; the
local entrypoints call them with no argument, so ``config`` defaults to
``OrchestrationConfig.from_env()`` (the same ``os.getenv`` + defaults behaviour as
before). An external orchestrator builds its own ``OrchestrationConfig`` and passes
it in — no environment required.

The remaining ``os.getenv`` reads here are Tier-3 disk concerns (outputs/ocr/soc
paths, ``PERSIST_TO_DISK``) used only by the local entrypoints. Modules themselves
still take plain arguments and hold no defaults.

Keeping this shared keeps ``run_poc.py`` and ``run_f2f.py`` thin and identical in
their setup — each entrypoint just loads its document and calls one pipeline.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv

from .agents.agent_factory import AgentFactory
from .config import OrchestrationConfig
from .core.anchors import AnchorSet
from .core.document_source import DocumentKind, LocalDirectoryDocumentSource
from .core.logging_setup import configure_logging, get_logger
from .core.models import ModelProvider
from .core.prompts import PromptRenderer
from .core.result_store import (
    CLASSIFICATION_DIRNAME,
    CLASSIFICATION_F2F_FILENAME,
    MERGE_ENCOUNTERS_DIRNAME,
    MERGE_ENCOUNTERS_FILENAME,
    POC_EXTRACTION_DIRNAME,
    POC_EXTRACTION_FILENAME,
    SELECTION_DIRNAME,
    SELECTION_FILENAME,
    ResultStore,
)
from .core.tracing import LangfuseTracer
from .audit import FinalAuditEngine
from .merge_encounters import DiskMergeSource
from .pipelines.f2f_pipeline import F2fPipeline
from .pipelines.poc_pipeline import PocPipeline
from .pipelines.selection_pipeline import SelectionPipeline

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
    """Load ``.env`` (local dev) and configure structured logging. Call first.

    ``.env`` is an optional local-dev convenience: values already present in the
    process environment take precedence and are sufficient in deployed contexts.
    A present-but-unreadable ``.env`` (e.g. wrong owner/permissions) must not abort
    every entrypoint — especially the pure ``run_merge_encounters`` step, which
    needs no secrets. We log a warning (never silent) and continue from the real
    environment instead of raising.
    """
    dotenv_error: OSError | None = None
    try:
        load_dotenv()
    except OSError as exc:
        dotenv_error = exc
    configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))
    if dotenv_error is not None:
        get_logger(__name__).warning(
            ".env present but unreadable; continuing from process environment",
            extra={
                "error_type": type(dotenv_error).__name__,
                "dotenv_path": str(Path(".env").resolve()),
            },
        )


def client_name() -> str:
    return os.getenv("CLIENT_NAME", "DEFAULT")


def build_model_provider(config: OrchestrationConfig) -> ModelProvider:
    model = config.model
    return ModelProvider(
        active_model=model.active_model,
        kimi_model_id=model.kimi_model_id,
        anthropic_model_id=model.anthropic_model_id,
        kimi_provider=model.kimi_provider,
        anthropic_provider=model.anthropic_provider,
        temperature=model.temperature,
        read_timeout_seconds=model.read_timeout_seconds,
        connect_timeout_seconds=model.connect_timeout_seconds,
        max_attempts=model.max_attempts,
        retry_mode=model.retry_mode,
    )


def build_tracer(config: OrchestrationConfig) -> LangfuseTracer:
    return LangfuseTracer(
        public_key=config.tracing.public_key,
        secret_key=config.tracing.secret_key,
        host=config.tracing.host,
        client_name=config.client_name,
        active_model=config.model.active_model,
    )


def build_agent_factory(
    config: OrchestrationConfig, model_provider: ModelProvider
) -> AgentFactory:
    return AgentFactory(
        model_provider=model_provider,
        prompt_renderer=PromptRenderer(config.prompts_dir),
        skills_root=config.skills_dir,
    )


def build_document_source() -> LocalDirectoryDocumentSource:
    return LocalDirectoryDocumentSource(_ocr_markdown_dir())


def build_merge_source() -> DiskMergeSource:
    """Disk-backed merge source over the same ``outputs/`` dir the pipelines write.

    This is the source used by the standalone ``run_merge_encounters`` entrypoint.
    The in-memory and framework-agnostic sources are constructed by their callers
    (a live ``ResultStore`` / a plain mapping), so only the disk source needs
    environment wiring here.
    """
    return DiskMergeSource(_outputs_dir())


def output_exists(transaction_id: str, filename: str) -> bool:
    """True when ``filename`` already exists under this transaction's outputs dir.

    Used by the entrypoints to skip transactions a pipeline has already finished.
    The marker is each pipeline's own final artifact (POC vs F2F), so the two
    entrypoints stay independent even though they share the transaction folder.
    """
    return (_outputs_dir() / transaction_id / filename).is_file()


def build_result_store(transaction_id: str) -> ResultStore:
    return ResultStore(
        _outputs_dir(),
        transaction_id,
        persist_to_disk=_bool_env("PERSIST_TO_DISK", True),
    )


def build_poc_pipeline(config: OrchestrationConfig | None = None) -> PocPipeline:
    return _build_pipeline(PocPipeline, config)


def build_f2f_pipeline(config: OrchestrationConfig | None = None) -> F2fPipeline:
    return _build_pipeline(F2fPipeline, config)


def build_selection_pipeline(config: OrchestrationConfig | None = None) -> SelectionPipeline:
    return _build_pipeline(SelectionPipeline, config)


def load_merge_encounters(transaction_id: str) -> dict:
    """Load the consolidated ``merge-encounters/results.json`` for the selection entrypoint.

    Raises an actionable error when the merge has not been built yet, so the
    selection run fails loudly rather than selecting from nothing.
    """
    merge_path = (
        _outputs_dir() / transaction_id / MERGE_ENCOUNTERS_DIRNAME / MERGE_ENCOUNTERS_FILENAME
    )
    try:
        return json.loads(merge_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Merge-encounters results not found at {merge_path}. "
            f"Run run_merge_encounters for transaction '{transaction_id}' first."
        ) from exc


def build_final_audit_engine() -> FinalAuditEngine:
    """Build the pure final-audit engine (no env/tracer/store needed)."""
    return FinalAuditEngine()


def load_selection(transaction_id: str) -> dict:
    """Load the ``encounter-selection/results.json`` for the final-audit entrypoint.

    Raises an actionable error when selection has not run yet, so the audit run
    fails loudly rather than auditing against a missing verdict.
    """
    selection_path = _outputs_dir() / transaction_id / SELECTION_DIRNAME / SELECTION_FILENAME
    try:
        return json.loads(selection_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Encounter-selection results not found at {selection_path}. "
            f"Run run_selection for transaction '{transaction_id}' first."
        ) from exc


def load_classification_roster(transaction_id: str) -> dict:
    """Load the F2F classification roster (``classification/f2f.json``).

    Used by the selection entrypoint to pre-filter supporting-only encounters
    (e.g. ``referral_documents``) out of the candidate set before ranking. Raises
    an actionable error when classification has not run yet, so selection fails
    loudly rather than ranking an unfiltered candidate set.
    """
    roster_path = (
        _outputs_dir() / transaction_id / CLASSIFICATION_DIRNAME / CLASSIFICATION_F2F_FILENAME
    )
    try:
        return json.loads(roster_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"F2F classification roster not found at {roster_path}. "
            f"Run run_f2f for transaction '{transaction_id}' first."
        ) from exc


def load_soc_dates() -> dict[str, str]:
    """Load the local ``transaction_id -> soc_date`` map used by run_selection.

    The path defaults to ``soc_dates.json`` at the project root and is overridable
    via ``SOC_DATES_FILE``. SOC is a required selection input, so a missing map is
    a configuration error and fails fast.
    """
    soc_path = _soc_dates_file()
    try:
        data = json.loads(soc_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"SOC date map not found at {soc_path}. Create it as a JSON object "
            f'mapping transaction_id -> soc_date, e.g. {{"transaction_x": "2026-03-01"}}.'
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"SOC date map at {soc_path} must be a JSON object.")
    return {str(key): str(value) for key, value in data.items()}


def load_saved_anchors(transaction_id: str) -> AnchorSet:
    """Rebuild the POC anchors from the extraction result saved by ``run_poc``.

    Lets F2F be iterated on independently of the (slower) POC run.
    """
    poc_path = (
        _outputs_dir() / transaction_id / POC_EXTRACTION_DIRNAME / POC_EXTRACTION_FILENAME
    )
    try:
        extraction = json.loads(poc_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"POC anchors not found at {poc_path}. "
            f"Run run_poc for transaction '{transaction_id}' first."
        ) from exc
    return AnchorSet.from_poc_extraction(extraction, client_name=client_name())


def _build_pipeline[PipelineT: (PocPipeline, F2fPipeline, SelectionPipeline)](
    pipeline_cls: type[PipelineT],
    config: OrchestrationConfig | None,
) -> PipelineT:
    """Construct a pipeline with a fresh factory/tracer and the concurrency knobs.

    ``config`` defaults to ``OrchestrationConfig.from_env()`` so the local
    entrypoints keep their zero-argument setup; an external caller passes its own.
    """
    cfg = config or OrchestrationConfig.from_env()
    model_provider = build_model_provider(cfg)
    return pipeline_cls(
        agent_factory=build_agent_factory(cfg, model_provider),
        tracer=build_tracer(cfg),
        max_concurrent_agents=cfg.concurrency.max_concurrent_agents,
        launch_stagger_seconds=cfg.concurrency.launch_stagger_seconds,
        max_retries=cfg.concurrency.max_retries,
        retry_base_delay_seconds=cfg.concurrency.retry_base_delay_seconds,
        retry_max_delay_seconds=cfg.concurrency.retry_max_delay_seconds,
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ocr_markdown_dir() -> Path:
    return Path(os.getenv("OCR_MARKDOWN_DIR", str(_project_root() / "ocr-markdown")))


def _outputs_dir() -> Path:
    return Path(os.getenv("OUTPUTS_DIR", str(_project_root() / "outputs")))


def _soc_dates_file() -> Path:
    return Path(os.getenv("SOC_DATES_FILE", str(_project_root() / "soc_dates.json")))


def _bool_env(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")
