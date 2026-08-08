# F2F Audit — Agent Orchestration

Production-style orchestration of the F2F audit deep agents, with end-to-end
Langfuse tracing. Two pipelines share one agent factory and one tracing layer:

- **POC pipeline** (anchor): `classification(POC.md)` → `poc_485_extraction(POC.md)`
  → produces the **anchor values** consumed by every F2F agent.
- **F2F pipeline** (main): `classification(F2F.md)` → split into encounters →
  for **each encounter in parallel**, run the per-encounter agents **in parallel**.

## Execution flow

```
run_poc.py  → PocPipeline:  classification(POC.md) → poc_485_extraction → anchors
              (anchors saved to outputs/<transaction_id>/poc_485_extraction/results.json)

run_f2f.py  → reads the saved POC anchors from disk → F2fPipeline:
                classification(F2F.md) → split encounters
                → per encounter [parallel]:
                    encounter_identity, primary_diagnosis, skilled_services,
                    homebound, inpatient_detection
                    + telehealth_identity   (only if telehealth encounter)
                    + surgical_note         (only if operative/procedural encounter)
```

`run_poc` and `run_f2f` are independent: run POC once, then iterate F2F on its
own (it reuses the saved anchors), which keeps local development fast.

Telehealth / surgical agents are auto-selected per encounter from the
classification output (`encounter_category` + `classification_notes`) — no manual flags.

## Layout

There is no config object. Every value a pipeline needs is passed as a
constructor argument. Locally the entrypoints source these from `os.getenv(...)`
(after `load_dotenv()`); in production an upstream layer passes them directly.

| Path | Responsibility |
|------|----------------|
| `core/models.py` | Builds the `kimi` and `anthropic` Bedrock models from plain args |
| `core/tracing.py` | Langfuse v4 handler + nested spans for one end-to-end trace tree |
| `core/prompts.py` | Loads a system prompt and injects anchor placeholders |
| `core/anchors.py` | Maps `poc_485` output → prompt placeholders |
| `core/encounter_splitter.py` | Splits a document into per-encounter chunks |
| `core/detection.py` | Auto-selects telehealth / surgical agents per encounter |
| `core/result_store.py` | In-memory results dict + JSON writer |
| `core/document_source.py` | `DocumentSource` protocol + local file loader |
| `agents/agent_factory.py` | All deep agents defined in one file |
| `pipelines/` | `base_pipeline`, `poc_pipeline`, `f2f_pipeline` |
| `bootstrap.py` | Reads `os.getenv`, builds the collaborators/pipelines (shared wiring) |
| `run_poc.py` / `run_f2f.py` | Entrypoints (FULL / SELECTED run modes) |
| `tests/` | Unit tests for the deterministic modules |

## Setup

```bash
pip install -r requirements.txt
```

For local/dev, copy `env.example` to `.env` and fill it in (the file is named
`env.example` rather than `.env.example` because the repo `.cursorignore`
ignores `.env.*`):

```bash
cp env.example .env
```

There is no config object or `Settings`. `bootstrap.py` is the only place that
reads the environment (via `load_dotenv()` + `os.getenv(...)`) and passes those
values straight into the module constructors. In production, an upstream layer
supplies the same values and `bootstrap` is bypassed.

## Run

The entrypoints are configured in code (no CLI arguments). Edit the config block
at the top of `run_poc.py` / `run_f2f.py`:

```python
RUN_MODE = RunMode.SELECTED        # or RunMode.FULL
SELECTED_TRANSACTIONS = ["transaction_anzaldua_esther"]
```

- **`FULL`** — run every transaction found under `ocr-markdown/` (must contain the
  relevant doc), one by one.
- **`SELECTED`** — run only the transactions listed in `SELECTED_TRANSACTIONS`.

Then, from the repo root:

```bash
python -m f2f_orchestration.run_poc     # extract + save anchors
python -m f2f_orchestration.run_f2f     # audit using the saved anchors
```

Input documents are read from `ocr-markdown/<transaction_id>/{POC.md,F2F.md}`.
Transactions run sequentially; a failing transaction is logged and skipped, and a
batch report (`succeeded` / `failed`) is emitted at the end. Every run is traced
in Langfuse, grouped by `transaction_id`.

## Outputs

Everything for a run lives under `outputs/<transaction_id>/`. Classification
(which runs on both documents) is a subfolder with one file per document. Each
per-encounter agent gets its own subfolder holding one file per encounter.

```
outputs/
└── <transaction_id>/
    ├── poc_485_extraction/
    │   └── results.json                              # anchor values (document-level)
    ├── classification/
    │   ├── f2f.json                                  # F2F classification
    │   └── poc.json                                  # POC classification
    ├── encounter_identity/
    │   └── encounter_<i>-results.json
    ├── primary_diagnosis/
    │   └── encounter_<i>-results.json
    ├── skilled_services/
    │   └── encounter_<i>-results.json
    ├── homebound/
    │   └── encounter_<i>-results.json
    ├── inpatient_detection/
    │   └── encounter_<i>-results.json
    ├── telehealth_identity/                          # only telehealth encounters
    │   └── encounter_<i>-results.json
    ├── surgical_note/                                # only operative encounters
    │   └── encounter_<i>-results.json
    ├── merge-encounters/
    │   └── results.json                              # consolidated merge_encounters contract
    ├── encounter-selection/
    │   └── results.json                              # best-encounter selection
    └── _summary-results.json                         # combined run manifest
```

### `_summary-results.json`

A single consolidated manifest for the whole transaction, so you never have to
open a dozen files to understand a run. It aggregates:

- **Run metadata** — `transaction_id`, timestamp, active model, client name,
  and the Langfuse `session_id` / trace id for one-click debugging.
- **POC section** — anchor values extracted and the POC/F2F classification counts.
- **Per-encounter roll-up** — for each encounter: its category, which agents ran
  (including auto-selected telehealth/surgical), each agent's status
  (`ok` / `failed`) and confidence, and the relative path to its result file.
- **Failures** — any agent that raised, with the error message and context
  (so a partial run is never silent).

It is the top-level index of the run: quick health check + pointers into the
individual per-agent result files.

## Traceability

Each run opens one Langfuse trace named by `transaction_id`, with nested spans:
`transaction → {poc pipeline → classification, poc_485} → {f2f pipeline →
classification → encounter_i → agent}`. Every agent call also carries
`langfuse_session_id`, tags, and a stable `run_name`, so any span is filterable
and easy to debug.
