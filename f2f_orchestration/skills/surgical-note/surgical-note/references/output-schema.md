# Output Schema — Surgical Note Validation

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "surgical_note",
  "client_id": "DEFAULT",
  "encounter_index": 1,
  "evaluated_at": "2026-03-23T14:32:00Z",
  "status": "ADEQUATE",
  "confidence": 0.91,
  "result": {
    "note_type": "post_op_note",
    "note_type_valid": true,
    "note_type_evidence_refs": ["E001"],
    "surgical_procedure": {
      "raw": "Right total knee arthroplasty",
      "not_found": false,
      "evidence_refs": ["E003"]
    },
    "setting_type": "hospital_or",
    "hh_relevant_content": {
      "found": true,
      "items": [
        {
          "evidence_refs": ["E002"]
        }
      ]
    },
    "f2f_adequate": true,
    "flags": {
      "anesthesia_only": false,
      "operative_note_only": false,
      "no_hh_content": false,
      "procedure_only": false,
      "hh_content_weak": false,
      "discharge_summary_hh_referenced": false
    }
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "field": "note_type",
      "verbiage": "Post-Operative Day 2 — Patient recovering well. Wound intact.",
      "page": 1,
      "line_start": 3,
      "line_end": 3,
      "section": "Header",
      "context": "Note type — post-operative clinical assessment",
      "criterion_matched": "SN_NOTE_TYPE",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E002",
      "field": "hh_relevant_content",
      "verbiage": "Patient will require home PT 3x/week for gait training and wound care daily",
      "page": 2,
      "line_start": 45,
      "line_end": 45,
      "section": "Plan",
      "context": "HH-relevant content — skilled PT and wound care ordered",
      "criterion_matched": "SN_HH_CONTENT",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E003",
      "field": "surgical_procedure",
      "verbiage": "Procedure: Right total knee arthroplasty",
      "page": 1,
      "line_start": 5,
      "line_end": 5,
      "section": "Header",
      "context": "Surgical procedure performed",
      "criterion_matched": "SN_NOTE_TYPE",
      "signal_strength": "STRONG"
    }
  ],
  "rules_applied": {
    "cms": [
      {
        "section_id": "SN_NOTE_TYPE",
        "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Post-operative note is a valid F2F encounter document.",
        "negative_finding": null
      },
      {
        "section_id": "SN_F2F_CONTENT",
        "outcome": "PASSED",
        "evidence_refs": ["E002"],
        "detail": "Clinical findings support HH need — skilled PT and wound care documented.",
        "negative_finding": null
      }
    ],
    "client": []
  },
  "reasoning": {
    "status": "ADEQUATE",
    "summary": "Post-operative note documents clinical encounter with specific skilled PT and wound care requirements supporting HH certification.",
    "evidence_refs": ["E001", "E002", "E003"],
    "missing": null,
    "agency_warnings": []
  }
}
```

## Field Rules

| Field | Type | Rule |
|-------|------|------|
| `schema_version` | string | always `"1.0"` — increment on schema changes |
| `parameter_id` | string | always `"surgical_note"` |
| `client_id` | string | from system prompt; `"DEFAULT"` if no client |
| `encounter_index` | integer | from classification output |
| `evaluated_at` | string | ISO 8601 runtime timestamp |
| `status` | enum | see Status Decision Rules |
| `confidence` | float | 0.0 – 1.0; must align with status — see Confidence Bands |
| `result.note_type` | enum | `pre_op_note` / `operative_note` / `post_op_note` / `anesthesia_note` / `surgical_consult` / `discharge_summary` / `unknown` |
| `result.note_type_valid` | boolean | `true` for `post_op_note` / `surgical_consult` / `discharge_summary`; CONDITIONAL for `pre_op_note` and `operative_note` (depends on HH content present); `false` for `anesthesia_note` |
| `result.note_type_evidence_refs` | string[] | evidence_ids grounding the note-type determination; `[]` if `unknown` |
| `result.surgical_procedure.raw` | string \| null | verbatim procedure name; `null` if not found |
| `result.surgical_procedure.not_found` | boolean | `true` if no procedure name found |
| `result.surgical_procedure.evidence_refs` | string[] | evidence_ids grounding the procedure; `[]` if `not_found` |
| `result.setting_type` | enum | `hospital_or` / `asc` / `hospital_outpatient` / `physician_office` / `unknown` |
| `result.hh_relevant_content.found` | boolean | `true` if ANY HH-related clinical content found |
| `result.hh_relevant_content.items` | array | each item: `evidence_refs` only (verbiage/page/line live in `evidence[]`); empty if not found |
| `result.f2f_adequate` | boolean | `true` only when note_type_valid AND hh content found AND content not weak |
| `result.flags.anesthesia_only` | boolean | `true` if note_type is `anesthesia_note` |
| `result.flags.operative_note_only` | boolean | `true` if operative note with no embedded clinical assessment |
| `result.flags.no_hh_content` | boolean | `true` if no HH-relevant content found anywhere |
| `result.flags.procedure_only` | boolean | `true` if document contains only procedural and intraoperative data |
| `result.flags.hh_content_weak` | boolean | `true` if HH content found but vague/conclusory |
| `result.flags.discharge_summary_hh_referenced` | boolean | `true` if discharge summary explicitly names HH services |
| `evidence[].evidence_id` | string | unique ID starting E001; used for cross-referencing |
| `evidence[].field` | string | result path this evidence primarily documents (e.g. `note_type`, `hh_relevant_content`, `surgical_procedure`) |
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
| `reasoning.summary` | string | clinical findings only; no PII; no inline references; 1-2 sentences |
| `reasoning.evidence_refs` | string[] | evidence_ids cited by the summary (replaces the old `sources` objects) |
| `reasoning.missing` | string \| null | `null` if ADEQUATE; gap description if INADEQUATE or PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

## Evidence & Traceability

`evidence[]` is the **single source of truth** for all location data. Every entry carries the exact `verbiage`, `page`, `line_start`, `line_end`, and `section`. Everything else references it by `evidence_id` — no other section repeats page/line/verbiage.

- **Documented result values** (`note_type` via `note_type_evidence_refs`, `surgical_procedure`, `hh_relevant_content.items[]`) MUST carry `evidence_refs` pointing at real `evidence[]` entries.
- **Absent / not-found / derived** values carry `evidence_refs: []` — there is no text to cite (`setting_type`, `note_type_valid`, `f2f_adequate`, and all `flags.*` are derived; rely on `rules_applied.*.negative_finding`).
- **Reuse `evidence_id`s**: when several values are grounded by the same quote, all reference the same `E00x`; do not mint a new entry per field.
- Every `E00x` referenced anywhere MUST exist in `evidence[]` (no dangling refs). Inline `page`/`line`/`verbiage` on result values has been removed — resolve location through `evidence_refs`.

## Confidence Bands

| Status | Range | Guidance |
|--------|-------|---------|
| `ADEQUATE` | 0.80 – 1.00 | Valid note type with clinically specific HH content |
| `PARTIAL` | 0.50 – 0.79 | Note type valid but HH content weak or incomplete |
| `INADEQUATE` | 0.30 – 0.49 | Note type invalid or no HH content found |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.29 | Note type unknown or document insufficient for evaluation |

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
| note_type_valid AND hh_relevant_content.found AND NOT hh_content_weak | `ADEQUATE` |
| note_type_valid AND hh_relevant_content.found AND hh_content_weak | `PARTIAL` |
| note_type_valid AND no_hh_content | `PARTIAL` |
| `pre_op_note` with no post-surgical HH need documented | `PARTIAL` |
| note_type is `anesthesia_note` | `INADEQUATE` |
| `operative_note_only` AND no_hh_content | `INADEQUATE` |
| note_type is `unknown` | `UNABLE_TO_DETERMINE` |
