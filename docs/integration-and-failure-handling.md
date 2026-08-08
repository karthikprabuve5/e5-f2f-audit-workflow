# Integration & Failure-Handling Guide

A complete, self-contained guide for orchestrating `e5_f2f_audit` from your
own Python layer (Temporal, Airflow, a service, a batch script — anything). It
covers the full run flow, the exact in-memory contract you get back (**processed +
raw + errors**), and **every failure case** with how to capture and handle it.

> The core flow is three dicts (POC → F2F → merge). Three **optional stages** follow
> the merge: a pure **referral filter** (`filter_candidates`), the **encounter
> selection** agent (picks the single best F2F encounter from the already-validated
> `merge_encounters` plus a runtime `soc_date`), and the pure **final audit**
> (`FinalAuditEngine`, a lossless superset merge + selection headline fields). They are
> called out separately wherever they apply (flow, contract, failures §5 Cases J/K).

> Companion doc: [`external-orchestration-guide.md`](./external-orchestration-guide.md)
> is the authoritative end-to-end reuse guide (imports, `OrchestrationConfig`
> construction, the full six-stage flow, Temporal mapping, packaging). This doc focuses
> on the **orchestration contract and failure handling**.

---

## 1. The run flow (three dicts + optional filter / selection / final audit)

```
POC.md ─▶ PocPipeline.run() ─▶ AnchorSet   (+ poc_store.results  = DICT 1)
                                   │ raises on hard failure
                                   ▼ anchors
F2F.md ─▶ F2fPipeline.run() ───────────────▶ f2f_store.results   = DICT 2
                                   │ raises only on hard failure; soft failures isolated
                                   ▼ build_merge_encounters_payload(DICT 1, DICT 2)
                            MergeEncountersEngine.build() ─▶ merge_encounters  = DICT 3
                                   │ filter_candidates(DICT 3, roster)          [optional, pure]
                                   ▼ (valid_candidates, excluded_encounters)
                            SelectionPipeline.run(valid, soc_date, excluded)    [optional]
                                   ▼ AgentOutput.processed ─▶ selection         = DICT 4
                                   │ FinalAuditEngine.build(FULL DICT 3, DICT 4) [optional, pure]
                                   ▼ audit                                       = DICT 5
```

- **POC must run first** — F2F needs the `AnchorSet` POC returns.
- **POC returns an `AnchorSet`**, not a dict; the POC *dict* is `poc_store.results`.
- **F2F returns its dict** directly (same object as `f2f_store.results`).
- **Merge, filter, and final audit are pure and sync**; the three agent pipelines
  (POC, F2F, selection) are `async`.
- **Filter is optional and pure**: `filter_candidates(merge, roster)` drops
  supporting-only encounters (`referral_documents`) from the selection candidate set
  and returns `(valid_candidates, excluded_encounters)`. Inputs are never mutated.
- **Selection is optional**; it is `async` (a deep-agent pipeline like POC/F2F, not
  pure) and returns an `AgentOutput` — DICT 4 is `.processed`. It needs a runtime
  `soc_date` (and `client_name`), and takes the filtered candidate set + `excluded`.
- **Final audit is optional and pure**: it consumes the **FULL** DICT 3 (not the
  filtered set) plus DICT 4 and returns DICT 5, a lossless superset (all encounters +
  selection headline fields + `encounter_selection_summary`).

---

## 2. What you get back — the `results` contract

Every `ResultStore` is **per-transaction**. `store.results` always has this shape
(keys always present; values fill in as work completes):

```python
{
  "transaction_id": "transaction_x",
  "classification":      {"f2f": {...}, "poc": {...}},   # processed
  "poc_485_extraction":  {...} | None,                   # processed
  "encounters":          {1: {"encounter-identity": {...}, "homebound": {...}}, 2: {...}},  # processed
  "summary":             {...} | None,                   # F2F run manifest + failure roll-up
  "merge_encounters":    {...} | None,                   # only if you call store_merge_encounters()
  "selection":           {...} | None,                   # only if you call store_selection() (DICT 4)
  "audit":               {...} | None,                   # only if you call store_audit() (DICT 5)

  # ── additive capture (safe to ignore; merge engine ignores these) ──
  "raw": {
    "classification":     {"f2f": {...}, "poc": {...}},  # pre-normalization agent output
    "poc_485_extraction": {...} | None,
    "encounters":         {1: {"encounter-identity": {...}}, ...},  # incl. unparseable raw strings
    "selection":          {...} | None,                  # raw selection agent output
  },
  "errors": [                                            # SOFT failures only (see §4)
    {"encounter_index": 3, "agent": "homebound", "error_type": "AgentOutputError", "message": "..."},
    {"encounter_index": 5, "agent": None,        "error_type": "ValueError",       "message": "..."},
  ],
}
```

