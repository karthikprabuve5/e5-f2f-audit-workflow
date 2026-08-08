# e5-f2f-audit-workflow

Face-to-Face (F2F) / Plan-of-Care (POC) home-health audit agent orchestration.

The Python package lives in [`e5-f2f-audit/`](./e5-f2f-audit/) (distribution
`e5-f2f-audit`, import `e5_f2f_audit`, src-layout). This repo root additionally holds
the shared runtime datasets used by the local batch entrypoints.

## Repository layout

| Path | What |
|---|---|
| [`e5-f2f-audit/`](./e5-f2f-audit/) | The installable package (src-layout, bundled `prompts/` + `skills/`) — **see its [README](./e5-f2f-audit/README.md)** |
| [`docs/`](./docs/) | Architecture, reuse, and failure-handling documentation |
| `ocr-markdown/` | Input OCR markdown documents (batch runs) |
| `outputs/` | Per-transaction results written by the batch entrypoints |
| `soc_dates.json` | `transaction_id → soc_date` map for encounter selection |
| `requirements.txt` | Runtime dependency list (mirrors the package `pyproject.toml`) |

## Getting started

Everything — install, configuration, the six-stage pipeline, the batch CLIs, outputs
layout, library reuse, and the full env reference — is documented in the package README:

**➡ [`e5-f2f-audit/README.md`](./e5-f2f-audit/README.md)**

Quick version:

```bash
pip install -e "e5-f2f-audit[dev]"     # install the package (editable)
cd e5-f2f-audit && cp .env.example .env  # configure, then fill in MODEL_* / AWS / LANGFUSE_*
python -m e5_f2f_audit.run_poc          # run a stage (or: f2f-poc)
```

## Documentation

- [External orchestration guide](./docs/external-orchestration-guide.md) — authoritative end-to-end reuse (config, six stages, Temporal, runnable example).
- [Pipeline flow](./docs/pipeline-flow.md) — class-level call flow.
- [Encounter selection flow](./docs/encounter-selection-flow.md) — referral filter + best-encounter ranking.
- [Integration & failure handling](./docs/integration-and-failure-handling.md) — orchestration contract + every failure case.
- [Agent status reference](./docs/agent-status-reference.md) — per-agent status/verdict vocabulary.
