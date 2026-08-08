# Developer Guide — Orchestrating the F2F Audit Library

This guide is for a **consumer package** that imports `f2f_orchestration` as a
library and orchestrates the pipelines itself. Your layer:

1. Runs the **POC pipeline** in memory, captures the result as a `dict`.
2. Runs the **F2F pipeline** in memory, captures the result as a `dict`.
3. Feeds both into the **merge-encounters engine** and gets the `merge_encounters` `dict` back.
4. *(Optional)* Runs the **encounter-selection pipeline** over the `merge_encounters`
   to pick the single best F2F encounter. This stage needs a runtime `soc_date`.

You own orchestration, persistence (e.g. S3), retries at the batch level, and the
event loop. This library owns document→agent processing, the merge assembly, and
(optionally) the encounter selection.

---

## 1. The three-dict contract (+ optional selection)

```
POC.md ──▶ PocPipeline.run() ──▶ AnchorSet  (+ poc_store.results  = DICT 1)
                                     │
                                     ▼ anchors
F2F.md ──▶ F2fPipeline.run() ─────────────────▶ f2f_store.results = DICT 2
                                     │
                                     ▼ build_merge_encounters_payload(DICT 1, DICT 2)
                              MergeEncountersEngine.build() ──▶ merge_encounters = DICT 3
                                     │
                                     ▼ SelectionPipeline.run(merge_encounters, soc_date)   [optional]
                              AgentOutput.processed ──▶ selection = DICT 4
```

> **Ordering is mandatory:** F2F cannot run without the `AnchorSet` produced by
> POC. POC must complete first. Selection, when used, runs **last** — it consumes
> DICT 3 (`merge_encounters`) plus a runtime `soc_date`.

> **POC returns an `AnchorSet`, not a dict.** The POC *dict* is read from the
> `ResultStore` you passed in (`poc_store.results`). F2F returns its dict
> directly (it is the same `result_store.results` object).

> **Selection returns an `AgentOutput`, not a `ResultStore` dict.** DICT 4 is
> `AgentOutput.processed` (with `.raw` and `.validation` alongside). It is a
> deep-agent pipeline (async, Bedrock, traced) — unlike the pure `MergeEncountersEngine`.

---

## 2. Import map

| What you need | Import |
|---|---|
| POC pipeline | `from f2f_orchestration.pipelines.poc_pipeline import PocPipeline` |
| F2F pipeline | `from f2f_orchestration.pipelines.f2f_pipeline import F2fPipeline` |
| Selection pipeline (optional) | `from f2f_orchestration.pipelines.selection_pipeline import SelectionPipeline` |
| In-memory result store | `from f2f_orchestration.core.result_store import ResultStore` |
| Anchors (only if you build them yourself) | `from f2f_orchestration.core.anchors import AnchorSet` |
| Merge engine + input adapter + payload builder | `from f2f_orchestration.merge_encounters import MergeEncountersEngine, TransactionOutputs, build_merge_encounters_payload` |
| Env-based construction helpers | `from f2f_orchestration import bootstrap` |
| Env-free construction (advanced) | `ModelProvider`, `AgentFactory`, `PromptRenderer`, `LangfuseTracer` (see §4B) |

The top-level `f2f_orchestration/__init__.py` is intentionally empty — import from
the submodules above.

---

## 3. Prerequisites

- **Python / async** — both pipelines are `async`. Call them inside an event loop
  (`asyncio.run(...)` or an existing loop). `MergeEncountersEngine.build(...)` is **sync**.
- **Credentials** — agents call AWS Bedrock; Langfuse tracing is optional.
- **Model + tracing config** — supplied via env (§4A) or explicit args (§4B).
- **Bundled resources** — agents read prompt templates and skill folders from the
  filesystem. The package **must** ship the `prompts/` and `skills/` directories
  (or point `PROMPTS_DIR` / `SKILLS_DIR` at them). See §15 Packaging notes.
- **Selection inputs (optional stage)** — the encounter-selection pipeline takes a
  runtime **`soc_date`** and reuses **`client_name`**; both are passed as call
  arguments (not env). `soc_date` is **required** — a blank/absent value raises
  `ValueError`. No new environment variables are introduced.

Relevant environment variables (defaults in parentheses):

