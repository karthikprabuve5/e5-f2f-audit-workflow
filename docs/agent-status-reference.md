# Agent Status Reference

**What each agent's `status` field can report, what each value means, and the
confidence band that must accompany it.**

Every agent envelope carries a top-level `status` and a `confidence` float
(`0.0 – 1.0`). `status` is the agent's verdict for the encounter (or document);
`confidence` is how strongly the evidence supports that verdict. The two are not
independent — each status maps to a fixed confidence band, and an agent must
never report a high confidence with a non-MET / non-success status.

Source of truth for every table below is each skill's
`references/output-schema.md`.

---

## 1. Status families at a glance

The nine agents do **not** share one status vocabulary. They fall into four
families, chosen to match what the agent is actually deciding:

| Family | Vocabulary | Used by | Semantics |
|---|---|---|---|
| **Verdict (MET-family)** | `MET` / `PARTIAL` / `NOT_MET` / `UNABLE_TO_DETERMINE` | `homebound`, `primary-diagnosis`, `skilled-services`, `encounter-identity` | A pass/fail criterion evaluation |
| **Extraction** | `EXTRACTED` / `PARTIAL` / `UNABLE_TO_DETERMINE` | `poc-485-extraction`, `telehealth-identity` | Anchors/parameters pulled from a document |
| **Detection** | `INPATIENT_DETECTED` / `OBSERVATION_DETECTED` / `NOT_INPATIENT` / `PARTIAL` / `UNABLE_TO_DETERMINE` | `inpatient-detection` | Which setting was detected |
| **Adequacy** | `ADEQUATE` / `PARTIAL` / `INADEQUATE` / `UNABLE_TO_DETERMINE` | `surgical-note` | Whether a note is fit for F2F use |
| **(none — structural)** | no verdict `status`; per-encounter `classification_confidence` | `classification` | Splits the document into encounters |

Two invariants hold across **all** verdict/extraction/detection/adequacy agents:

- **Confidence must align with status.** Each status has a fixed band (below).
- **`UNABLE_TO_DETERMINE` is always the lowest band.** It means "not enough in
  the document to evaluate," never "evaluated and failed" (that is `NOT_MET` /
  `INADEQUATE`).

---

## 2. Status + confidence matrix

| Agent | `parameter_id` | Status values | Confidence bands |
|---|---|---|---|
| Homebound | `homebound_status` | `MET` / `PARTIAL` / `NOT_MET` / `UNABLE_TO_DETERMINE` | .80–1.00 / .50–.79 / .30–.49 / .00–.29 |
| Primary diagnosis | `primary_diagnosis` | `MET` / `PARTIAL` / `NOT_MET` / `UNABLE_TO_DETERMINE` | .85–1.00 (coded+aligned) · .80–.84 (narrative) / .50–.79 / .30–.49 / .00–.29 |
| Skilled services | `skilled_services` | `MET` / `PARTIAL` / `NOT_MET` / `UNABLE_TO_DETERMINE` | .85–1.00 (all STRONG) · .80–.84 (some MODERATE) / .50–.79 / .30–.49 / .00–.29 |
| Encounter identity | `encounter_identity` | `MET` / `PARTIAL` / `NOT_MET` / `UNABLE_TO_DETERMINE` | per SKILL.md threshold table (MET highest) |
| Surgical note | `surgical_note` | `ADEQUATE` / `PARTIAL` / `INADEQUATE` / `UNABLE_TO_DETERMINE` | .80–1.00 / .50–.79 / .30–.49 / .00–.29 |
| Telehealth identity | `telehealth_identity` | `EXTRACTED` / `PARTIAL` / `UNABLE_TO_DETERMINE` | .80–1.00 / .50–.79 / .00–.49 |
| Inpatient detection | `inpatient_detection` | `INPATIENT_DETECTED` / `OBSERVATION_DETECTED` / `NOT_INPATIENT` / `PARTIAL` / `UNABLE_TO_DETERMINE` | .80–1.00 / .80–1.00 / .70–1.00 / .50–.79 / .00–.49 |
| POC/485 extraction | `poc_485_extraction` | `EXTRACTED` / `PARTIAL` / `UNABLE_TO_DETERMINE` | .80–1.00 / .50–.79 / .00–.49 |
| Classification | *(none)* | *(no verdict status)* | per-encounter `classification_confidence` `0.0–1.0` |

---

## 3. Per-agent detail

Each section lists the status meanings, the confidence bands, the decision rules
(the conditions that produce each status), and the `result` fields that drive
the verdict.

### 3.1 Homebound — `homebound_status`

Per-encounter. Two-prong CMS homebound test.

