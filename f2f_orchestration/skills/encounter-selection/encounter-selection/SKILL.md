---
name: encounter-selection
description: >-
  Selects the single best Face-to-Face encounter to send on the home health claim
  when a transaction has multiple encounters. Consumes the consolidated
  merge_encounters (already-validated, per-encounter verdicts from the upstream F2F
  skills) plus a start-of-care date, and reasons like a MAC reviewer to choose the
  most claim-defensible encounter. It SELECTS — it does not re-validate. Selection
  uses ONLY five parameters: timely_encounter, eligible_practitioners,
  primary_hh_reason, homebound, and skilled_services. It never uses telehealth,
  inpatient, or surgical_note — those are validated downstream when the final CMS
  audit results are generated. The only rule it applies originally is the 90/30-day
  timing window (needs SOC), which the upstream skills defer. Emits
  best_encounter_index, a weighted 0-100 score per encounter, best_is_date_aligned,
  a decision, a clinical narrative summary of the whole selection in an auditor's
  voice, and a per-encounter comparison explaining why the winner beats every other
  encounter.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Reads client_name and soc_date from the system prompt.
  Input merge_encounters JSON: /workspace/documents/MERGE_ENCOUNTERS.json
  CMS files: /skills/encounter-selection/encounter-selection/references/
  Client file: /skills/encounter-selection/encounter-selection/clients/<client_name>/client-rules.md
---

# encounter-selection

## Overview

Chooses the one F2F encounter that should go on the claim, from a transaction that
may contain several. The input is the transaction's `merge_encounters` JSON — the
consolidated, evidence-resolved output of the upstream F2F skills — where every
encounter already carries decided verdicts (timeliness date, provider eligibility,
primary-reason alignment, homebound, skilled services, inpatient/setting).

**This skill SELECTS; it does not re-validate.** Every eligibility judgment was
already made by the owning upstream skill. This skill *reads* those verdicts,
*weighs* them across encounters, and *picks* the strongest, most defensible one —
it never re-extracts or re-classifies. The only CMS rule it applies originally is
the **90/30-day timing window** relative to `soc_date` (upstream `encounter-identity`
states it "does not validate the timing window").

**Selection parameters (the ONLY ones used):**
- `timely_encounter`
- `eligible_practitioners`
- `primary_hh_reason`
- `homebound`
- `skilled_services`

**Never used for selection:** `telehealth`, `inpatient`, and `surgical_note`. These
are validated downstream when the final CMS audit results are generated — ignore
them entirely here, even when present in the merge_encounters input.

**This skill does NOT:** read raw OCR, re-extract dates/providers, re-run the
homebound two-prong test, re-score skilled necessity, classify setting, or evaluate
telehealth/inpatient/surgical-note. If a verdict is missing or `UNABLE_TO_DETERMINE`
in the merge_encounters input, treat it as a gap (a selection risk) — never fill or re-derive it.

**Input:** one transaction's `merge_encounters` JSON at `/workspace/documents/MERGE_ENCOUNTERS.json`.

### Reference Files

| File | When to Read |
|------|-------------|
| `references/cms-selection-rules.md` | Step 1 — always |
| `references/selection-criteria.md` | Step 1 — always |
| `references/risk-flags.md` | Step 1 — always |
| `references/decision-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `references/inference-summary.md` | Steps 6–7 — writing the clinical summary + comparison |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before reading the merge_encounters input, read:
- `references/cms-selection-rules.md` — the CMS basis for choosing; cites the upstream
  skill `cms_section_id`s for every read-only criterion, and holds the original text for
  the one deferred rule in scope here (the 90/30 timing window).
- `references/selection-criteria.md` — the priority waterfall and how to read each
  merge_encounters verdict as a ranking signal.
- `references/risk-flags.md` — the denial-risk signals that make one encounter less
  claim-safe than another.
- `references/decision-rules.md` — how to set `decision` and when to escalate.
- `references/output-schema.md` — the exact JSON structure and every field rule.

Check `client_name` from the system prompt:
- If `DEFAULT` → no additional file; apply CMS selection rules only.
- If not `DEFAULT` → additionally read `clients/<client_name>/client-rules.md`.

**If client-rules.md is loaded, parse each directive block:**

Each directive begins with: `## DIRECTIVE <ID> | <TYPE> | <ANCHOR>`
Read `TYPE` and apply this guard:
- `ELEVATE` → always valid; client condition IN ADDITION to CMS; failure changes the
  selection outcome; record it in `reasoning.missing`.
