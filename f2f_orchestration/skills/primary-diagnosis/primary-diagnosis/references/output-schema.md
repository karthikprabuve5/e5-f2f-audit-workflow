# Output Schema — Primary Diagnosis

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "primary_diagnosis",
  "client_id": "DEFAULT",
  "encounter_index": 1,
  "evaluated_at": "2026-03-10T14:32:00Z",
  "status": "MET",
  "confidence": 0.92,
  "result": {
    "is_documented": true,
    "f2f_primary_diagnosis": {
      "verbatim": "Acute on chronic systolic congestive heart failure",
      "icd10_code": "I50.31",
      "specificity": "SPECIFIC",
      "evidence_refs": ["E001"]
    },
    "f2f_secondary_diagnoses": [],
    "poc_diagnosis": {
      "source": "system_prompt",
      "icd10_code": "I50.31",
      "icd10_description": "Acute on chronic systolic (congestive) heart failure"
    },
    "alignment": {
      "status": "ALIGNED",
      "basis": "F2F and 485 both document I50.31; descriptions are clinically consistent."
    },
    "clinical_relevance_met": true,
    "specificity_met": true,
    "medical_necessity_met": true,
    "pathways_met": ["A"]
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "field": "f2f_primary_diagnosis",
      "verbiage": "Acute on chronic systolic congestive heart failure",
      "page": 2,
      "line_start": 45,
      "line_end": 46,
      "section": "Assessment",
      "context": "F2F Primary Diagnosis",
      "criterion_matched": "PD_SPECIFICITY",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E002",
      "field": "pathways_met",
      "verbiage": "Discharged 5 days ago following acute CHF exacerbation, 12 lb weight gain with worsening dyspnea.",
      "page": 2,
      "line_start": 51,
      "line_end": 52,
      "section": "History of Present Illness",
      "context": "Medical Necessity — Pathway A",
      "criterion_matched": "CR_NECESSITY_PATHWAYS",
      "signal_strength": "STRONG"
    }
  ],
  "rules_applied": {
    "cms": [
      {
        "section_id": "PD_F2F_DOCUMENTATION",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "F2F note documents a specific clinical diagnosis related to the home health need.",
        "negative_finding": null
      },
      {
        "section_id": "PD_SPECIFICITY",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Diagnosis is named with type and acuity descriptor; not conclusory or vague.",
        "negative_finding": null
      },
      {
        "section_id": "PD_CLINICAL_RELEVANCE",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Systolic CHF is the condition driving the ordered skilled nursing services.",
        "negative_finding": null
      },
      {
        "section_id": "PD_POC_ALIGNMENT",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "F2F diagnosis matches 485 anchor code I50.31 exactly.",
        "negative_finding": null
      }
    ],
    "clinical": {
      "summary": "Recent acute CHF exacerbation with 12 lb weight gain and worsening dyspnea; clinical instability requiring skilled nursing monitoring and medication management.",
      "evidence_refs": ["E002"],
      "pathways": [
        {
          "section_id": "CR_NECESSITY_PATHWAYS",
          "pathway": "A",
          "outcome": "PASSED",
          "evidence_refs": ["E002"],
          "detail": "Pathway A met — acute CHF exacerbation with 12 lb weight gain and worsening dyspnea documented.",
          "negative_finding": null
        },
        {
          "section_id": "CR_NECESSITY_PATHWAYS",
          "pathway": "B",
          "outcome": "NOT_TRIGGERED",
          "evidence_refs": [],
          "detail": "Pathway B was searched but not established for the primary diagnosis.",
          "negative_finding": "Pathway B (new/changed medication) not found."
        },
        {
          "section_id": "CR_NECESSITY_PATHWAYS",
          "pathway": "C",
          "outcome": "NOT_TRIGGERED",
          "evidence_refs": [],
          "detail": "Pathway C was searched but not established for the primary diagnosis.",
          "negative_finding": "Pathway C (explicit skilled order / safety risk) not found."
        }
      ]
    },
    "client": []
  },
  "reasoning": {
    "status": "MET",
    "summary": "The F2F note documents a specific primary diagnosis of acute on chronic systolic CHF, which is the condition driving the home health episode and aligns with the 485 anchor.",
    "evidence_refs": ["E001"],
    "missing": null,
    "agency_warnings": []
  }
}
```

---

## Field Rules

| Field | Type | Rule |
|-------|------|------|
| `parameter_id` | string | always `"primary_diagnosis"` |
| `status` | enum | `MET` / `NOT_MET` / `PARTIAL` / `UNABLE_TO_DETERMINE` |
| `result.is_documented` | boolean | true if any named diagnosis found in F2F note |
| `result.f2f_primary_diagnosis` | object or null | null only if is_documented = false |
| `result.f2f_primary_diagnosis.verbatim` | string | exact copy — never paraphrase |
| `result.f2f_primary_diagnosis.icd10_code` | string or null | as written in document; null if absent |
| `result.f2f_primary_diagnosis.specificity` | enum | `SPECIFIC` / `VAGUE` / `CONCLUSORY` / `SYMPTOM_ONLY` |
| `result.f2f_primary_diagnosis.evidence_refs` | string[] | evidence_ids grounding the diagnosis (page/line/verbiage live in `evidence[]`) |
| `result.f2f_secondary_diagnoses` | array | empty if none; same shape as primary minus specificity, each with `evidence_refs` |
| `result.poc_diagnosis.source` | string | always `"system_prompt"` — anchor from prompt, not the F2F doc; carries no `evidence_refs` |
| `result.poc_diagnosis.icd10_code` | string | `poc_icd10_code` from system prompt |
| `result.poc_diagnosis.icd10_description` | string | `poc_description` from system prompt |
| `result.alignment.status` | enum | `ALIGNED` / `PARTIALLY_ALIGNED` / `MISALIGNED` |
| `result.alignment.basis` | string | one plain English sentence |
| `result.clinical_relevance_met` | boolean | true if F2F diagnosis is the HH driver |
| `result.specificity_met` | boolean | true only if specificity = `SPECIFIC` |
| `result.medical_necessity_met` | boolean | true if at least one pathway A/B/C satisfied |
| `result.pathways_met` | string[] | satisfied pathway codes; empty if none |
| `rules_applied.clinical` | object | `{summary, evidence_refs, pathways[]}` — not a bare array |
| `rules_applied.clinical.summary` | string | plain-English findings summary of medical necessity; **do NOT name pathways** ("Pathway A/C met") — describe the clinical findings |
| `rules_applied.clinical.evidence_refs` | string[] | union of every `PASSED` pathway's evidence ids (deduplicated); `NOT_TRIGGERED` pathways contribute nothing |
| `rules_applied.clinical.pathways` | array | one entry per pathway evaluated (A, B, C) |
| `rules_applied.clinical.pathways[].section_id` | string | always `CR_NECESSITY_PATHWAYS` |
| `rules_applied.clinical.pathways[].pathway` | enum | `A` / `B` / `C` |
| `rules_applied.clinical.pathways[].outcome` | enum | `PASSED` (satisfied) / `NOT_TRIGGERED` (searched, not found) |
| `rules_applied.clinical.pathways[].evidence_refs` | string[] | on PASSED: a distinct evidence_id quoting THIS pathway's F2F language (never reuse the diagnosis evidence E001); on NOT_TRIGGERED: `[]` |
| `rules_applied.clinical.pathways[].detail` | string | one plain English sentence |
| `rules_applied.clinical.pathways[].negative_finding` | string \| null | null on PASSED; on NOT_TRIGGERED, states the pathway was searched but not found |
| `evidence[].field` | string | result path this evidence primarily documents (e.g. `f2f_primary_diagnosis`) |
| `evidence[].context` | string | `F2F Primary Diagnosis` / `F2F Secondary Diagnosis` |
| `reasoning.evidence_refs` | string[] | evidence_ids cited by the summary (replaces the old `sources` objects) |
| `reasoning.missing` | string or null | null if MET; gap description if NOT_MET or PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

## Evidence & Traceability

`evidence[]` is the **single source of truth** for all location data. Every entry carries the exact `verbiage`, `page`, `line_start`, `line_end`, and `section`. Everything else references it by `evidence_id` — no other section repeats page/line/verbiage.

- **Documented result values** (`f2f_primary_diagnosis`, `f2f_secondary_diagnoses[]`) MUST carry `evidence_refs` pointing at real `evidence[]` entries.
- **Absent / derived / prompt-anchor** values carry `evidence_refs: []` or omit it — there is no F2F text to cite (`poc_diagnosis` comes from the system prompt; `alignment` and `*_met` booleans are derived). The `pathways_met` code list is also derived — its supporting quotes live in `rules_applied.clinical.pathways[]`, one distinct `evidence[]` entry per satisfied pathway, and `rules_applied.clinical.evidence_refs` is the union of those.
- **Reuse `evidence_id`s**: when several values are grounded by the same quote, all reference the same `E00x`; do not mint a new entry per field.
- Every `E00x` referenced anywhere MUST exist in `evidence[]` (no dangling refs). Inline `page`/`line`/`section` on result values has been removed — resolve location through `evidence_refs`.

---

## Confidence Bands

| Status | Range |
|--------|-------|
| `MET` — coded + aligned | 0.85 – 1.00 |
| `MET` — narrative only | 0.80 – 0.84 |
| `PARTIAL` | 0.50 – 0.79 |
| `NOT_MET` | 0.30 – 0.49 |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.29 |

## Status Decision Rules

| Condition | status |
|-----------|--------|
| Specific + medical_necessity_met + ALIGNED | `MET` |
| Specific + medical_necessity_met + PARTIALLY_ALIGNED | `PARTIAL` |
| Specific + medical_necessity_met + MISALIGNED | `NOT_MET` |
| Specific + medical_necessity_met = false (only disqualifying language) | `NOT_MET` |
| Specific + clinical relevance NOT met | `NOT_MET` |
| VAGUE / CONCLUSORY / SYMPTOM_ONLY | `NOT_MET` |
| No diagnosis documented | `NOT_MET` |
| Document insufficient to evaluate | `UNABLE_TO_DETERMINE` |

Evaluate all CMS and clinical sections regardless of earlier results. Do not short-circuit.