| Status | Meaning | Confidence |
|---|---|---|
| `MET` | Both prongs satisfied and documented | 0.80 – 1.00 (higher when language is explicit) |
| `PARTIAL` | Homebound language present but insufficient for either prong | 0.50 – 0.79 |
| `NOT_MET` | Evaluated and failed (prong 1 false, or prong 1 true but prong 2 false) | 0.30 – 0.49 |
| `UNABLE_TO_DETERMINE` | No homebound language found in the encounter | 0.00 – 0.29 |

**Decision rules**

| Condition | Status |
|---|---|
| `prong_1.met` AND `prong_2.met` AND documented | `MET` |
| `prong_1.met` = true BUT `prong_2.met` = false | `NOT_MET` |
| `prong_1.met` = false | `NOT_MET` |
| Language present but insufficient for either prong | `PARTIAL` |
| No homebound language in encounter | `UNABLE_TO_DETERMINE` |

**Driving fields:** `result.prong_1.met` (OR of four sub-criteria),
`result.prong_2.met` (AND of `normal_inability_met` + `considerable_effort_met`),
`result.is_documented`.

### 3.2 Primary diagnosis — `primary_diagnosis`

Per-encounter. Also carries a nested `result.alignment.status`
(`ALIGNED` / `PARTIALLY_ALIGNED` / `MISALIGNED`) that feeds the top-level verdict.

| Status | Meaning | Confidence |
|---|---|---|
| `MET` | Specific diagnosis + medical necessity met + aligned with 485 | 0.85 – 1.00 (coded + aligned); 0.80 – 0.84 (narrative only) |
| `PARTIAL` | Specific + necessity met but only `PARTIALLY_ALIGNED` with 485 | 0.50 – 0.79 |
| `NOT_MET` | Misaligned, vague/conclusory/symptom-only, necessity not met, or no diagnosis | 0.30 – 0.49 |
| `UNABLE_TO_DETERMINE` | Document insufficient to evaluate | 0.00 – 0.29 |

**Decision rules**

| Condition | Status |
|---|---|
| Specific + `medical_necessity_met` + `ALIGNED` | `MET` |
| Specific + `medical_necessity_met` + `PARTIALLY_ALIGNED` | `PARTIAL` |
| Specific + `medical_necessity_met` + `MISALIGNED` | `NOT_MET` |
| Specific + `medical_necessity_met` = false | `NOT_MET` |
| Specific + clinical relevance not met | `NOT_MET` |
| `VAGUE` / `CONCLUSORY` / `SYMPTOM_ONLY` | `NOT_MET` |
| No diagnosis documented | `NOT_MET` |
| Document insufficient | `UNABLE_TO_DETERMINE` |

**Driving fields:** `result.f2f_primary_diagnosis.specificity`,
`result.medical_necessity_met`, `result.pathways_met`, `result.alignment.status`,
`result.clinical_relevance_met`.

### 3.3 Skilled services — `skilled_services`

Per-encounter. Evaluates whether ordered disciplines are justified.

| Status | Meaning | Confidence |
|---|---|---|
| `MET` | All qualifying services justified at STRONG or MODERATE | 0.85 – 1.00 (all STRONG); 0.80 – 0.84 (some MODERATE) |
| `PARTIAL` | At least one qualifying service justified; one or more WEAK/ABSENT | 0.50 – 0.79 |
| `NOT_MET` | No qualifying service justified, or only OT/MSS/HHA ordered | 0.30 – 0.49 |
| `UNABLE_TO_DETERMINE` | Document insufficient to evaluate any service | 0.00 – 0.29 |

**Driving fields:** `result.services[].is_justified`,
`result.services[].signal_strength`, `result.poc_ordered_services`.

### 3.4 Encounter identity — `encounter_identity`

Per-encounter. Extracts encounter date, signature, and eligible conducting
provider (with co-sign resolution).

| Status | Meaning |
|---|---|
| `MET` | All three components extracted + provider allowed + co-sign resolved |
| `PARTIAL` | One component low-confidence, or a non-critical flag raised |
| `NOT_MET` | No signature, provider not allowed, or co-sign required but absent |
| `UNABLE_TO_DETERMINE` | Document insufficient to evaluate any component |

Confidence follows the threshold table in the skill's `SKILL.md` (`MET` highest,
`UNABLE_TO_DETERMINE` lowest); it must align with the status.

**Driving fields:** `result.encounter_date`, `result.signature.signed`,
`result.eligible_provider.conducting_provider.is_allowed`,
`result.eligible_provider.cosign` (`is_required` / `is_valid`).

### 3.5 Surgical note — `surgical_note`