Notes:
- `raw` **mirrors** the processed layout, so processed↔raw map 1:1 by the same keys.
  Unparseable agent output (non-JSON) is captured here as a **string**.
- `errors` is a **flattened** view of the soft failures the F2F pipeline isolates.
  It is populated when `summary` is stored. An entry with `agent: None` is a
  **whole-encounter** failure; otherwise it's a single agent failure.
- With two separate stores (recommended), `poc_store.results` fills the POC keys
  and `f2f_store.results` fills the F2F keys — neither is "complete" alone, which is
  why the merge adapter combines them (§3).

---

## 3. Minimal end-to-end orchestration

```python
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from e5_f2f_audit import (
    OrchestrationConfig, ModelConfig,
    build_poc_pipeline, build_f2f_pipeline, build_selection_pipeline,
    build_final_audit_engine,
    MergeEncountersEngine, TransactionOutputs, build_merge_encounters_payload,
    filter_candidates,
)
from e5_f2f_audit.core.result_store import ResultStore
from e5_f2f_audit.pipelines.poc_pipeline import POCClassificationError
from e5_f2f_audit.agents.agent_factory import AgentOutputError

_IN_MEMORY = Path("unused-when-not-persisting")

# Build config once and inject it (no env required). OrchestrationConfig.from_env()
# is available for local dev.
CONFIG = OrchestrationConfig(
    model=ModelConfig(active_model="anthropic",
                      kimi_model_id="<bedrock-id>", anthropic_model_id="<bedrock-id>"),
    client_name="DEFAULT",
)


async def orchestrate_one(transaction_id, poc_md, f2f_md, soc_date=None, config=CONFIG):
    poc_pipeline = build_poc_pipeline(config)
    f2f_pipeline = build_f2f_pipeline(config)
    selection_pipeline = build_selection_pipeline(config)       # optional Step 5
    client = config.client_name
    now = datetime.now(UTC).isoformat()

    # 1) POC (hard failures raise — see §4)
    poc_store = ResultStore(_IN_MEMORY, transaction_id, persist_to_disk=False)
    anchors = await poc_pipeline.run(
        transaction_id=transaction_id, poc_document_content=poc_md,
        client_name=client, result_store=poc_store,
    )
    poc_results = poc_store.results          # DICT 1  (processed + raw)

    # 2) F2F (hard failures raise; soft failures land in results['errors'])
    f2f_store = ResultStore(_IN_MEMORY, transaction_id, persist_to_disk=False)
    f2f_results = await f2f_pipeline.run(
        transaction_id=transaction_id, f2f_document_content=f2f_md,
        anchors=anchors, result_store=f2f_store,
    )                                        # DICT 2  (processed + raw + errors)

    # 3) Merge encounters (pure)
    payload = build_merge_encounters_payload(poc_results, f2f_results,
                                             transaction_id=transaction_id, client_id=client)
    merged = MergeEncountersEngine().build(TransactionOutputs.from_mapping(payload),
                                           generated_at=now)

    # 4) Filter referral/supporting-only encounters out of the candidate set (pure)
    valid_candidates, excluded = filter_candidates(
        merged, f2f_results["classification"]["f2f"])

    # 5) Selection (optional; requires a runtime soc_date — see Case J)
    selection = None
    if soc_date:
        selection_output = await selection_pipeline.run(
            transaction_id=transaction_id, merge_encounters=valid_candidates,
            soc_date=soc_date, client_name=client, excluded_encounters=excluded,
        )
        selection = selection_output.processed          # DICT 4 (+ .raw, .validation)

    # 6) Final audit (optional, pure; uses the FULL merge + selection — see Case K)
    audit = None
    if selection is not None:
        audit = build_final_audit_engine().build(merged, selection, generated_at=now)

    return poc_results, f2f_results, merged, selection, audit   # DICT 3 (+ DICT 4, DICT 5)
```

Push `poc_results`/`f2f_results` (including their `raw` subtrees), `merged`,
`selection` (with `selection_output.raw`), and `audit` to your own sink (S3) wherever
you like — the library never touches disk when `persist_to_disk=False`.

