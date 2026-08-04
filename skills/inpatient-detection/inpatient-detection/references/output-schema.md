# Output Schema — Inpatient Detection

## JSON Structure

```json
{
  "schema_version": "1.1",
  "parameter_id": "inpatient_detection",
  "client_id": "DEFAULT",
  "encounter_index": 1,
  "evaluated_at": "2026-03-23T14:32:00Z",
  "status": "INPATIENT_DETECTED",
  "confidence": 0.92,
  "result": {
    "inpatient_flag": true,
    "setting_type": "hospital",
    "facility_name": {
      "raw": "Houston Methodist Hospital",
      "not_found": false,
      "evidence_refs": ["E001"]
    },
    "admission_date": {
      "value": "2026-03-10",
      "raw": "03/10/2026",
      "not_found": false,
      "evidence_refs": ["E001"]
    },
    "discharge_date": {
      "value": "2026-03-23",
      "raw": "03/23/2026",
      "not_found": false,
      "evidence_refs": ["E002"]
    },
    "discharge_disposition": {
      "raw": "Discharge to home with home health services for wound care and PT",
      "direct_to_hh": true,
      "not_found": false,
      "evidence_refs": ["E002"]
    },
    "community_physician": {
      "raw": "Will be followed by Dr. Maria Santos, PCP",
      "not_found": false,
      "evidence_refs": ["E003"]
    },
    "flags": {
      "inpatient_flag": true,
      "observation_status_flagged": false,
      "inpatient_status_unclear": false,
      "no_setting_documented": false,
      "no_admission_date": false,
      "no_discharge_date": false,
      "direct_to_hh": true,
      "community_physician_absent": false,
      "part_a_signal": false
    }
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "field": "admission_date",
      "verbiage": "Patient admitted to Houston Methodist Hospital on 03/10/2026",
      "page": 1,
      "line_start": 4,
      "line_end": 4,
      "section": "Header",
      "context": "Inpatient setting — hospital admission confirmed",
      "criterion_matched": "IP_SETTING_TYPES",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E002",
      "field": "discharge_disposition",
      "verbiage": "Discharge to home with home health services for wound care and PT on 03/23/2026",
      "page": 3,
      "line_start": 51,
      "line_end": 52,
      "section": "Discharge Plan",
      "context": "Discharge date and disposition — direct to home health",
      "criterion_matched": "IP_INPATIENT_EXCLUSION",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E003",
      "field": "community_physician",
      "verbiage": "Will be followed by Dr. Maria Santos, PCP",
      "page": 3,
      "line_start": 58,
      "line_end": 58,
      "section": "Discharge Plan",
      "context": "Community follow-up physician named",
      "criterion_matched": "IP_INPATIENT_EXCLUSION",
      "signal_strength": "MODERATE"
    }
  ],
  "rules_applied": {
    "cms": [
      {
        "section_id": "IP_TWO_MIDNIGHT",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Hospital inpatient admission confirmed — inpatient flag set.",
        "negative_finding": null
      },
      {
        "section_id": "IP_INPATIENT_EXCLUSION",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Inpatient hospital setting detected — discharge date captured for audit engine overlap check.",
        "negative_finding": null
      }
    ],
    "client": []
  },
  "reasoning": {
    "status": "INPATIENT_DETECTED",
    "summary": "F2F encounter conducted in acute hospital setting with confirmed admission. Patient discharged directly to home health.",
    "evidence_refs": ["E001", "E002", "E003"],
    "missing": null,
    "agency_warnings": []
  }
}
```

## Field Rules

