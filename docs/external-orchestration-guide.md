# External Orchestration Guide — Reusing the `e5_f2f_audit` Pipeline

This is the authoritative guide for a **consumer package** (a Temporal worker, a
FastAPI service, another repo) that imports `e5_f2f_audit` as a library and drives
the whole F2F/POC audit pipeline itself — construction, orchestration, persistence,
and retries.

The library owns *document → agent → contract* processing. **You** own the event
loop, the sink (S3/DB), batch-level retries, and the runtime inputs (`soc_date`,
`client_name`, the F2F classification roster).

---

## 1. The six stages (and the DICT contract)

```
POC.md ─▶ PocPipeline.run() ─────────────▶ AnchorSet  (+ poc_store.results = DICT 1)
                                  │ anchors
F2F.md ─▶ F2fPipeline.run() ──────────────▶ f2f_store.results            = DICT 2
                                  │ build_merge_encounters_payload(DICT 1, DICT 2)
              MergeEncountersEngine.build() ▶ merge_encounters           = DICT 3
                                  │ filter_candidates(DICT 3, roster)
              (valid_candidates, excluded_encounters)
                                  │ SelectionPipeline.run(valid, soc_date, excluded)
              AgentOutput.processed ───────▶ selection                   = DICT 4
                                  │ FinalAuditEngine.build(DICT 3, DICT 4)
              audit ───────────────────────▶ final audit                 = DICT 5
```

Two kinds of stages:

| Kind | Stages | Properties |
|---|---|---|
| **Agentic** (Tier 2) | POC, F2F, Selection | `async`, call AWS Bedrock, traced, auto-retry. Non-deterministic → Temporal **activities**, never workflow code. |
| **Pure** (Tier 1) | Merge, Filter, Final Audit | Sync, no I/O, no clock (`generated_at` injected), no env, inputs never mutated. Safe anywhere, including a Temporal activity. |

**Ordering is mandatory:** POC → F2F (F2F needs the POC `AnchorSet`) → Merge → Filter
→ Selection → Final Audit. Filter and Selection are optional; Final Audit requires a
Selection result.

> **Final Audit consumes the *full* merge (DICT 3), not the filtered candidate set.**
> The filter only narrows what Selection *ranks*; the audit remains a lossless
> superset of every encounter plus the selection headline fields.

---

## 2. Install

```bash
pip install e5-f2f-audit          # distribution name (import name: e5_f2f_audit)
```

- Python **>= 3.12**.
- `prompts/` and `skills/` ship **inside** the wheel (package data), so the agentic
  layer is self-contained — no source checkout needed. Override their locations with
  `PROMPTS_DIR` / `SKILLS_DIR` only if you must.
- Runtime datasets (`ocr-markdown/`, `outputs/`, `soc_dates.json`) are **not** shipped
  — a library consumer holds documents in memory and persists results to its own sink.

---

## 3. Public API

```python
from e5_f2f_audit import (
    # Config (Tier 2 construction — no environment required)
    OrchestrationConfig, ModelConfig, TracingConfig, ConcurrencyConfig,
    # Agentic pipeline builders (take an OrchestrationConfig)
    build_poc_pipeline, build_f2f_pipeline, build_selection_pipeline,
    # Pure engines / helpers
    MergeEncountersEngine, TransactionOutputs, build_merge_encounters_payload,
    filter_candidates, FinalAuditEngine, build_final_audit_engine,
)
```

A few types are imported from submodules (they are not re-exported at top level):

| What | Import |
|---|---|
| In-memory result store | `from e5_f2f_audit.core.result_store import ResultStore` |
| POC classification gate error | `from e5_f2f_audit.pipelines.poc_pipeline import POCClassificationError` |
| Pipeline classes (advanced) | `from e5_f2f_audit.pipelines.{poc,f2f,selection}_pipeline import ...` |
| Anchors (only if you build them yourself) | `from e5_f2f_audit.core.anchors import AnchorSet` |

---

## 4. Configuration — `OrchestrationConfig`

All Tier-2 configuration is a single frozen, composed object. Build it however you
like — literals, a settings model, a secrets manager — and pass it to the builders.
No environment variables are required.

```python
from e5_f2f_audit import OrchestrationConfig, ModelConfig, TracingConfig, ConcurrencyConfig

config = OrchestrationConfig(
    model=ModelConfig(
        active_model="anthropic",              # or "kimi"
        kimi_model_id="<bedrock-model-id>",
        anthropic_model_id="<bedrock-model-id>",
        # defaults shown for completeness:
        kimi_provider="moonshotai", anthropic_provider="anthropic",
        temperature=0.0, read_timeout_seconds=1000, connect_timeout_seconds=60,
        max_attempts=5, retry_mode="adaptive",
    ),
    tracing=TracingConfig(                      # omit → tracing disabled (no-op)
        public_key=None, secret_key=None, host="https://cloud.langfuse.com",
    ),
    concurrency=ConcurrencyConfig(
        max_concurrent_agents=5, launch_stagger_seconds=0.0,
        max_retries=6, retry_base_delay_seconds=1.0, retry_max_delay_seconds=30.0,
    ),
    client_name="DEFAULT",
    # prompts_dir / skills_dir default to the bundled package data.
)
```

