# Integration & Failure-Handling Guide

A complete, self-contained guide for orchestrating `f2f_orchestration` from your
own Python layer (Temporal, Airflow, a service, a batch script — anything). It
covers the full run flow, the exact in-memory contract you get back (**processed +
raw + errors**), and **every failure case** with how to capture and handle it.

> Companion doc: [`library-integration-guide.md`](./library-integration-guide.md)
> covers imports, construction options, and packaging. This doc focuses on the
> **orchestration contract and failure handling**.

---

## 1. The run flow (three dicts)

```
POC.md ─▶ PocPipeline.run() ─▶ AnchorSet   (+ poc_store.results  = DICT 1)
                                   │ raises on hard failure
                                   ▼ anchors
F2F.md ─▶ F2fPipeline.run() ───────────────▶ f2f_store.results   = DICT 2
                                   │ raises only on hard failure; soft failures isolated
                                   ▼ build_audit_payload(DICT 1, DICT 2)
                            AuditEngine.build() ─▶ audit-results  = DICT 3
```

- **POC must run first** — F2F needs the `AnchorSet` POC returns.
- **POC returns an `AnchorSet`**, not a dict; the POC *dict* is `poc_store.results`.
- **F2F returns its dict** directly (same object as `f2f_store.results`).
- **Audit is pure and sync**; the two pipelines are `async`.

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
  "audit_results":       {...} | None,                   # only if you call store_audit_results()

  # ── additive capture (safe to ignore; audit engine ignores these) ──
  "raw": {
    "classification":     {"f2f": {...}, "poc": {...}},  # pre-normalization agent output
    "poc_485_extraction": {...} | None,
    "encounters":         {1: {"encounter-identity": {...}}, ...},  # incl. unparseable raw strings
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
  why the audit adapter merges them (§3).

---

## 3. Minimal end-to-end orchestration

```python
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from f2f_orchestration import bootstrap
from f2f_orchestration.core.result_store import ResultStore
from f2f_orchestration.pipelines.poc_pipeline import POCClassificationError
from f2f_orchestration.agents.agent_factory import AgentOutputError
from f2f_orchestration.audit import AuditEngine, TransactionOutputs, build_audit_payload

_IN_MEMORY = Path("unused-when-not-persisting")


async def orchestrate_one(transaction_id, poc_md, f2f_md):
    bootstrap.load_environment()
    poc_pipeline = bootstrap.build_poc_pipeline()
    f2f_pipeline = bootstrap.build_f2f_pipeline()
    client = bootstrap.client_name()

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

    # 3) Audit (pure)
    payload = build_audit_payload(poc_results, f2f_results,
                                  transaction_id=transaction_id, client_id=client)
    audit = AuditEngine().build(TransactionOutputs.from_mapping(payload),
                                generated_at=datetime.now(UTC).isoformat())
    return poc_results, f2f_results, audit   # DICT 3
```

Push `poc_results`/`f2f_results` (including their `raw` subtrees) and `audit` to
your own sink (S3) wherever you like — the library never touches disk when
`persist_to_disk=False`.

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
| `AgentOutputError` | `AgentFactory` (via POC/F2F classification or POC extraction) | agent wrote no output / non-JSON / non-object |
| `botocore.exceptions.ClientError`, `ReadTimeoutError`, `ConnectTimeoutError`, `EndpointConnectionError` | Bedrock, after retries exhausted | throttling/transient failure that outlived the retry budget |

Import points:
- `from f2f_orchestration.pipelines.poc_pipeline import POCClassificationError`
- `from f2f_orchestration.agents.agent_factory import AgentOutputError`

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
- **Handling:** proceed to audit. `audit["data_quality"]["failed_agents"]` empty.

### Case B — POC is not a plan of care (no `poc_485`/`2.1`)

- `PocPipeline.run()` **raises `POCClassificationError`** after storing `poc`
  classification. `poc_485_extraction` stays `None`. No `AnchorSet`. F2F never runs.
- Sample exception:

```
POCClassificationError: POC classification for 'transaction_x' has no
'poc_485' / '2.1' encounter (found 2: [('f2f_encounter', '1.3'), ('progress_note', '3.2')]).
```

- **Handling:** catch it, mark the transaction "skipped: not a plan of care", do not
  attempt F2F or audit. This is a data condition, not a system fault — do **not** retry.

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
- **Handling:** treat as a soft anomaly — audit will build but
  `data_quality.failed_agents` will be empty and there is simply nothing to audit.
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
  - **Proceed to audit anyway** — the audit engine records the gap in
    `audit["data_quality"]["failed_agents"]` (a false PASS is never shown).
  - **Targeted re-run** — re-run only the failed agents/encounters (see §6) before auditing.

### Case H — Whole encounter fails (soft)

- A per-encounter exception yields an `errors` entry with `agent: None` and a
  summary entry with `failed["__encounter__"]`. Other encounters are unaffected.
- **Handling:** same options as Case G, scoped to the encounter.

### Case I — Audit input problems

- `TransactionOutputs.from_mapping` raises `ValueError` if `transaction_id` is
  missing from the payload. A present-but-corrupt file (disk path) raises `ValueError`.
- **Handling:** this is a programming/data-plumbing error in your adapter — fail
  loud, fix the payload; do not retry blindly.

---

## 6. Handling patterns (production standard)

### Per-transaction isolation (mirror the local batch loop)

```python
succeeded, skipped, failed = [], {}, {}
for txn in transaction_ids:
    try:
        poc_results, f2f_results, audit = await orchestrate_one(txn, poc_md, f2f_md)
    except POCClassificationError as exc:
        skipped[txn] = f"not_a_plan_of_care: {exc}"          # Case B/C — do not retry
        continue
    except AgentOutputError as exc:
        failed[txn] = f"agent_output: {exc}"                 # Case D/E — retry-once then review
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
| `AgentOutputError` (model produced bad JSON) | Once (non-determinism), then manual review | The failing step |
| `POCClassificationError` / zero encounters | No | — (data condition) |
| Soft agent failures (Case G/H) | Optional, targeted | Re-run only the failed agent/encounter |

> The pipeline already retries throttling/transient errors internally with
> exponential backoff (`AGENT_MAX_RETRIES`, `AGENT_RETRY_*`). Your transaction-level
> retry is the outer safety net for exhausted budgets.

### Idempotency & re-runs

- Re-running is safe: each run uses a fresh `ResultStore`; nothing is shared between
  transactions. With `persist_to_disk=False` there are no partial files to clean up.
- If POC succeeded, cache its `AnchorSet` (or `poc_485_extraction`) and re-run only
  F2F to avoid re-paying for POC.

### Deciding PASS vs incomplete from the audit

- After building the audit, inspect `audit["data_quality"]`:
  - `failed_agents` — expected agents that produced no output / critical validation,
    per encounter.
  - `schema_issues` — non-empty validation signals (missing/repaired/dangling).
- Non-empty `data_quality` means the audit is built on **incomplete** data — gate
  your downstream "PASS" on it per your compliance rules.

---

## 7. Production notes

- **PHI/PII:** `raw` (and processed) outputs contain clinical text. Keep them out of
  logs (the library logs only paths/metadata), and ensure your S3 sink is encrypted
  and access-controlled. Never log raw payloads.
- **No silent failures:** hard failures raise; soft failures are recorded in
  `errors` + `summary`. Do not add `except: pass` anywhere in your orchestration.
- **Structured logging:** log transaction id, error type, and counts — not payloads.
- **Determinism of audit:** `AuditEngine` reads no clock/env/IO; you inject
  `generated_at`. Safe inside a Temporal activity.
- **Concurrency:** the pipeline caps in-flight Bedrock calls globally
  (`MAX_CONCURRENT_AGENTS`). If you run many transactions concurrently in your
  layer, remember each pipeline instance has its own cap — size accordingly.

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
| Final verdicts + gaps | `audit["results"]`, `audit["data_quality"]` |