| Field | Type | Rule |
|-------|------|------|
| `schema_version` | string | always `"1.1"` — increment on schema changes |
| `parameter_id` | string | always `"inpatient_detection"` |
| `client_id` | string | from system prompt; `"DEFAULT"` if no client |
| `encounter_index` | integer | from classification output |
| `evaluated_at` | string | ISO 8601 runtime timestamp |
| `status` | enum | see Status Decision Rules |
| `confidence` | float | 0.0 – 1.0; must align with status — see Confidence Bands |
| `result.inpatient_flag` | boolean | `true` only for `hospital` / `snf` / `post_acute_care`; `false` for `hospital_observation` |
| `result.setting_type` | enum | `hospital` / `hospital_observation` / `snf` / `post_acute_care` / `outpatient_clinic` / `physician_office` / `patient_home` / `unknown` |
| `result.facility_name.raw` | string \| null | verbatim facility name; `null` if not found |
| `result.admission_date.value` | string \| null | ISO 8601; `null` if not found |
| `result.admission_date.raw` | string \| null | exact text as found in document |
| `result.discharge_date.value` | string \| null | ISO 8601; `null` if not found |
| `result.discharge_date.raw` | string \| null | exact text as found in document |
| `result.discharge_disposition.raw` | string \| null | full verbatim disposition text |
| `result.discharge_disposition.direct_to_hh` | boolean | `true` if disposition references home health |
| `result.community_physician.raw` | string \| null | verbatim follow-up physician text; `null` if not found |
| `result.community_physician.not_found` | boolean | `true` if `direct_to_hh` true but no physician identified |
| `result.<field>.evidence_refs` | string[] | evidence_ids grounding `facility_name` / `admission_date` / `discharge_date` / `discharge_disposition` / `community_physician`; `[]` when `not_found` (page/line live in `evidence[]`) |
| `result.flags.inpatient_flag` | boolean | mirrors `result.inpatient_flag` |
| `result.flags.observation_status_flagged` | boolean | `true` when setting_type is `hospital_observation` |
| `result.flags.inpatient_status_unclear` | boolean | `true` when hospital detected but status not documented |
| `result.flags.no_setting_documented` | boolean | `true` when setting_type is `unknown` |
| `result.flags.no_admission_date` | boolean | `true` if inpatient_flag true and no admission date |
| `result.flags.no_discharge_date` | boolean | `true` if inpatient_flag true and no discharge date |
| `result.flags.direct_to_hh` | boolean | mirrors `discharge_disposition.direct_to_hh` |
| `result.flags.community_physician_absent` | boolean | `true` if direct_to_hh true and no follow-up physician named |
| `result.flags.part_a_signal` | boolean | `true` if explicit Part A billing language found |
| `evidence[].evidence_id` | string | unique ID starting E001; used for cross-referencing |
| `evidence[].field` | string | result path this evidence primarily documents (e.g. `admission_date`, `community_physician`) |
| `evidence[].verbiage` | string | exact copy from markdown — never paraphrase |
| `evidence[].page` | integer | from nearest preceding `### Page N` marker |
| `evidence[].line_start` | integer | document-level line number |
| `evidence[].line_end` | integer | document-level line number |
| `evidence[].section` | string | document section where found |
| `evidence[].context` | string | auditor label for what this evidence represents |
| `evidence[].criterion_matched` | string | cms_section_id this evidence satisfies |
| `evidence[].signal_strength` | enum | `STRONG` / `WEAK` / `INCONCLUSIVE` |
| `rules_applied.cms[].section_id` | string | cms_section_id from cms-rules.md |
| `rules_applied.cms[].outcome` | enum | see Outcome Values table |
| `rules_applied.cms[].evidence_refs` | string[] | evidence_ids supporting this outcome; empty if NOT_TRIGGERED |
| `rules_applied.cms[].detail` | string | one plain English sentence |
| `rules_applied.cms[].negative_finding` | string \| null | what was looked for but not found; null if PASSED |
| `rules_applied.client[].directive_id` | string | directive ID from client-rules.md |
| `rules_applied.client[].directive_type` | enum | `ELEVATE` / `EXTEND` / `EXCLUDE` / `REPLACE` |
| `rules_applied.client[].anchored_to` | string | cms_section_id this directive targets |
| `rules_applied.client[].outcome` | enum | see Outcome Values table |
| `rules_applied.client[].evidence_refs` | string[] | evidence_ids supporting this outcome |
| `rules_applied.client[].detail` | string | one plain English sentence |
| `rules_applied.client[].negative_finding` | string \| null | what was looked for but not found; null if PASSED |
| `reasoning.status` | enum | same as top-level `status` |
| `reasoning.summary` | string | findings only; no PII; no inline references; 1-2 sentences |
| `reasoning.evidence_refs` | string[] | evidence_ids cited by the summary (replaces the old `sources` objects) |
| `reasoning.missing` | string \| null | `null` if detected; gap description if PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

## Evidence & Traceability

`evidence[]` is the **single source of truth** for all location data. Every entry carries the exact `verbiage`, `page`, `line_start`, `line_end`, and `section`. Everything else references it by `evidence_id` — no other section repeats page/line/verbiage.

- **Documented result values** (`facility_name`, `admission_date`, `discharge_date`, `discharge_disposition`, `community_physician`) MUST carry `evidence_refs` pointing at real `evidence[]` entries.
- **Absent / not-found / derived** values carry `evidence_refs: []` — there is no text to cite (`setting_type`, `inpatient_flag`, and all `flags.*` are derived; rely on `rules_applied.*.negative_finding`).
- **Reuse `evidence_id`s**: when several values are grounded by the same quote, all reference the same `E00x`; do not mint a new entry per field.
- Every `E00x` referenced anywhere MUST exist in `evidence[]` (no dangling refs). Inline `page` on result values has been removed — resolve location through `evidence_refs`.

## Confidence Bands

| Status | Range | Guidance |
|--------|-------|---------|
| `INPATIENT_DETECTED` | 0.80 – 1.00 | Setting confirmed with clear facility and date signals |
| `OBSERVATION_DETECTED` | 0.80 – 1.00 | Observation language clearly confirmed |
| `NOT_INPATIENT` | 0.70 – 1.00 | Outpatient or home setting clearly confirmed |
| `PARTIAL` | 0.50 – 0.79 | Setting identified but dates or disposition missing |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.49 | No setting indicators anywhere in document |

## Outcome Values

| Outcome | Applies To | Meaning |
|---------|-----------|---------|
| `PASSED` | cms + client | Rule evaluated — condition satisfied |
| `FAILED` | cms + client | Rule evaluated — condition not satisfied |
| `NOT_TRIGGERED` | cms + client | Section or directive target not found in encounter |
| `BLOCKED` | client only | EXCLUDE or REPLACE targeted CMS regulation — not applied |

## Status Decision Rules

| Condition | status |
|-----------|--------|
| setting_type is `hospital` / `snf` / `post_acute_care` | `INPATIENT_DETECTED` |
| setting_type is `hospital_observation` | `OBSERVATION_DETECTED` |
| setting_type is `outpatient_clinic` / `physician_office` / `patient_home` | `NOT_INPATIENT` |
| Setting identified but admission or discharge dates missing | `PARTIAL` |
| Hospital detected but inpatient vs. observation unclear | `PARTIAL` + `inpatient_status_unclear = true` |
| No setting indicators found (`unknown`) | `UNABLE_TO_DETERMINE` |