- `EXTEND` → always valid; Affects Outcome YES → changes the selection; Affects Outcome
  NO → adds to `agency_warnings` only.
- `EXCLUDE` → check Element Type; ILLUSTRATION / EXAMPLE / SUGGESTION → apply;
  REGULATION / REQUIREMENT / CRITERIA → do NOT apply; add to `agency_warnings`:
  "EXCLUDE [ID] targets CMS requirement — not applied".
- `REPLACE` → check Element Type; EXAMPLE / ILLUSTRATION / SUGGESTION → apply;
  REGULATION / REQUIREMENT / CRITERIA → do NOT apply; add to `agency_warnings`:
  "REPLACE [ID] targets CMS requirement — not applied".

CMS rules not mentioned in client-rules.md remain fully in effect.
Do not proceed until all required files are read.

### 2. Read the Merge-Encounters Input

Read `/workspace/documents/MERGE_ENCOUNTERS.json` in full. Note `transaction_id`, `client_id`,
and the full encounter roster (every `encounter_index` under
`results.timely_encounter.f2f_encounters`). Every encounter in the roster MUST appear
in your output, in index order — never drop one.

**Evidence rule:** quote `verbiage` + `page` only (no line numbers). Copy evidence
verbatim from the merge_encounters input; never invent or paraphrase location data.

### 3. Establish the Timing Window and Date Alignment

Using `soc_date` from the system prompt, compute the **120-day** encounter window per
`cms-selection-rules.md`: **90 days before `soc_date` through 30 days after**
(inclusive). Record `encounter_window.start` and `encounter_window.end`. If `soc_date`
is absent, mark timeliness `UNKNOWN` for every encounter, flag `SOC_MISSING`, and
escalate — do not guess.

Then compute **date alignment** (`SEL_DATE_ALIGNMENT`): for each encounter set
`date_aligned` + `matched_anchor` by **exact** match of `encounter_date` to a POC
anchor (`i_certify` / `undersigned`), and emit the transaction-level
`date_aligned_encounter` key. Date alignment is **reported and used in reconciliation
and tie-breaking — never a gate and never an early exit** (you still rank all
encounters in Step 5). If no anchor exists, flag `NO_ANCHOR_DATE`; if the two anchors
point to different encounters, flag `ANCHOR_DATES_DISAGREE`.

### 4. Summarize Each Encounter's Verdicts (read-only)

For every encounter in the roster, pull the already-decided verdicts from the audit
input (do NOT re-derive), each with `verbiage` + `page`. Use ONLY these five
parameters (ignore `telehealth`, `inpatient`, `surgical_note`):
- **Timeliness** — `timely_encounter.f2f_encounters[i].encounter_date` vs the window.
- **Provider** — `eligible_practitioners…eligible_provider.conducting_provider.is_allowed`,
  `provider_type`, `signature_type`, `overall_confidence` (read under the CY2026
  definition — the performer need not be the certifier; see `cms-selection-rules.md`).
- **Substantiating note** — the encounter must be backed by an actual signed clinical
  note, not just a date on the certification.
- **Relatedness** — `primary_hh_reason.f2f_encounters[i].alignment.status`, `pathways_met`.
- **Homebound** — `homebound.f2f_encounters[i].status`, `prong_1.met`, `prong_2.met`.
- **Skilled** — `skilled_services.f2f_encounters[i]` service justification and strength.

### 5. Screen, Score, then Rank (double-check every encounter)

Per `selection-criteria.md`:
1. **Screen** each encounter on the Stage-1 hard gates (timing window, allowed
   practitioner, substantiating signed note, no hard relatedness contradiction).
   A gate failure → `NOT_ELIGIBLE`. Signature *strength* is NOT a gate.
2. **Resolve alignment** for each eligible encounter on all six parameters —
   time window, **primary diagnosis**, homebound, skilled services, provider
   eligibility, signature — to `ALIGNED` / `NOT_ALIGNED` / `UNABLE_TO_DETERMINE`
   per `SEL_ALIGNMENT_MAP` (skilled counts as `ALIGNED` when `MET`, or `PARTIAL`
   with ≥1 justified POC-ordered discipline; homebound `ALIGNED` when `MET`).
3. **Score** each encounter 0–100 per `SEL_SCORE` (Primary 30 / Homebound 20 /
   Skilled 20 / Time 10 / Provider 10 / Signature 10) and emit `score` +
   `score_breakdown`. The score is **advisory** — a tie-breaker only.
