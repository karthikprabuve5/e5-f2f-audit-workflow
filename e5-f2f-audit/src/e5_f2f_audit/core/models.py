"""Bedrock model provisioning.

``ModelProvider`` provisions both the ``kimi`` and ``anthropic`` models and
exposes the globally-selected ``active`` one. Every value (model ids, provider
names, temperature, client tuning) is a required argument — no defaults — so the
caller always supplies them (``os.getenv`` at the entrypoint locally, an upstream
layer in production). All models share one botocore ``Config`` enabling adaptive
retries and generous timeouts: the client-side layer of rate-limit protection.
"""

from __future__ import annotations

from typing import Literal, get_args

from botocore.config import Config
from langchain_aws import ChatBedrockConverse

from .logging_setup import get_logger

logger = get_logger(__name__)

ModelName = Literal["kimi", "anthropic"]


class ModelProvider:
    """Builds and caches ``ChatBedrockConverse`` instances from plain arguments."""

    def __init__(
        self,
        *,
        active_model: ModelName,
        kimi_model_id: str,
        anthropic_model_id: str,
        kimi_provider: str,
        anthropic_provider: str,
        temperature: float,
        read_timeout_seconds: int,
        connect_timeout_seconds: int,
        max_attempts: int,
        retry_mode: str,
    ) -> None:
        self._validate(active_model, kimi_model_id, anthropic_model_id)

        self._active_model: ModelName = active_model
        self._temperature = temperature
        self._model_ids: dict[ModelName, str] = {
            "kimi": kimi_model_id,
            "anthropic": anthropic_model_id,
        }
        self._providers: dict[ModelName, str] = {
            "kimi": kimi_provider,
            "anthropic": anthropic_provider,
        }
        self._boto_config = Config(
            read_timeout=read_timeout_seconds,
            connect_timeout=connect_timeout_seconds,
            retries={"max_attempts": max_attempts, "mode": retry_mode},
        )
        self._cache: dict[ModelName, ChatBedrockConverse] = {}

    @property
    def active_model_name(self) -> ModelName:
        return self._active_model

    def get(self, model_name: ModelName) -> ChatBedrockConverse:
        """Return the model for ``model_name``, building it once and caching it."""
        if model_name not in self._model_ids:
            available = ", ".join(self._model_ids)
            raise ValueError(f"Unknown model '{model_name}'. Available models: {available}.")

        if model_name not in self._cache:
            self._cache[model_name] = self._build_model(model_name)
        return self._cache[model_name]

    def active(self) -> ChatBedrockConverse:
        """Return the globally selected model (``active_model``)."""
        return self.get(self._active_model)

    def _build_model(self, model_name: ModelName) -> ChatBedrockConverse:
        provider = self._providers[model_name]
        logger.debug(
            "Building Bedrock model",
            extra={"model_name": model_name, "provider": provider},
        )
        return ChatBedrockConverse(
            model=self._model_ids[model_name],
            provider=provider,
            temperature=self._temperature,
            config=self._boto_config,
        )

    @staticmethod
    def _validate(active_model: ModelName, kimi_model_id: str, anthropic_model_id: str) -> None:
        allowed: tuple[ModelName, ...] = get_args(ModelName)
        if active_model not in allowed:
            raise ValueError(
                f"Invalid active_model '{active_model}'. Expected one of {allowed}."
            )
        if not kimi_model_id:
            raise ValueError("kimi_model_id must be a non-empty string.")
        if not anthropic_model_id:
            raise ValueError("anthropic_model_id must be a non-empty string.")