Only `model.active_model` + the two Bedrock ids are mandatory; everything else has a
default. `OrchestrationConfig.from_env()` exists for local dev (reads `MODEL_KIMI`,
`MODEL_ANTHROPIC`, `ACTIVE_MODEL`, `LANGFUSE_*`, `MAX_CONCURRENT_AGENTS`, `CLIENT_NAME`,
…) but an external package should construct the object directly.

Build the collaborators from the config:

```python
from e5_f2f_audit import build_poc_pipeline, build_f2f_pipeline, build_selection_pipeline

poc_pipeline = build_poc_pipeline(config)
f2f_pipeline = build_f2f_pipeline(config)
selection_pipeline = build_selection_pipeline(config)   # optional stage
```

> The three agentic pipelines share one constructor. A single set is safe to reuse
> across transactions (a fresh deep agent is built per run).

---

## 5. The in-memory `ResultStore`

`ResultStore.results` is always populated in memory; disk mirroring is toggled by
`persist_to_disk`. A library consumer that persists to its own sink disables disk:

```python
from pathlib import Path
from e5_f2f_audit.core.result_store import ResultStore

# outputs_dir is IGNORED when persist_to_disk=False — pass any placeholder Path.
store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
```

Shape of `store.results` (processed + raw + soft errors, all in memory):

```python
{
  "transaction_id": "...",
  "classification": {"f2f": {...}, "poc": {...}},
  "poc_485_extraction": {...} | None,
  "encounters": {1: {"encounter-identity": {...}, "homebound": {...}, ...}, 2: {...}},
  "summary": {...} | None,
  "merge_encounters": {...} | None,
  "selection": {...} | None,
  "audit": {...} | None,
  "raw": {"classification": {...}, "poc_485_extraction": {...}, "encounters": {...}, "selection": {...}},
  "errors": [{"encounter_index": 3, "agent": "homebound", "error_type": "AgentOutputError", "message": "..."}],
}
```

---

## 6. Stage-by-stage

### Stage 1 — POC (DICT 1)

```python
anchors = await poc_pipeline.run(
    transaction_id=transaction_id,
    poc_document_content=poc_markdown,     # you load the POC.md text
    client_name=config.client_name,
    result_store=poc_store,
)
poc_results = poc_store.results            # DICT 1
```

- Returns an `AnchorSet` (required by F2F). The POC *dict* is `poc_store.results`.
- Raises `POCClassificationError` if the POC has no `poc_485` / `2.1` encounter —
  catch per transaction so one bad document does not abort the batch.

### Stage 2 — F2F (DICT 2)

```python
f2f_results = await f2f_pipeline.run(
    transaction_id=transaction_id,
    f2f_document_content=f2f_markdown,     # you load the F2F.md text
    anchors=anchors,                       # from Stage 1
    result_store=f2f_store,
)                                          # == f2f_store.results (DICT 2)
```

Holds `classification.f2f`, the per-encounter `encounters` map, and the `summary`
roll-up (agent counts, soft failures, validation signals).

### Stage 3 — Merge encounters (DICT 3, pure)

```python
from datetime import UTC, datetime
from e5_f2f_audit import MergeEncountersEngine, TransactionOutputs, build_merge_encounters_payload

payload = build_merge_encounters_payload(
    poc_results, f2f_results, transaction_id=transaction_id, client_id=config.client_name
)
merge_encounters = MergeEncountersEngine().build(
    TransactionOutputs.from_mapping(payload), generated_at=datetime.now(UTC).isoformat()
)
```

`build_merge_encounters_payload` adapts the two pipeline dicts (including transposing
`encounters` from `{enc: {agent}}` to `{agent: {enc}}`) — you do not write that glue.

### Stage 4 — Filter referral/supporting-only encounters (pure, optional)

Deterministically removes supporting-only encounters (currently `referral_documents`)
from the *selection candidate set* before ranking. Runs before Selection.

```python
from e5_f2f_audit import filter_candidates

valid_candidates, excluded_encounters = filter_candidates(
    merge_encounters,                          # DICT 3
    f2f_results["classification"]["f2f"],      # the F2F classification roster
)
```

- Returns `(valid_candidates, excluded_encounters)`. `valid_candidates` is a deep copy
  of the merge with excluded indices pruned from each topic's `f2f_encounters`
  (`poc_485` blocks untouched). `excluded_encounters` is a list of
  `{encounter_index, encounter_category, encounter_subcategory, reason}`.
