# Developer Guide — Orchestrating the F2F Audit Library (moved)

> **This guide has been superseded.** The single authoritative, end-to-end reuse
> document is now [`external-orchestration-guide.md`](./external-orchestration-guide.md).
> It covers construction via `OrchestrationConfig`, the full six-stage pipeline
> (POC → F2F → Merge → Filter → Selection → Final Audit), the Temporal activity
> mapping, persistence conventions, the failure model, and a complete runnable
> example.

## Quick API reference

```python
from e5_f2f_audit import (
    OrchestrationConfig, ModelConfig, TracingConfig, ConcurrencyConfig,
    build_poc_pipeline, build_f2f_pipeline, build_selection_pipeline,
    MergeEncountersEngine, TransactionOutputs, build_merge_encounters_payload,
    filter_candidates, FinalAuditEngine, build_final_audit_engine,
)
from e5_f2f_audit.core.result_store import ResultStore
from e5_f2f_audit.pipelines.poc_pipeline import POCClassificationError
```

| Stage | Entry point | Kind |
|---|---|---|
| POC | `build_poc_pipeline(config).run(...)` → `AnchorSet` | agentic (async) |
| F2F | `build_f2f_pipeline(config).run(...)` → `dict` | agentic (async) |
| Merge | `MergeEncountersEngine().build(TransactionOutputs.from_mapping(payload), generated_at=...)` | pure |
| Filter | `filter_candidates(merge_encounters, classification_roster)` | pure |
| Selection | `build_selection_pipeline(config).run(..., soc_date=...)` → `AgentOutput` | agentic (async) |
| Final Audit | `build_final_audit_engine().build(merge_encounters, selection, generated_at=...)` | pure |

See [`external-orchestration-guide.md`](./external-orchestration-guide.md) for full
signatures, the DICT contract, config details, and the Temporal mapping.

## Related docs

- [`pipeline-flow.md`](./pipeline-flow.md) — class-level flow across all six stages.
- [`encounter-selection-flow.md`](./encounter-selection-flow.md) — filter + ranking logic.
- [`integration-and-failure-handling.md`](./integration-and-failure-handling.md) — retries, soft/hard failures, PASS logic.
- [`agent-status-reference.md`](./agent-status-reference.md) — verdict/status vocabulary.