4. **Rank** (`SEL_WATERFALL`), ranking **all** eligible encounters even if a
   date-aligned one looks fully aligned (the double-check):
   - **Primary-diagnosis threshold (dominant)** — only `ALIGNED`-on-primary-dx
     encounters can be best; a primary-dx-unaligned encounter can never win, no
     matter its score. None aligned → `PRIMARY_DX_UNALIGNED` → review.
   - **Clinical-pillar coverage** — among those, prefer more of {homebound,
     skilled} aligned (2 > 1 > 0).
   - **Full criteria coverage** — then the higher count of all six.
   - **Tie-breakers** — score (advisory) → certified-date → signature/provider
     strength → closest-to-SOC → documentation defensibility.
5. **Reconcile against the date-aligned encounter** (`SEL_DATE_RECONCILIATION`):
   set `best_is_date_aligned` and `final_statement`. If the ranked winner **is**
   the date-aligned encounter → `date_and_clinical_agree`. If a different encounter
   strictly out-ranks it → **never silently swap**: recommend the winner,
   `clinical_override_of_date_match`, flag `DATE_MATCH_OVERRIDDEN_BY_CLINICAL` →
   review, and report both. If only *equal*, the date-aligned encounter wins.

Assign each encounter a `standing` (`PREFERRED` | `VIABLE` | `WEAK` | `NOT_ELIGIBLE`),
its six-parameter `alignment` profile, `score` + `score_breakdown`,
`criteria_satisfied_count`, `clinical_relevance` summary, `strengths`, `weaknesses`,
and `risk_flags` (from `risk-flags.md`). **Always** build the full per-encounter
relevance report for *every* encounter — required for both the pick and the defense.

### 6. Decide

Per `decision-rules.md`, set `best_encounter_index`, `best_encounter_score`,
`best_is_date_aligned`, `decision`, `selection_method`, and `final_statement`:
- `SELECTED` — the ranked winner passes the gates, is aligned on **primary dx plus
  both clinical pillars** (homebound + skilled), and is the date-aligned encounter
  (or no anchor exists), with no *critical* risk. A lower-priority `warning`
  (e.g. `WEAK_SIGNATURE`, `NO_ANCHOR_DATE` when otherwise fully aligned) is
  disclosed but does NOT block `SELECTED`.
- `NEEDS_HUMAN_REVIEW` — residual clinical-pillar gap on the winner
  (`DECISIVE_DATA_GAP`), the winner is not the date-aligned encounter
  (`DATE_MATCH_OVERRIDDEN_BY_CLINICAL`), no primary-dx alignment anywhere
  (`PRIMARY_DX_UNALIGNED`), anchors disagree (`ANCHOR_DATES_DISAGREE`), SOC missing
  (`SOC_MISSING`), or an unresolved tie. Still name the recommended `best_encounter_index`.
- `NO_ELIGIBLE_ENCOUNTER` — no encounter passes the gates; `best_encounter_index = null`.

### 7. Write the Summary and Comparison

Per `inference-summary.md`, write two things:
- **`reasoning.summary`** — the clinical narrative of the whole selection, in an
  auditor's voice (a MAC reviewer assessing whether the record substantiates the
  claim): the plan-of-care reason, whether each encounter's documentation
  substantiates the diagnosis, home confinement, and skilled need, which encounter
  most defensibly supports the claim and why, and any documentation gap to resolve —
  citing `verbiage` + `page`. Do **not** use system vocabulary here (no gates, score,
  "clinical-pillar", date-aligned/anchor, or `selection_method`); those live in the
  structured fields.
- **`result.comparison[]`** — the technical defense: for each *other* encounter
  (always including the date-aligned one when it is not the winner), state plainly
  why it lost to the winner, citing `verbiage` + `page` and naming the deciding step
  (primary-dx threshold, clinical-pillar coverage, full coverage, or a tie-breaker).
  State explicitly whether the best is the date-aligned encounter or another.

### 8. Generate Output

Follow `references/output-schema.md` exactly.
- Top-level `status` mirrors `result.decision`.
- All evidence inline as `{ "verbiage": ..., "page": ... }`; top-level `evidence` is `[]`.
- Factual reasoning only — no PII, no fabricated content.
- Populate `rules_applied.client` for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/encounter-selection/results.json`.