| Var | Purpose |
|---|---|
| `MODEL_KIMI`, `MODEL_ANTHROPIC` | **Required** Bedrock model ids |
| `ACTIVE_MODEL` (`kimi`) | Which model to use |
| `CLIENT_NAME` (`DEFAULT`) | Client id injected into prompts / audit |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | Tracing (optional) |
| `MAX_CONCURRENT_AGENTS` (`5`) | Global in-flight agent cap |
| `AGENT_LAUNCH_STAGGER_SECONDS` (`0.0`) | Spacing between launches |
| `AGENT_MAX_RETRIES` (`6`), `AGENT_RETRY_BASE_DELAY_SECONDS` (`1.0`), `AGENT_RETRY_MAX_DELAY_SECONDS` (`30.0`) | Throttling backoff |
| `PROMPTS_DIR`, `SKILLS_DIR`, `OUTPUTS_DIR` | Resource / output locations |
| `PERSIST_TO_DISK` (`true`) | Only relevant if you use `bootstrap.build_result_store()` |

---

## 4. Constructing the pipelines

### Option A — `bootstrap` (env-driven, recommended to start)

Easiest path: reuse the wiring that `run_poc` / `run_f2f` use. It reads all config
from the environment.

```python
from f2f_orchestration import bootstrap

bootstrap.load_environment()              # loads .env + configures logging
poc_pipeline = bootstrap.build_poc_pipeline()
f2f_pipeline = bootstrap.build_f2f_pipeline()
selection_pipeline = bootstrap.build_selection_pipeline()   # optional stage
client = bootstrap.client_name()          # from CLIENT_NAME env
```

You still create the **in-memory** `ResultStore` yourself (see §5) so nothing is
written to disk regardless of `PERSIST_TO_DISK`.

### Option B — env-free construction (clean library API)

For full control with no environment coupling, build the collaborators explicitly.
This mirrors `bootstrap._build_pipeline` but takes values from your own config.

```python
from pathlib import Path

from f2f_orchestration.core.models import ModelProvider
from f2f_orchestration.core.prompts import PromptRenderer
from f2f_orchestration.core.tracing import LangfuseTracer
from f2f_orchestration.agents.agent_factory import AgentFactory
from f2f_orchestration.pipelines.poc_pipeline import PocPipeline
from f2f_orchestration.pipelines.f2f_pipeline import F2fPipeline
from f2f_orchestration.pipelines.selection_pipeline import SelectionPipeline

model_provider = ModelProvider(
    active_model="kimi",
    kimi_model_id="...",           # your Bedrock model id
    anthropic_model_id="...",
    kimi_provider="moonshotai",
    anthropic_provider="anthropic",
    temperature=0.0,
    read_timeout_seconds=1000,
    connect_timeout_seconds=60,
    max_attempts=5,
    retry_mode="adaptive",
)

factory = AgentFactory(
    model_provider=model_provider,
    prompt_renderer=PromptRenderer(Path("prompts")),   # bundled prompts dir
    skills_root=Path("skills"),                         # bundled skills dir
)

tracer = LangfuseTracer(
    public_key=None, secret_key=None,        # None disables tracing
    host="https://cloud.langfuse.com",
    client_name="DEFAULT",
    active_model="kimi",
)

pipeline_kwargs = dict(
    agent_factory=factory,
    tracer=tracer,
    max_concurrent_agents=5,
    launch_stagger_seconds=0.0,
    max_retries=6,
    retry_base_delay_seconds=1.0,
    retry_max_delay_seconds=30.0,
)
poc_pipeline = PocPipeline(**pipeline_kwargs)
f2f_pipeline = F2fPipeline(**pipeline_kwargs)
selection_pipeline = SelectionPipeline(**pipeline_kwargs)   # optional stage
```

> All three pipelines share the `BasePipeline` constructor, so the kwargs are
> identical. A fresh `AgentFactory` builds a new deep agent per run, so one factory
> is safe to reuse across transactions.

---

## 5. The in-memory `ResultStore`

`ResultStore.results` is always populated in memory; disk mirroring is toggled by
`persist_to_disk`. For a library consumer that persists to S3 itself, disable disk:

```python
from pathlib import Path
from f2f_orchestration.core.result_store import ResultStore

# outputs_dir is IGNORED when persist_to_disk=False — pass any placeholder Path.
poc_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
```

The in-memory dict has this shape:

```python
{
  "transaction_id": "...",
  "classification": {"f2f": {...}, "poc": {...}},        # processed
  "poc_485_extraction": {...} | None,                    # processed
  "encounters": { 1: {"encounter-identity": {...}, "homebound": {...}, ...}, 2: {...} },  # processed
  "summary": {...} | None,
  "merge_encounters": {...} | None,
  "selection": {...} | None,                             # processed selection (DICT 4)

  "raw": {                                               # pre-normalization agent output
    "classification": {"f2f": {...}, "poc": {...}},
    "poc_485_extraction": {...} | None,
    "encounters": { 1: {"encounter-identity": {...}}, ... },
    "selection": {...} | None,
  },
  "errors": [ {"encounter_index": 3, "agent": "homebound",
               "error_type": "AgentOutputError", "message": "..."} ],  # soft failures
}
```

> **`selection` is only populated if you run Step 4** (see §9) and call
> `store_selection(...)`. On disk it lands at
> `outputs/<txn>/encounter-selection/results.json` (+ `results-raw.json`).

> **Processed + raw + errors are all in memory.** `.results` holds processed
> outputs, a mirrored `raw` tree (including unparseable raw strings), and a
> flattened `errors` list of the soft (isolated) failures. All three are available
> with `persist_to_disk=False` — ready to push to S3. See the failure model in
> [`integration-and-failure-handling.md`](./integration-and-failure-handling.md).

---

## 6. Step 1 — run the POC pipeline (DICT 1)

```python
poc_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)

anchors = await poc_pipeline.run(
    transaction_id=transaction_id,
    poc_document_content=poc_markdown,     # you load the POC.md text
    client_name=client,
    result_store=poc_store,
)

poc_results = poc_store.results            # DICT 1 — capture / send to S3
```

- Returns an `AnchorSet` (needed for F2F).
- Raises `POCClassificationError` if the POC has no `poc_485` / `2.1` encounter —
  catch it per transaction so one bad document does not abort your batch.

---

## 7. Step 2 — run the F2F pipeline (DICT 2)

```python
f2f_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)

f2f_results = await f2f_pipeline.run(
    transaction_id=transaction_id,
    f2f_document_content=f2f_markdown,     # you load the F2F.md text
    anchors=anchors,                       # from Step 1
    result_store=f2f_store,
)                                          # returns f2f_store.results == DICT 2
```

`f2f_results` contains `classification.f2f`, the per-encounter `encounters` map,
and the `summary` roll-up (agent counts, failures, validation signals).

---

## 8. Step 3 — adapt + run the merge-encounters engine (DICT 3)

The pipeline dicts do **not** match what `TransactionOutputs.from_mapping`
expects. The library ships the adapter for you — **import `build_merge_encounters_payload`**
from `f2f_orchestration.merge_encounters` (no need to write your own).

It performs this mapping:

| `from_mapping` key | Source in pipeline dicts |
|---|---|
| `transaction_id` | you pass it (or read from either dict) |
| `client_id` (optional) | you pass it; else derived from the outputs |
| `poc_extraction` | `poc_results["poc_485_extraction"]` |
| `classification_f2f` | `f2f_results["classification"]["f2f"]` |
| `agents` | **transpose** of `f2f_results["encounters"]`: `{enc: {agent: data}}` → `{agent: {enc: data}}` |

```python
from datetime import UTC, datetime

from f2f_orchestration.merge_encounters import (
    MergeEncountersEngine,
    TransactionOutputs,
    build_merge_encounters_payload,
)

# Assemble the merge_encounters dict (DICT 3)
payload = build_merge_encounters_payload(
    poc_results, f2f_results, transaction_id=transaction_id, client_id=client
)
outputs = TransactionOutputs.from_mapping(payload)
merge_encounters = MergeEncountersEngine().build(
    outputs, generated_at=datetime.now(UTC).isoformat()
)
```

`MergeEncountersEngine` is pure (no I/O, no clock, no env) — safe inside any orchestrator,
including a Temporal activity. `generated_at` is injected by you.

---

## 9. Step 4 (optional) — run the encounter-selection pipeline (DICT 4)

Once you have `merge_encounters` (DICT 3), you can pick the single best F2F encounter.
This stage is **optional** and runs **last**. It needs a runtime `soc_date` (the
90/30-day window is computed from it) and reuses `client_name`.

```python
from f2f_orchestration.pipelines.selection_pipeline import SelectionPipeline

# selection_pipeline built in §4 (bootstrap.build_selection_pipeline() or SelectionPipeline(**kwargs))
selection_output = await selection_pipeline.run(
    transaction_id=transaction_id,
    merge_encounters=merge_encounters,     # DICT 3 from Step 3
    soc_date="2026-07-15",           # REQUIRED runtime input (ISO date)
    client_name=client,
)

selection = selection_output.processed          # DICT 4 — capture / send to S3
best_index = selection["result"]["best_encounter_index"]
decision = selection["result"]["decision"]      # SELECTED | NEEDS_HUMAN_REVIEW | NO_ELIGIBLE_ENCOUNTER
```