- Inputs are never mutated. If you skip this stage, pass `merge_encounters` straight to
  Selection and `excluded_encounters=None`.

### Stage 5 — Encounter selection (DICT 4, agentic, optional)

Picks the single best F2F encounter. Transaction-level (runs once), does not
re-validate — it ranks the already-validated merge verdicts. Needs a runtime
`soc_date` (the SOC-90 … SOC+30 window is computed from it) and reuses `client_name`.

```python
selection_output = await selection_pipeline.run(
    transaction_id=transaction_id,
    merge_encounters=valid_candidates,     # filtered set from Stage 4 (or DICT 3)
    soc_date="2026-07-15",                  # REQUIRED (ISO date)
    client_name=config.client_name,
    excluded_encounters=excluded_encounters,  # recorded verbatim in the output
)
selection = selection_output.processed      # DICT 4
```

- Returns an `AgentOutput` (`.processed` + `.raw` + `.validation`), **not** a store dict.
- `soc_date` and `client_name` are **required** — blank/absent raises `ValueError`
  before any agent runs (fail-fast; fix the input, do not retry blindly).
- Key output fields (`selection["result"]`): `best_encounter_index`,
  `best_encounter_score` (0–100, advisory), `best_is_date_aligned`,
  `date_aligned_encounter`, `decision` (`SELECTED` | `NEEDS_HUMAN_REVIEW` |
  `NO_ELIGIBLE_ENCOUNTER`), `excluded_encounters`, plus per-encounter alignment. The
  top-level `selection["reasoning"]["summary"]` is the auditor-voice narrative.
- Persist with `store.store_selection(selection_output.processed, raw=selection_output.raw)`.

### Stage 6 — Final audit (DICT 5, pure, optional)

Assembles the final contract: the **identical merge format with every encounter
retained** (lossless), prefixed inside `results` with the selection headline fields.

```python
from e5_f2f_audit import build_final_audit_engine   # or FinalAuditEngine()

audit = build_final_audit_engine().build(
    merge_encounters,          # DICT 3 (the FULL merge, not the filtered set)
    selection,                 # DICT 4
    generated_at=datetime.now(UTC).isoformat(),
)
```