Per-encounter (adequacy family — this asks "is this note usable as an F2F
encounter?", not pass/fail of a clinical criterion).

| Status | Meaning | Confidence |
|---|---|---|
| `ADEQUATE` | Valid note type with clinically specific HH content | 0.80 – 1.00 |
| `PARTIAL` | Note type valid but HH content weak or incomplete | 0.50 – 0.79 |
| `INADEQUATE` | Note type invalid (e.g. anesthesia-only, operative-only) or no HH content | 0.30 – 0.49 |
| `UNABLE_TO_DETERMINE` | Note type unknown / document insufficient | 0.00 – 0.29 |

**Decision rules**

| Condition | Status |
|---|---|
| `note_type_valid` AND `hh_relevant_content.found` AND NOT `hh_content_weak` | `ADEQUATE` |
| `note_type_valid` AND `hh_relevant_content.found` AND `hh_content_weak` | `PARTIAL` |
| `note_type_valid` AND `no_hh_content` | `PARTIAL` |
| `pre_op_note` with no post-surgical HH need | `PARTIAL` |
| `note_type` is `anesthesia_note` | `INADEQUATE` |
| `operative_note_only` AND `no_hh_content` | `INADEQUATE` |
| `note_type` is `unknown` | `UNABLE_TO_DETERMINE` |

**Driving fields:** `result.note_type_valid`, `result.hh_relevant_content.found`,
`result.f2f_adequate`, `result.flags.*`.

### 3.6 Telehealth identity — `telehealth_identity`

Per-encounter (extraction family). Runs only on encounters flagged telehealth.

| Status | Meaning | Confidence |
|---|---|---|
| `EXTRACTED` | Telehealth confirmed + all key parameters found | 0.80 – 1.00 |
| `PARTIAL` | Telehealth confirmed but one or more parameters missing | 0.50 – 0.79 |
| `UNABLE_TO_DETERMINE` | No telehealth indicator found | 0.00 – 0.49 |

**Driving fields:** `result.telehealth_indicator.not_found`,
`result.modality.type`, `result.patient_location`, `result.provider_location`,
`result.consent.documented`, `result.conducting_provider`, `result.flags.*`.

### 3.7 Inpatient detection — `inpatient_detection`

Per-encounter (detection family — the status reports *which setting* was found).

| Status | Meaning | Confidence |
|---|---|---|
| `INPATIENT_DETECTED` | `hospital` / `snf` / `post_acute_care` setting confirmed | 0.80 – 1.00 |
| `OBSERVATION_DETECTED` | `hospital_observation` confirmed | 0.80 – 1.00 |
| `NOT_INPATIENT` | Outpatient / physician office / patient home confirmed | 0.70 – 1.00 |
| `PARTIAL` | Setting identified but admission/discharge dates or disposition missing | 0.50 – 0.79 |
| `UNABLE_TO_DETERMINE` | No setting indicators anywhere (`setting_type = unknown`) | 0.00 – 0.49 |

**Decision rules**

| Condition | Status |
|---|---|
| `setting_type` in `hospital` / `snf` / `post_acute_care` | `INPATIENT_DETECTED` |
| `setting_type` = `hospital_observation` | `OBSERVATION_DETECTED` |
| `setting_type` in `outpatient_clinic` / `physician_office` / `patient_home` | `NOT_INPATIENT` |
| Setting identified but dates missing | `PARTIAL` |
| Hospital detected but inpatient vs. observation unclear | `PARTIAL` + `inpatient_status_unclear = true` |
| No setting indicators (`unknown`) | `UNABLE_TO_DETERMINE` |

**Driving fields:** `result.setting_type`, `result.inpatient_flag`,
`result.admission_date`, `result.discharge_date`, `result.flags.*`.

### 3.8 POC / 485 extraction — `poc_485_extraction`

Document-level (extraction family). Pulls the five anchors that seed the F2F run.

| Status | Meaning | Confidence |
|---|---|---|
| `EXTRACTED` | All five anchors found with complete values | 0.80 – 1.00 |
| `PARTIAL` | Some anchors found; one or more missing or incomplete | 0.50 – 0.79 |
| `UNABLE_TO_DETERMINE` | Not a valid 485/POC or no anchors found | 0.00 – 0.49 |

**Anchor-level `rules_applied.cms[].outcome`** uses a separate vocabulary:
`EXTRACTED` / `PARTIAL` / `NOT_FOUND` / `BLOCKED` (see §4).

**Driving fields:** the five anchors — `result.primary_diagnosis`,
`result.skilled_services`, `result.homebound`, `result.f2f_encounter_date`,
`result.certification` (each with a `not_found` flag).

### 3.9 Classification — *(no verdict status)*

Document-level. This agent has **no** pass/fail `status`. It splits the document
into encounters and emits a `classification_confidence` (`0.0 – 1.0`) per
encounter, plus `classification_notes`. There is no MET/EXTRACTED-style verdict
because classification does not audit a criterion — it structures the input for
the per-encounter agents that follow.

**Key fields:** `total_encounters`, `encounters[].encounter_category`,
`encounters[].encounter_subcategory`, `encounters[].classification_confidence`,
`encounters[].classification_notes`.

---

## 4. `rules_applied` outcomes (shared vocabulary)

Independent of the top-level `status`, every agent records how each individual
CMS/client rule evaluated under `rules_applied.cms[]` / `rules_applied.client[]`:

| Outcome | Applies to | Meaning |
|---|---|---|
| `PASSED` | cms + client | Rule evaluated — condition satisfied |
| `FAILED` | cms + client | Rule evaluated — condition not satisfied |
| `NOT_TRIGGERED` | cms + client | Rule/section target not present in encounter |
| `NOT_APPLICABLE` | cms | Rule does not apply (e.g. co-sign not required) — used by `encounter-identity` |
| `BLOCKED` | client only | A client `EXCLUDE`/`REPLACE` directive suppressed a CMS rule |

**Exceptions:**

- `encounter-identity` also allows `UNABLE_TO_DETERMINE` as a rule outcome.
- `poc-485-extraction` rule outcomes use `EXTRACTED` / `PARTIAL` / `NOT_FOUND` /
  `BLOCKED` instead of the PASSED/FAILED set, matching its extraction nature.
- `primary-diagnosis` medical-necessity pathways use `PASSED` /
  `NOT_TRIGGERED` per pathway (A/B/C) under `rules_applied.clinical.pathways[]`.

The per-status `reasoning.status` mirrors the top-level `status`, and
`reasoning.missing` is `null` on the success status (`MET` / `EXTRACTED` /
`ADEQUATE` / `*_DETECTED`) and a gap description otherwise.

---

## 5. How agent status surfaces in `merge-encounters/results.json`

The merge engine (`f2f_orchestration/merge_encounters/merge_engine.py`) consumes each
agent output and projects it into merge topics. Two things happen to `status`:

**a) Per-agent status is copied into the merge topic.** Topic builders that map
to a single verdict agent carry the agent's `status` + `confidence` straight
through:

- `homebound`, `skilled_services`, `inpatient` topics include
  `{encounter_index, status, confidence, reasoning}` and set
  `reasoning.status` from the agent.
- `eligible_practitioners` (encounter-identity) and `primary_hh_reason`
  (primary-diagnosis) carry `confidence` and a `reasoning` block; the verdict
  lives in the envelope `status` so `reasoning.status` is omitted
  (`include_status=False`).
- Encounters an agent did not run on are emitted with `status: null` /
  `confidence: null` and a null reasoning block — never silently dropped.

**b) Gaps roll up into `data_quality`** so an incomplete run can never be shown
as a false PASS:

- `data_quality.failed_agents` — maps an agent to the encounter indices where an
  *expected* agent (per the classification-driven selector) produced **no
  output** or a **critical** validation.
- `data_quality.schema_issues` — every non-empty validation signal
  (`missing_keys` / `repaired_keys` / `dangling_refs`) across per-encounter and
  document-level outputs.

> Note: `data_quality` is derived from **presence and validation**, not from the
> `status` value itself. A `NOT_MET` or `INADEQUATE` verdict is a legitimate,
> fully-evaluated result and does **not** appear in `failed_agents`; only a
> missing/critical output does. Soft failures raised during a pipeline run are
> additionally surfaced in `ResultStore.results["errors"]` for the orchestrator
> (see `docs/integration-and-failure-handling.md`).

---

## 6. Source files

| Agent | Schema |
|---|---|
| Homebound | `skills/homebound/homebound/references/output-schema.md` |
| Primary diagnosis | `skills/primary-diagnosis/primary-diagnosis/references/output-schema.md` |
| Skilled services | `skills/skilled-services/skilled-services/references/output-schema.md` |
| Encounter identity | `skills/encounter-identity/encounter-identity/references/output-schema.md` |
| Surgical note | `skills/surgical-note/surgical-note/references/output-schema.md` |
| Telehealth identity | `skills/telehealth-identity/telehealth-identity/references/output-schema.md` |
| Inpatient detection | `skills/inpatient-detection/inpatient-detection/references/output-schema.md` |
| POC/485 extraction | `skills/poc-485-extraction/poc-485-extraction/references/output-schema.md` |
| Classification | `skills/classification/classification/references/output-schema.md` |
| Merge projection | `f2f_orchestration/merge_encounters/merge_engine.py`, `f2f_orchestration/merge_encounters/key_builders/` |