---

## 4. The failure model — hard vs soft

This is the core of production orchestration. There are exactly **two failure
classes**, and they surface differently.

### Hard failures → **an exception is raised out of `run()`**

These abort the transaction. They happen on the **document-level** steps that are
awaited directly (not inside a `gather`): POC classification, the `poc_485` gate,
POC extraction, and F2F classification.

| Exception | Raised by | Meaning |
|---|---|---|
| `POCClassificationError` | `PocPipeline` | POC has no `poc_485` / `2.1` encounter — not a plan of care |
| `AgentOutputError` | `AgentFactory` (via POC/F2F classification, POC extraction, or the selection agent) | agent wrote no output / non-JSON / non-object |
| `ValueError` | `SelectionPipeline` (optional stage) | blank/absent `soc_date` or `client_name` — a caller precondition violation, fails fast before the agent runs |
| `botocore.exceptions.ClientError`, `ReadTimeoutError`, `ConnectTimeoutError`, `EndpointConnectionError` | Bedrock, after retries exhausted | throttling/transient failure that outlived the retry budget |

Import points:
- `from e5_f2f_audit.pipelines.poc_pipeline import POCClassificationError`
- `from e5_f2f_audit.agents.agent_factory import AgentOutputError`

> **Not in `results`.** A hard failure is raised *before* the summary is stored, so
> it never appears in `results["errors"]`. You capture it with `try/except`.

### Soft failures → **isolated, recorded, run still succeeds**

Any **per-encounter agent** failure (`encounter-identity`, `primary-diagnosis`,
`skilled-services`, `homebound`, `inpatient-detection`, `telehealth-identity`,
`surgical-note`) or a
**whole-encounter** failure is caught by the F2F pipeline (`asyncio.gather(...,
return_exceptions=True)`). The run completes and returns a dict. These are surfaced
in two places:

- `results["summary"]["totals"]["agents_failed"]` and
  `results["summary"]["encounters"][i]["failed"]` (the raw roll-up), and
- `results["errors"]` — the flattened, ready-to-consume list (see §2).

The failing agent has **no entry** under `results["encounters"][i]`, and its raw
(if unparseable) is captured under `results["raw"]["encounters"][i]`.

---

## 5. Every case — behavior, output, and handling

### Case A — Full success

- POC finds `poc_485`/`2.1`; F2F classifies and all selected agents succeed.
- `poc_results["poc_485_extraction"]` filled; `f2f_results["encounters"]` filled;
  `f2f_results["errors"] == []`.
- **Handling:** proceed to merge. `merged["data_quality"]["failed_agents"]` empty.

### Case B — POC is not a plan of care (no `poc_485`/`2.1`)

- `PocPipeline.run()` **raises `POCClassificationError`** after storing `poc`
  classification. `poc_485_extraction` stays `None`. No `AnchorSet`. F2F never runs.
- Sample exception:

```
POCClassificationError: POC classification for 'transaction_x' has no
'poc_485' / '2.1' encounter (found 2: [('f2f_encounter', '1.3'), ('progress_note', '3.2')]).
```

- **Handling:** catch it, mark the transaction "skipped: not a plan of care", do not
  attempt F2F or merge. This is a data condition, not a system fault — do **not** retry.

### Case C — POC has zero encounters

- Same as Case B (`found 0: []`). Almost always a malformed/empty POC document.
- **Handling:** same as B; additionally flag for document-quality review.

### Case D — POC classification or extraction agent hard-fails

- `AgentOutputError` (bad/no JSON) or an exhausted-retry Bedrock error propagates
  out of `PocPipeline.run()`.
- **Handling:** catch per transaction. For Bedrock/throttling errors, a **whole-
  transaction retry** is appropriate (see §6). For `AgentOutputError`, retry once
  (model non-determinism) then route to manual review.

### Case E — F2F classification hard-fails

- F2F classification is awaited directly, so `AgentOutputError` / Bedrock errors
  **raise out of `F2fPipeline.run()`**. No encounters are processed.
- **Handling:** same as Case D (retry policy by error type). POC output is still
  valid, so on retry you can reuse the anchors and re-run only F2F.

### Case F — F2F classification returns **no encounters** (not an exception)

- The pipeline logs a warning and completes: `encounters == {}`, `summary` present
  with `encounter_count: 0`, `errors == []`.
