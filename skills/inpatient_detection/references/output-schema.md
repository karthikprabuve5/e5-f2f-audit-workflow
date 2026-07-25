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
      "page": 1,
      "not_found": false
    },
    "admission_date": {
      "value": "2026-03-10",
      "raw": "03/10/2026",
      "page": 1,
      "not_found": false
    },
    "discharge_date": {
      "value": "2026-03-23",
      "raw": "03/23/2026",
      "page": 1,
      "not_found": false
    },
    "discharge_disposition": {
      "raw": "Discharge to home with home health services for wound care and PT",
      "direct_to_hh": true,
      "page": 3,
      "not_found": false
    },
    "community_physician": {
      "raw": "Will be followed by Dr. Maria Santos, PCP",
      "page": 3,
      "not_found": false
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
      "verbiage": "Patient admitted to Houston Methodist Hospital on 03/10/2026",
      "page": 1,
      "line_start": 4,
      "line_end": 4,
      "section": "Header",
      "context": "Inpatient setting — hospital admission confirmed",
      "criterion_matched": "IP_SETTING_TYPES",
      "signal_strength": "STRONG"
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
    "sources": [
      {
        "evidence_id": "E001",
        "page": 1,
        "line_start": 4,
        "line_end": 4,
        "description": "Hospital inpatient setting confirmed"
      }
    ],
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
| `reasoning.sources[].evidence_id` | string | links source to evidence array |
| `reasoning.sources[].page` | integer | page number |
| `reasoning.sources[].line_start` | integer | document-level line number |
| `reasoning.sources[].line_end` | integer | document-level line number |
| `reasoning.sources[].description` | string | what this source represents |
| `reasoning.missing` | string \| null | `null` if detected; gap description if PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

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
