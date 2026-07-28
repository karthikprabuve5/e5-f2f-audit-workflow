# Output Schema — Homebound Status

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "homebound_status",
  "client_id": "DEFAULT",
  "encounter_index": 1,
  "evaluated_at": "2026-03-10T14:32:00Z",
  "status": "MET",
  "confidence": 0.95,
  "result": {
    "is_documented": true,
    "prong_1": {
      "met": true,
      "criteria_met": ["device_needed", "assistance_of_person"],
      "criteria_evaluated": [
        "device_needed",
        "special_transport",
        "assistance_of_person",
        "medically_contraindicated"
      ]
    },
    "prong_2": {
      "met": true,
      "normal_inability_met": true,
      "considerable_effort_met": true
    },
    "allowable_absences_noted": false,
    "allowable_absences": [
      {
        "verbiage": "exact text from markdown",
        "page": 2,
        "line_start": 30,
        "line_end": 30,
        "absence_type": "MEDICAL",
        "is_allowable": true,
        "reason": "Outpatient dialysis — allowable per MBPM Ch.7 §30.1.1"
      }
    ]
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "verbiage": "exact text from markdown, character for character",
      "page": 2,
      "line_start": 45,
      "line_end": 46,
      "section": "Assessment",
      "context": "Homebound Statement — Prong 1",
      "criterion_matched": "HB_CRITERIA_ONE",
      "signal_strength": "STRONG"
    }
  ],
  "rules_applied": {
    "cms": [
      {
        "section_id": "HB_CRITERIA_ONE",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Patient requires walker and assistance to leave home.",
        "negative_finding": null
      }
    ],
    "client": [
      {
        "directive_id": "HB-001",
        "directive_type": "ELEVATE",
        "anchored_to": "HB_CRITERIA_TWO",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Walker mentioned alongside considerable effort language.",
        "negative_finding": null
      }
    ]
  },
  "reasoning": {
    "status": "MET",
    "summary": "Clinical findings support homebound status. Both prongs satisfied.",
    "sources": [
      {
        "evidence_id": "E001",
        "page": 2,
        "line_start": 45,
        "line_end": 46,
        "description": "Prong 1 — assistive device need"
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
| `schema_version` | string | always `"1.0"` — increment on schema changes |
| `parameter_id` | string | always `"homebound_status"` |
| `client_id` | string | from system prompt; `"DEFAULT"` if no client |
| `encounter_index` | integer | from classification output |
| `evaluated_at` | string | ISO 8601 runtime timestamp |
| `status` | enum | `MET` / `NOT_MET` / `PARTIAL` / `UNABLE_TO_DETERMINE` |
| `confidence` | float | 0.0 – 1.0; must align with status — see Confidence Bands |
| `result.is_documented` | boolean | true if any homebound language found |
| `result.prong_1.met` | boolean | true if ANY ONE Prong 1 sub-criterion present (OR logic) |
| `result.prong_1.criteria_met` | string[] | sub-criteria that were found: device_needed / special_transport / assistance_of_person / medically_contraindicated |
| `result.prong_1.criteria_evaluated` | string[] | all four sub-criteria always listed |
| `result.prong_2.met` | boolean | true only if BOTH Prong 2 sub-criteria present (AND logic) |
| `result.prong_2.normal_inability_met` | boolean | true if normal inability to leave home documented |
| `result.prong_2.considerable_effort_met` | boolean | true if considerable and taxing effort documented |
| `result.allowable_absences_noted` | boolean | true if any absence mentioned |
| `result.allowable_absences` | array | empty if none; structure shown in JSON above |
| `evidence[].evidence_id` | string | unique ID starting E001; used for cross-referencing |
| `evidence[].verbiage` | string | exact copy from markdown — never paraphrase |
| `evidence[].page` | integer | from nearest preceding `### Page N` marker |
| `evidence[].line_start` | integer | document-level line number |
| `evidence[].line_end` | integer | document-level line number |
| `evidence[].section` | string | clinical section where found (Assessment / HPI / Plan / Orders) |
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
| `reasoning.summary` | string | clinical findings only; no PII; no inline references; 1-2 sentences |
| `reasoning.sources[].evidence_id` | string | links source to evidence array |
| `reasoning.sources[].page` | integer | page number |
| `reasoning.sources[].line_start` | integer | document-level line number |
| `reasoning.sources[].line_end` | integer | document-level line number |
| `reasoning.sources[].description` | string | what this source represents |
| `reasoning.missing` | string \| null | null if MET; gap description if NOT_MET or PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

## Confidence Bands

| Status | Range | Guidance |
|--------|-------|---------|
| `MET` | 0.80 – 1.00 | Higher when language is explicit and specific |
| `PARTIAL` | 0.50 – 0.79 | Higher when closer to MET; lower when closer to NOT_MET |
| `NOT_MET` | 0.30 – 0.49 | Higher when clearly evaluated and failed |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.29 | Higher when encounter clearly lacks content |

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
| prong_1.met AND prong_2.met AND documented | `MET` |
| prong_1.met BUT prong_2.met = false | `NOT_MET` |
| prong_1.met = false | `NOT_MET` |
| Language present but insufficient for either prong | `PARTIAL` |
| No homebound language found in encounter | `UNABLE_TO_DETERMINE` |