- **Handling:** treat as a soft anomaly — merge will build but
  `data_quality.failed_agents` will be empty and there is simply nothing to merge.
  Flag for review; do not retry automatically.

### Case G — Some F2F agents fail (soft, isolated)

- The run succeeds. Failing agents appear in `results["errors"]` and the summary;
  their processed output is absent; unparseable raw is under `results["raw"]`.
- Sample `results["errors"]`:

```json
[
  {"encounter_index": 2, "agent": "homebound", "error_type": "AgentOutputError", "message": "output is not valid JSON."},
  {"encounter_index": 4, "agent": "skilled-services", "error_type": "ClientError", "message": "ThrottlingException ..."}
]
```

- **Handling:** you decide policy per your SLA:
  - **Proceed to merge anyway** — the merge engine records the gap in
    `merged["data_quality"]["failed_agents"]` (a false PASS is never shown).
  - **Targeted re-run** — re-run only the failed agents/encounters (see §6) before merging.

### Case H — Whole encounter fails (soft)

- A per-encounter exception yields an `errors` entry with `agent: None` and a
  summary entry with `failed["__encounter__"]`. Other encounters are unaffected.
- **Handling:** same options as Case G, scoped to the encounter.

### Case I — Merge input problems

- `TransactionOutputs.from_mapping` raises `ValueError` if `transaction_id` is
  missing from the payload. A present-but-corrupt file (disk path) raises `ValueError`.
- **Handling:** this is a programming/data-plumbing error in your adapter — fail
  loud, fix the payload; do not retry blindly.

### Case J — Selection input / agent problems (optional stage)

- **Missing `soc_date` / `client_name`** → `SelectionPipeline.run()` raises
  `ValueError` **before** any agent runs. This is a caller precondition violation
  (SOC is always provided at runtime). Fix the input; **do not retry blindly**.
- **Selection agent hard-fails** → the selection agent is awaited directly (not in a
  `gather`), so `AgentOutputError` (bad/no JSON) or an exhausted-retry Bedrock error
  **raises out of `run()`**, exactly like classification. POC/F2F/merge outputs
  remain valid, so retry only the selection step (see §6). Selection never mutates
  the earlier dicts.
- **Selection completes with a non-`SELECTED` decision** → not an exception. The
  `result.decision` is `NEEDS_HUMAN_REVIEW` or `NO_ELIGIBLE_ENCOUNTER` (and
  `best_encounter_index` may be `null`). Route per your compliance policy; the
  validator flags any unexpected decision as a schema warning, not a failure.

### Case K — Final audit input problems (optional stage)

- `FinalAuditEngine.build` is pure and validates its inputs. It raises `ValueError`
  if the `transaction_id` in the merge and the selection disagree, or if either input
  is not a mapping — a data-plumbing error, not a transient fault.
- It performs **no pruning**: every merged encounter is retained and the selection
  headline fields (`best_encounter_index`, `best_encounter_score`,
  `best_is_date_aligned`, `date_aligned_encounter`, `excluded_encounters`,
  `encounter_selection_summary`) are prefixed onto `audit["results"]`.
- **Handling:** fail loud, fix the caller (you almost certainly passed mismatched
  transactions); do not retry blindly. A missing `encounter_selection_summary` source
  simply yields `null` — not an error.

---

## 6. Handling patterns (production standard)

### Per-transaction isolation (mirror the local batch loop)

```python
succeeded, skipped, failed = [], {}, {}
for txn in transaction_ids:
    try:
        poc_results, f2f_results, merged, selection, audit = await orchestrate_one(
            txn, poc_md, f2f_md, soc_date=soc_dates[txn]     # omit soc_date to skip Steps 5-6
        )
    except POCClassificationError as exc:
        skipped[txn] = f"not_a_plan_of_care: {exc}"          # Case B/C — do not retry
        continue
    except ValueError as exc:
        failed[txn] = f"bad_input: {exc}"                    # Case I/J — fix input, do not retry
        continue
    except AgentOutputError as exc:
        failed[txn] = f"agent_output: {exc}"                 # Case D/E/J — retry-once then review
        continue
    except Exception as exc:                                  # Bedrock/unknown — see retry policy
        failed[txn] = f"{type(exc).__name__}: {exc}"
        continue

    soft = f2f_results["errors"]                              # Case G/H
    if soft:
        # policy: proceed-with-gaps OR targeted re-run
        log.warning("soft failures", extra={"txn": txn, "count": len(soft)})
    succeeded.append(txn)
```