The top of `audit["results"]` carries: `best_encounter_index`, `best_encounter_score`,
`best_is_date_aligned`, `date_aligned_encounter`, `excluded_encounters`, and
`encounter_selection_summary` (the selection's `reasoning.summary`), followed by the
unchanged topic blocks. Persist with `store.store_audit(audit)`.

---

## 7. Temporal mapping

| Stage | Activity? | Notes |
|---|---|---|
| POC / F2F / Selection | **Activity** | Agentic, async, non-deterministic (Bedrock). Build the pipeline from `OrchestrationConfig` inside the activity (or a worker singleton). |
| Merge / Filter / Final Audit | **Activity** (pure) | Deterministic, JSON-in/JSON-out, `generated_at` injected by the caller. Trivially unit-testable. |

Guidelines:
- Pass **plain dicts** across activity boundaries — every stage input/output is
  JSON-serializable (`AnchorSet` is the one exception; either keep POC+F2F in one
  activity, or rebuild anchors from the POC extraction via
  `AnchorSet.from_poc_extraction(poc_extraction, client_name=...)`).
- Inject `generated_at` (and any clock/id) from the workflow so the pure stages stay
  deterministic on replay.
- Own persistence in the activity or a dedicated sink activity — the library never
  writes when `persist_to_disk=False`.

---

## 8. Persistence & artifact conventions

With `persist_to_disk=False` the library never touches your filesystem; you capture
each dict and store it. The local batch entrypoints use this on-disk layout (mirror it
in your sink if useful):

| Artifact | Source dict | Batch path |
|---|---|---|
| POC / F2F classification | `results["classification"]` | `classification/{poc,f2f}.json` |
| POC 485 extraction (+ raw) | `results["poc_485_extraction"]` | `poc_485_extraction/results.json` |
| Per-encounter agent outputs | `results["encounters"]` | `<agent>/encounter_<i>.json` (+ `-raw`) |
| Run summary | `results["summary"]` | `_summary-results.json` |
| Merge encounters | DICT 3 | `merge-encounters/results.json` |
| Selection (+ raw) | DICT 4 | `encounter-selection/results.json` |
| Final audit | DICT 5 | `audit/results.json` |

Serialize with `json.dumps(..., default=str)` (matches `ResultStore._write`).

---

## 9. Failure model (summary)

- **Hard failures** raise out of `run()` — `POCClassificationError`, a
  classification/extraction agent failing outright, or `ValueError` for a missing
  `soc_date`/`client_name`. Wrap each transaction in try/except so one failure never
  aborts the batch.
- **Soft failures** are isolated and recorded: a single F2F agent (or whole encounter)
  failing lands in `results["errors"]` and `data_quality` while the run still succeeds.
- The pure stages fail loudly on malformed input (e.g. `transaction_id` mismatch
  between merge and selection in Final Audit) — never silently.

Full case-by-case behavior, retry policy, and PASS/incomplete logic live in
[`integration-and-failure-handling.md`](./integration-and-failure-handling.md). Agent
verdict/status vocabulary is in [`agent-status-reference.md`](./agent-status-reference.md).
The selection ranking logic is diagrammed in
[`encounter-selection-flow.md`](./encounter-selection-flow.md); the class-level flow in
[`pipeline-flow.md`](./pipeline-flow.md).

---

## 10. Full end-to-end example

```python
import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from e5_f2f_audit import (
    OrchestrationConfig, ModelConfig,
    build_poc_pipeline, build_f2f_pipeline, build_selection_pipeline,
    build_final_audit_engine,
    MergeEncountersEngine, TransactionOutputs, build_merge_encounters_payload,
    filter_candidates,
)
from e5_f2f_audit.core.result_store import ResultStore
from e5_f2f_audit.pipelines.poc_pipeline import POCClassificationError


def build_config() -> OrchestrationConfig:
    return OrchestrationConfig(
        model=ModelConfig(
            active_model="anthropic",
            kimi_model_id="<bedrock-model-id>",
            anthropic_model_id="<bedrock-model-id>",
        ),
        client_name="DEFAULT",
    )


async def orchestrate_one(
    config: OrchestrationConfig,
    transaction_id: str,
    poc_markdown: str,
    f2f_markdown: str,
    soc_date: str,
) -> dict[str, Any]:
    poc_pipeline = build_poc_pipeline(config)
    f2f_pipeline = build_f2f_pipeline(config)
    selection_pipeline = build_selection_pipeline(config)
    now = datetime.now(UTC).isoformat()

    # 1) POC → anchors + DICT 1
    poc_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
    try:
        anchors = await poc_pipeline.run(
            transaction_id=transaction_id,
            poc_document_content=poc_markdown,
            client_name=config.client_name,
            result_store=poc_store,
        )
    except POCClassificationError:
        raise  # not a plan of care — handle per transaction
    poc_results = poc_store.results

    # 2) F2F → DICT 2
    f2f_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
    f2f_results = await f2f_pipeline.run(
        transaction_id=transaction_id,
        f2f_document_content=f2f_markdown,
        anchors=anchors,
        result_store=f2f_store,
    )

    # 3) Merge → DICT 3
    payload = build_merge_encounters_payload(
        poc_results, f2f_results, transaction_id=transaction_id, client_id=config.client_name
    )
    merge_encounters = MergeEncountersEngine().build(
        TransactionOutputs.from_mapping(payload), generated_at=now
    )

    # 4) Filter referral/supporting-only → candidate set + excluded
    valid_candidates, excluded = filter_candidates(
        merge_encounters, f2f_results["classification"]["f2f"]
    )

    # 5) Selection → DICT 4
    selection_output = await selection_pipeline.run(
        transaction_id=transaction_id,
        merge_encounters=valid_candidates,
        soc_date=soc_date,
        client_name=config.client_name,
        excluded_encounters=excluded,
    )
    selection = selection_output.processed

    # 6) Final audit → DICT 5 (uses the FULL merge + selection)
    audit = build_final_audit_engine().build(merge_encounters, selection, generated_at=now)

    # (Your code) push poc_results / f2f_results / merge_encounters / selection / audit to your sink.
    return {"merge_encounters": merge_encounters, "selection": selection, "audit": audit}


if __name__ == "__main__":
    result = asyncio.run(
        orchestrate_one(
            build_config(), "transaction_demo",
            poc_markdown="...", f2f_markdown="...", soc_date="2026-07-15",
        )
    )
    results = result["audit"]["results"]
    print(results["best_encounter_index"], results["best_encounter_score"])
    print(results["encounter_selection_summary"])
```

---

## 11. Gotchas

- **POC returns an `AnchorSet`, not a dict.** Read the dict from `poc_store.results`;
  pass the `AnchorSet` into F2F. Ordering (POC → F2F) is mandatory.
- **Async pipelines, sync engines.** `await` the POC/F2F/Selection `run(...)`; call
  `MergeEncountersEngine.build`, `filter_candidates`, and `FinalAuditEngine.build`
  directly.
- **Final Audit takes the full merge (DICT 3), Selection takes the filtered set.**
  Don't swap them.
- **`soc_date` / `client_name` are required for Selection** (runtime args, not env).
- **`transaction_id` is yours** — pass a stable id.
- **Config injection is the contract.** Build `OrchestrationConfig` explicitly; env is
  a local-dev convenience only.
```