- Returns an `AgentOutput` (`raw` + `processed` + `validation`) — **not** a
  `ResultStore` dict. DICT 4 is `selection_output.processed`.
- **`soc_date` and `client_name` are required** — a blank/absent value raises
  `ValueError` before any agent runs (fail-fast; fix the input, do not retry blindly).
- It is **transaction-level** (runs once per transaction, not per encounter) and
  does not re-validate the encounters — it selects from the already-validated
  `merge_encounters` verdicts.
- To keep it in your in-memory store (and optionally on disk), pass it to
  `ResultStore.store_selection(selection_output.processed, raw=selection_output.raw)`.

---

## 10. RAW + errors in memory (implemented)

`ResultStore` keeps **raw** and **errors** in memory alongside processed, so
`persist_to_disk=False` gives you everything for your S3 sink:

- `results["raw"]` — pre-normalization agent output, mirroring the processed layout
  (`classification` / `poc_485_extraction` / `encounters`). Unparseable agent output
  is captured here as a **string** (via the failed-agent path).
- `results["errors"]` — flattened soft failures `{encounter_index, agent,
  error_type, message}` (derived when the run summary is stored; `agent: None`
  denotes a whole-encounter failure).

Both are additive — the merge engine and existing consumers ignore them, and disk
output is unchanged. Access example:

```python
raw_homebound = f2f_results["raw"]["encounters"][2]["homebound"]
soft_failures = f2f_results["errors"]
```

For the full failure model (hard vs soft, every case, retry policy), see
[`integration-and-failure-handling.md`](./integration-and-failure-handling.md).

> Hard failures (e.g. `POCClassificationError`, a classification/extraction agent
> failing outright) are **not** in `errors` — they raise out of `run()` and are
> caught by your orchestrator.

---

## 11. Full end-to-end example

```python
import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from f2f_orchestration import bootstrap
from f2f_orchestration.core.result_store import ResultStore
from f2f_orchestration.pipelines.poc_pipeline import POCClassificationError
from f2f_orchestration.merge_encounters import (
    MergeEncountersEngine,
    TransactionOutputs,
    build_merge_encounters_payload,
)


async def orchestrate_one(
    transaction_id: str, poc_markdown: str, f2f_markdown: str, soc_date: str
) -> dict[str, Any]:
    bootstrap.load_environment()
    poc_pipeline = bootstrap.build_poc_pipeline()
    f2f_pipeline = bootstrap.build_f2f_pipeline()
    selection_pipeline = bootstrap.build_selection_pipeline()   # optional Step 4
    client = bootstrap.client_name()

    # 1) POC → anchors + DICT 1
    poc_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
    try:
        anchors = await poc_pipeline.run(
            transaction_id=transaction_id,
            poc_document_content=poc_markdown,
            client_name=client,
            result_store=poc_store,
        )
    except POCClassificationError:
        raise
    poc_results = poc_store.results

    # 2) F2F → DICT 2
    f2f_store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
    f2f_results = await f2f_pipeline.run(
        transaction_id=transaction_id,
        f2f_document_content=f2f_markdown,
        anchors=anchors,
        result_store=f2f_store,
    )

    # (Your code) push poc_results / f2f_results (incl. their "raw" subtrees) to S3 here.

    # 3) Merge encounters → DICT 3
    payload = build_merge_encounters_payload(
        poc_results, f2f_results, transaction_id=transaction_id, client_id=client
    )
    merge_encounters = MergeEncountersEngine().build(
        TransactionOutputs.from_mapping(payload),
        generated_at=datetime.now(UTC).isoformat(),
    )

    # 4) Selection (optional) → DICT 4  (needs the runtime soc_date)
    selection_output = await selection_pipeline.run(
        transaction_id=transaction_id,
        merge_encounters=merge_encounters,
        soc_date=soc_date,
        client_name=client,
    )
    selection = selection_output.processed
    # (Your code) push selection (+ selection_output.raw) to S3 here.

    return {"merge_encounters": merge_encounters, "selection": selection}


if __name__ == "__main__":
    result = asyncio.run(
        orchestrate_one(
            "transaction_demo", poc_markdown="...", f2f_markdown="...", soc_date="2026-07-15"
        )
    )
    merged = result["merge_encounters"]
    print(merged["results"].keys(), merged["data_quality"])
    print(result["selection"]["result"]["best_encounter_index"])
```

