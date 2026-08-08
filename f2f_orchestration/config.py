"""Typed, framework-agnostic runtime configuration for the agentic (Tier 2) layer.

Every value the agentic pipelines need — model provisioning, Langfuse tracing,
concurrency/retry tuning, and the prompt/skill roots — lives here as a frozen,
composed config object. :meth:`OrchestrationConfig.from_env` reproduces the
local-dev behaviour (read ``os.getenv`` with documented defaults); an external
orchestrator constructs the same object however it likes (a settings model, a
secrets manager, plain literals) and passes it to ``bootstrap.build_*`` — no
environment required.

This module reads the environment only inside the explicit ``from_env`` classmethods;
constructing a config directly touches no globals, so it is safe to build and reuse
from any process (Temporal worker, web service, another repo).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from .core.models import ModelName


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Bedrock model provisioning for both ``kimi`` and ``anthropic`` plus the active one."""

    active_model: ModelName
    kimi_model_id: str
    anthropic_model_id: str
    kimi_provider: str = "moonshotai"
    anthropic_provider: str = "anthropic"
    temperature: float = 0.0
    read_timeout_seconds: int = 1000
    connect_timeout_seconds: int = 60
    max_attempts: int = 5
    retry_mode: str = "adaptive"

    @classmethod
    def from_env(cls) -> "ModelConfig":
        return cls(
            active_model=cast(ModelName, os.getenv("ACTIVE_MODEL", "kimi")),
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


@dataclass(frozen=True, slots=True)
class TracingConfig:
    """Langfuse credentials/host. Missing credentials => tracing runs in no-op mode."""

    public_key: str | None = None
    secret_key: str | None = None
    host: str = "https://cloud.langfuse.com"

    @classmethod
    def from_env(cls) -> "TracingConfig":
        return cls(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )


@dataclass(frozen=True, slots=True)
class ConcurrencyConfig:
    """Per-run concurrency cap, launch stagger, and agent retry/backoff tuning."""

    max_concurrent_agents: int = 5
    launch_stagger_seconds: float = 0.0
    max_retries: int = 6
    retry_base_delay_seconds: float = 1.0
    retry_max_delay_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "ConcurrencyConfig":
        return cls(
            max_concurrent_agents=_int_env("MAX_CONCURRENT_AGENTS", 5),
            launch_stagger_seconds=_float_env("AGENT_LAUNCH_STAGGER_SECONDS", 0.0),
            max_retries=_int_env("AGENT_MAX_RETRIES", 6),
            retry_base_delay_seconds=_float_env("AGENT_RETRY_BASE_DELAY_SECONDS", 1.0),
            retry_max_delay_seconds=_float_env("AGENT_RETRY_MAX_DELAY_SECONDS", 30.0),
        )


@dataclass(frozen=True, slots=True)
class OrchestrationConfig:
    """Everything the agentic pipelines need, composed from cohesive sub-configs.

    ``model`` is required (Bedrock ids have no safe defaults); the rest carry the
    same defaults the local entrypoints used to read from the environment.
    """

    model: ModelConfig
    tracing: TracingConfig = field(default_factory=TracingConfig)
    concurrency: ConcurrencyConfig = field(default_factory=ConcurrencyConfig)
    prompts_dir: Path = field(default_factory=lambda: _default_package_dir("prompts"))
    skills_dir: Path = field(default_factory=lambda: _default_package_dir("skills"))
    client_name: str = "DEFAULT"

    @classmethod
    def from_env(cls) -> "OrchestrationConfig":
        return cls(
            model=ModelConfig.from_env(),
            tracing=TracingConfig.from_env(),
            concurrency=ConcurrencyConfig.from_env(),
            prompts_dir=Path(os.getenv("PROMPTS_DIR", str(_default_package_dir("prompts")))),
            skills_dir=Path(os.getenv("SKILLS_DIR", str(_default_package_dir("skills")))),
            client_name=os.getenv("CLIENT_NAME", "DEFAULT"),
        )


def _default_package_dir(name: str) -> Path:
    """Resolve a bundled data dir (``prompts``/``skills``) shipped inside the package.

    Package-relative (not repo-relative) so an installed wheel finds its own prompts
    and skills without a source checkout. ``PROMPTS_DIR``/``SKILLS_DIR`` still override.
    """
    return Path(__file__).resolve().parent / name


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return value


def _int_env(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _float_env(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))
