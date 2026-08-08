# f2f-orchestration

Face-to-Face (F2F) / Plan-of-Care (POC) home-health audit agent orchestration.

The package layers into pure primitives (deterministic, I/O-free transforms) and
agentic pipelines (LLM agents built from an injected config). Bundled `prompts/`
and `skills/` ship inside the package, so an installed wheel is self-contained.

## Requirements

- Python >= 3.12

## Install

Local development (recommended — keeps the batch entrypoints working against the
repo's `ocr-markdown/`, `outputs/`, and `soc_dates.json`):

```bash
pip install -e ".[dev]"
```

As a dependency in another project:

```bash
pip install f2f-orchestration
```

## Running the batch entrypoints

Either the module form or the installed console scripts work:

```bash
python -m f2f_orchestration.run_poc      # or: f2f-poc
python -m f2f_orchestration.run_f2f      # or: f2f-f2f
python -m f2f_orchestration.run_merge_encounters  # or: f2f-merge
python -m f2f_orchestration.run_selection         # or: f2f-select
python -m f2f_orchestration.run_audit             # or: f2f-audit
```

Configure each run by editing the `RUN_MODE` / `SELECTED_TRANSACTIONS` block at the
top of the respective `run_*.py`.

## Using the library from another orchestrator (e.g. Temporal)

Build the agentic pipelines from an injected `OrchestrationConfig` (no environment
required) and drive the pure engines directly:

```python
from f2f_orchestration import (
    OrchestrationConfig, ModelConfig,
    build_selection_pipeline, MergeEncountersEngine, TransactionOutputs,
    filter_candidates, FinalAuditEngine,
)

config = OrchestrationConfig(
    model=ModelConfig(active_model="anthropic", kimi_model_id=..., anthropic_model_id=...),
)
selection = build_selection_pipeline(config)

merged = MergeEncountersEngine().build(
    TransactionOutputs.from_mapping(agent_outputs), generated_at=now
)
valid, excluded = filter_candidates(merged, classification_roster)
audit = FinalAuditEngine().build(merged, selection_output, generated_at=now)
```

## Configuration

`OrchestrationConfig.from_env()` reads the environment with documented defaults
(`MODEL_KIMI`, `MODEL_ANTHROPIC`, `ACTIVE_MODEL`, `LANGFUSE_*`, `MAX_CONCURRENT_AGENTS`,
`PROMPTS_DIR`, `SKILLS_DIR`, `CLIENT_NAME`, ...). External callers can instead build
the config object directly. Tier-3 I/O paths (`OCR_MARKDOWN_DIR`, `OUTPUTS_DIR`,
`SOC_DATES_FILE`, `PERSIST_TO_DISK`) are read by the local batch entrypoints.

## Tests

```bash
pytest
```
