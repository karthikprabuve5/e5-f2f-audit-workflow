"""Unit tests for the composed runtime configuration and its injection.

Covers two guarantees: (1) ``OrchestrationConfig.from_env`` reproduces the exact
defaults the entrypoints used to read from the environment, and reads overrides when
present; (2) the ``bootstrap.build_*`` helpers construct the agentic collaborators
purely from an injected config — with **no** environment variables set — which is
the whole point of the reuse boundary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from f2f_orchestration import bootstrap
from f2f_orchestration.config import (
    ConcurrencyConfig,
    ModelConfig,
    OrchestrationConfig,
    TracingConfig,
)
from f2f_orchestration.pipelines.selection_pipeline import SelectionPipeline

# Every environment key the config touches, cleared before each test for isolation.
_CONFIG_ENV_KEYS = (
    "ACTIVE_MODEL",
    "MODEL_KIMI",
    "MODEL_ANTHROPIC",
    "MODEL_KIMI_PROVIDER",
    "MODEL_ANTHROPIC_PROVIDER",
    "MODEL_TEMPERATURE",
    "BEDROCK_READ_TIMEOUT",
    "BEDROCK_CONNECT_TIMEOUT",
    "BEDROCK_MAX_ATTEMPTS",
    "BEDROCK_RETRY_MODE",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
    "MAX_CONCURRENT_AGENTS",
    "AGENT_LAUNCH_STAGGER_SECONDS",
    "AGENT_MAX_RETRIES",
    "AGENT_RETRY_BASE_DELAY_SECONDS",
    "AGENT_RETRY_MAX_DELAY_SECONDS",
    "PROMPTS_DIR",
    "SKILLS_DIR",
    "CLIENT_NAME",
)


@pytest.fixture(autouse=True)
def _clean_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _CONFIG_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _config() -> OrchestrationConfig:
    """A fully-specified config built without any environment reads."""
    return OrchestrationConfig(
        model=ModelConfig(
            active_model="anthropic",
            kimi_model_id="kimi-x",
            anthropic_model_id="claude-x",
        ),
        tracing=TracingConfig(),
        concurrency=ConcurrencyConfig(max_concurrent_agents=3, max_retries=2),
        prompts_dir=Path("/tmp/prompts"),
        skills_dir=Path("/tmp/skills"),
        client_name="CLIENT_A",
    )


def test_from_env_uses_documented_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_KIMI", "kimi-id")
    monkeypatch.setenv("MODEL_ANTHROPIC", "claude-id")

    config = OrchestrationConfig.from_env()

    assert config.model.active_model == "kimi"
    assert config.model.kimi_provider == "moonshotai"
    assert config.model.anthropic_provider == "anthropic"
    assert config.model.temperature == 0.0
    assert config.model.read_timeout_seconds == 1000
    assert config.model.connect_timeout_seconds == 60
    assert config.model.max_attempts == 5
    assert config.model.retry_mode == "adaptive"
    assert config.tracing.public_key is None
    assert config.tracing.secret_key is None
    assert config.tracing.host == "https://cloud.langfuse.com"
    assert config.concurrency.max_concurrent_agents == 5
    assert config.concurrency.launch_stagger_seconds == 0.0
    assert config.concurrency.max_retries == 6
    assert config.concurrency.retry_base_delay_seconds == 1.0
    assert config.concurrency.retry_max_delay_seconds == 30.0
    assert config.client_name == "DEFAULT"
    assert config.prompts_dir.name == "prompts"
    assert config.skills_dir.name == "skills"


def test_from_env_reads_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_KIMI", "kimi-id")
    monkeypatch.setenv("MODEL_ANTHROPIC", "claude-id")
    monkeypatch.setenv("ACTIVE_MODEL", "anthropic")
    monkeypatch.setenv("MODEL_TEMPERATURE", "0.7")
    monkeypatch.setenv("BEDROCK_MAX_ATTEMPTS", "9")
    monkeypatch.setenv("MAX_CONCURRENT_AGENTS", "12")
    monkeypatch.setenv("AGENT_MAX_RETRIES", "3")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    monkeypatch.setenv("LANGFUSE_HOST", "https://lf.example")
    monkeypatch.setenv("CLIENT_NAME", "CLIENT_A")
    monkeypatch.setenv("PROMPTS_DIR", "/tmp/p")
    monkeypatch.setenv("SKILLS_DIR", "/tmp/s")

    config = OrchestrationConfig.from_env()

    assert config.model.active_model == "anthropic"
    assert config.model.temperature == 0.7
    assert config.model.max_attempts == 9
    assert config.concurrency.max_concurrent_agents == 12
    assert config.concurrency.max_retries == 3
    assert config.tracing.public_key == "pk"
    assert config.tracing.secret_key == "sk"
    assert config.tracing.host == "https://lf.example"
    assert config.client_name == "CLIENT_A"
    assert config.prompts_dir == Path("/tmp/p")
    assert config.skills_dir == Path("/tmp/s")


def test_from_env_requires_model_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_ANTHROPIC", "claude-id")  # MODEL_KIMI intentionally missing

    with pytest.raises(RuntimeError, match="MODEL_KIMI"):
        OrchestrationConfig.from_env()


def test_config_is_frozen() -> None:
    config = _config()
    with pytest.raises((AttributeError, TypeError)):
        config.client_name = "changed"  # type: ignore[misc]


def test_build_model_provider_uses_injected_config() -> None:
    provider = bootstrap.build_model_provider(_config())

    # active_model comes straight from the injected config, not the environment.
    assert provider.active_model_name == "anthropic"


def test_build_tracer_uses_injected_config() -> None:
    # No credentials in the injected config => tracing runs in no-op mode.
    tracer = bootstrap.build_tracer(_config())

    assert tracer.is_enabled is False


def test_build_selection_pipeline_needs_no_environment() -> None:
    # Nothing is set in the environment (autouse fixture cleared it); building the
    # agentic pipeline must still succeed purely from the injected config.
    pipeline = bootstrap.build_selection_pipeline(_config())

    assert isinstance(pipeline, SelectionPipeline)
