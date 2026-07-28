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
      "page": 2,
      "line_start": 45,
      "line_end": 46,
      "section": "Assessment"
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
      "verbiage": "Acute on chronic systolic congestive heart failure",
      "page": 2,
      "line_start": 45,
      "line_end": 46,
      "section": "Assessment",
      "context": "F2F Primary Diagnosis",
      "criterion_matched": "PD_SPECIFICITY",
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
    "clinical": [
      {
        "section_id": "CR_NECESSITY_PATHWAYS",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Pathway A met — acute CHF exacerbation with medication change documented.",
        "negative_finding": null
      }
    ],
    "client": []
  },
  "reasoning": {
    "status": "MET",
    "summary": "The F2F note documents a specific primary diagnosis of acute on chronic systolic CHF, which is the condition driving the home health episode and aligns with the 485 anchor.",
    "sources": [
      {
        "evidence_id": "E001",
        "page": 2,
        "line_start": 45,
        "line_end": 46,
        "description": "F2F primary diagnosis — specificity, relevance, and 485 alignment"
      }
    ],
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
| `result.f2f_primary_diagnosis.page` | integer | from nearest `### Page N` marker |
| `result.f2f_primary_diagnosis.section` | string | clinical section where found |
| `result.f2f_secondary_diagnoses` | array | empty if none; same shape as primary minus specificity |
| `result.poc_diagnosis.source` | string | always `"system_prompt"` |
| `result.poc_diagnosis.icd10_code` | string | `poc_icd10_code` from system prompt |
| `result.poc_diagnosis.icd10_description` | string | `poc_description` from system prompt |
| `result.alignment.status` | enum | `ALIGNED` / `PARTIALLY_ALIGNED` / `MISALIGNED` |
| `result.alignment.basis` | string | one plain English sentence |
| `result.clinical_relevance_met` | boolean | true if F2F diagnosis is the HH driver |
| `result.specificity_met` | boolean | true only if specificity = `SPECIFIC` |
| `result.medical_necessity_met` | boolean | true if at least one pathway A/B/C satisfied |
| `result.pathways_met` | string[] | satisfied pathway codes; empty if none |
| `rules_applied.clinical[].section_id` | string | `CR_*` id from clinical-rules.md |
| `rules_applied.clinical[].outcome` | enum | `PASSED` / `FAILED` / `NOT_TRIGGERED` |
| `rules_applied.clinical[].evidence_refs` | string[] | evidence_ids supporting this outcome |
| `rules_applied.clinical[].detail` | string | one plain English sentence |
| `rules_applied.clinical[].negative_finding` | string \| null | pathways not found; null if PASSED |
| `evidence[].context` | string | `F2F Primary Diagnosis` / `F2F Secondary Diagnosis` |
| `reasoning.missing` | string or null | null if MET; gap description if NOT_MET or PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

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
