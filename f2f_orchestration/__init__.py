"""F2F/POC audit orchestration package.

Public reuse surface for external orchestrators (Temporal workers, services, other
repos). The building blocks come in two flavours:

* Pure primitives — deterministic, I/O-free transforms usable anywhere:
  :class:`MergeEncountersEngine`, :func:`filter_candidates`, :class:`FinalAuditEngine`,
  and :class:`TransactionOutputs` (feed in-memory agent outputs without disk).
* Agentic pipeline builders — construct the LLM pipelines from an injected
  :class:`OrchestrationConfig` (no environment required):
  :func:`build_poc_pipeline`, :func:`build_f2f_pipeline`, :func:`build_selection_pipeline`.

Typical external wiring::

    config = OrchestrationConfig(model=ModelConfig(...), ...)
    selection = build_selection_pipeline(config)
    merged = MergeEncountersEngine().build(
        TransactionOutputs.from_mapping(payload), generated_at=now
    )
    valid, excluded = filter_candidates(merged, classification_roster)
    audit = FinalAuditEngine().build(merged, selection_output, generated_at=now)
"""

from .audit import FinalAuditEngine
from .bootstrap import (
    build_f2f_pipeline,
    build_final_audit_engine,
    build_poc_pipeline,
    build_selection_pipeline,
)
from .config import (
    ConcurrencyConfig,
    ModelConfig,
    OrchestrationConfig,
    TracingConfig,
)
from .core.encounter_filter import filter_candidates
from .merge_encounters import (
    MergeEncountersEngine,
    TransactionOutputs,
    build_merge_encounters_payload,
)

__all__ = [
    "OrchestrationConfig",
    "ModelConfig",
    "TracingConfig",
    "ConcurrencyConfig",
    "build_poc_pipeline",
    "build_f2f_pipeline",
    "build_selection_pipeline",
    "build_final_audit_engine",
    "MergeEncountersEngine",
    "TransactionOutputs",
    "build_merge_encounters_payload",
    "filter_candidates",
    "FinalAuditEngine",
]