---

## 12. Alternative — a single shared `ResultStore`

You asked for two separate stores (POC dict + F2F dict). A simpler variant is to
pass **one** `ResultStore` to both pipelines. Then a single `.results` dict already
contains `poc_485_extraction`, `classification.f2f`, and `encounters` together — so
`build_merge_encounters_payload` can take just that one dict and no combining is needed.

```python
store = ResultStore(Path("."), transaction_id, persist_to_disk=False)
anchors = await poc_pipeline.run(..., result_store=store)
f2f_results = await f2f_pipeline.run(..., anchors=anchors, result_store=store)
# store.results now holds POC + F2F; payload = build_merge_encounters_payload(store.results, store.results)
```

Trade-off: you lose the clean POC-dict / F2F-dict separation (both requested for
independent S3 capture). Use two stores when you want that separation; use one when
you only care about the merged encounters.

---

## 13. Where to store intermediates (S3)

Because `persist_to_disk=False`, this library never touches your filesystem. Your
layer captures and stores each artifact from the returned dicts:

| Artifact | Source | When |
|---|---|---|
| POC processed + raw | `poc_results` (`poc_store.results`) | after Step 1 |
| F2F processed + raw | `f2f_results` (`f2f_store.results`) | after Step 2 |
| Merged encounters | `merge_encounters` | after Step 3 |
| Selection processed + raw | `selection_output.processed` / `.raw` | after Step 4 (optional) |

Serialize with `json.dumps(..., default=str)` (matches how `ResultStore._write`
handles non-JSON-native values).

---

## 14. Gotchas & FAQ

- **POC returns `AnchorSet`, not a dict.** Read the dict from `poc_store.results`;
  keep the returned `AnchorSet` to pass into F2F.
- **Raw + errors are in memory.** `results["raw"]` mirrors processed; `results["errors"]`
  lists soft failures. Available with `persist_to_disk=False` (see §10).
- **Async pipelines, sync merge.** Wrap the two `.run(...)` calls in an event loop;
  call `MergeEncountersEngine.build(...)` directly. Selection (Step 4) is **async** like the
  POC/F2F pipelines — `await selection_pipeline.run(...)`, not a direct call.
- **Selection is optional and last.** Only run it after the merge (DICT 3) exists.
  It returns an `AgentOutput` (`.processed` = DICT 4), not a `ResultStore` dict.
- **`soc_date` is required for selection.** It is a runtime call arg (not env); a
  blank/absent value raises `ValueError` before the agent runs. Fix the input — do
  not retry blindly. `client_name` is likewise required by the selection call.
- **`transaction_id` is yours.** Pass a stable id. (The dev entrypoints append
  `_run2`; do not copy that — it is a local-iteration hack.)
- **`client_id`.** POC needs `client_name` explicitly. In the merge payload it is
  optional — `TransactionOutputs.from_mapping` derives it from the outputs if omitted.
- **Zero-encounter F2F.** If classification returns no encounters, F2F still
  completes with an empty `encounters` map (logged as a warning). The merge engine
  then reports gaps in `data_quality.failed_agents`.
- **Batch isolation.** Wrap each transaction in try/except; a single failure
  (throttling, bad document) should not abort the batch.

---

## 15. Packaging notes (releasing as a library)

- **Ship `prompts/` and `skills/` as package data.** `AgentFactory` loads prompt
  templates via `PromptRenderer` and skill folders via a filesystem-backed backend
  (`skills_root`). If these are not packaged (or `PROMPTS_DIR` / `SKILLS_DIR` are
  not set), agents cannot run.
- **Expose a thin public API.** The top-level `__init__.py` is empty today.
  Consider re-exporting `PocPipeline`, `F2fPipeline`, `SelectionPipeline`,
  `ResultStore`, `AnchorSet`, `MergeEncountersEngine`, and `TransactionOutputs` from
  `f2f_orchestration` for a stable import surface.
- **Keep `bootstrap` optional.** It is convenience env-wiring; the env-free path
  (§4B) is the real library contract. Document both.
- **Dependencies.** AWS Bedrock (botocore), `deepagents`, and (optional) Langfuse
  must be declared as install requirements.