> A broad `except Exception` at the **transaction boundary** is the correct place
> for batch isolation — one bad transaction must never abort the batch. Keep it at
> the boundary only; never swallow exceptions deeper in.

### Retry policy by error type

| Situation | Retry? | Scope |
|---|---|---|
| Throttling / transient Bedrock (after internal retries already exhausted) | Yes, with backoff | Whole transaction, or F2F-only if POC succeeded |
| `AgentOutputError` (model produced bad JSON) | Once (non-determinism), then manual review | The failing step (incl. selection, Case J) |
| `POCClassificationError` / zero encounters | No | — (data condition) |
| `ValueError` (bad merge payload / missing `soc_date` — Case I/J) | No | — (precondition; fix the input) |
| Selection agent Bedrock/transient (Case J) | Yes, with backoff | Selection step only (merge already valid) |
| Soft agent failures (Case G/H) | Optional, targeted | Re-run only the failed agent/encounter |

> The pipeline already retries throttling/transient errors internally with
> exponential backoff (`AGENT_MAX_RETRIES`, `AGENT_RETRY_*`). Your transaction-level
> retry is the outer safety net for exhausted budgets.

### Idempotency & re-runs

- Re-running is safe: each run uses a fresh `ResultStore`; nothing is shared between
  transactions. With `persist_to_disk=False` there are no partial files to clean up.
- If POC succeeded, cache its `AnchorSet` (or `poc_485_extraction`) and re-run only
  F2F to avoid re-paying for POC.

### Deciding PASS vs incomplete from the merge

- After building the merge, inspect `merged["data_quality"]`:
  - `failed_agents` — expected agents that produced no output / critical validation,
    per encounter.
  - `schema_issues` — non-empty validation signals (missing/repaired/dangling).
- Non-empty `data_quality` means the merge is built on **incomplete** data — gate
  your downstream "PASS" on it per your compliance rules.

---

## 7. Production notes

- **PHI/PII:** `raw` (and processed) outputs contain clinical text. Keep them out of
  logs (the library logs only paths/metadata), and ensure your S3 sink is encrypted
  and access-controlled. Never log raw payloads.
- **No silent failures:** hard failures raise; soft failures are recorded in
  `errors` + `summary`. Do not add `except: pass` anywhere in your orchestration.
- **Structured logging:** log transaction id, error type, and counts — not payloads.
- **Determinism of the pure stages:** `MergeEncountersEngine`, `filter_candidates`,
  and `FinalAuditEngine` read no clock/env/IO; you inject `generated_at`. Safe inside a
  Temporal activity.
- **Config injection, not env:** build an `OrchestrationConfig` explicitly and pass it
  to the builders — an external package should not rely on process env.
  `OrchestrationConfig.from_env()` is a local-dev convenience; `load_environment()` is
  hardened to log a `WARNING` and continue if a `.env` is unreadable (it never crashes
  the entrypoint).
- **Concurrency:** the pipeline caps in-flight Bedrock calls globally
  (`ConcurrencyConfig.max_concurrent_agents`). If you run many transactions
  concurrently in your layer, remember each pipeline instance has its own cap — size
  accordingly.

---

## 8. Quick reference

| You want | Where to look |
|---|---|
| POC processed | `poc_results["poc_485_extraction"]`, `poc_results["classification"]["poc"]` |
| POC raw | `poc_results["raw"][...]` |
| F2F processed per agent | `f2f_results["encounters"][enc][agent]` |
| F2F raw per agent | `f2f_results["raw"]["encounters"][enc][agent]` |
| Soft failures (flattened) | `f2f_results["errors"]` |
| Soft failures (detailed roll-up) | `f2f_results["summary"]["encounters"][i]["failed"]` |
| Hard failure | caught exception from `run()` |
| Consolidated verdicts + gaps | `merged["results"]`, `merged["data_quality"]` |
| Excluded (referral) encounters | `filter_candidates(...)[1]`, echoed in `selection["result"]["excluded_encounters"]` |
| Selected encounter (optional) | `selection["result"]["best_encounter_index"]`, `selection["result"]["decision"]` |
| Selection raw | `selection_output.raw` |
| Final audit (lossless superset) | `audit["results"]` (all encounters + `best_encounter_index`, `best_encounter_score`, `encounter_selection_summary`, …) |
