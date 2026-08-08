# Output Schema — Telehealth Identity
# parameter_id: telehealth_identity | schema_version: 1.0

---

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "telehealth_identity",
  "client_id": "DEFAULT",
  "encounter_index": 1,
  "evaluated_at": "2026-01-15T14:32:00Z",
  "status": "EXTRACTED",
  "confidence": 0.90,
  "result": {
    "telehealth_indicator": {
      "keyword": "Video Visit", "verbatim": "Video Visit via Zoom for Healthcare",
      "not_found": false, "evidence_refs": ["E001"]
    },
    "modality": {
      "type": "audio_video", "raw": "audio and video connection established",
      "not_found": false, "evidence_refs": ["E001"]
    },
    "platform": { "name": "Zoom for Healthcare", "raw": "Zoom for Healthcare", "not_found": false, "evidence_refs": ["E001"] },
    "patient_location": { "raw": "Patient home — 123 Main St, Houston TX", "not_found": false, "evidence_refs": ["E003"] },
    "provider_location": { "raw": "Distant site — ABC Medical Clinic, Houston TX", "not_found": false, "evidence_refs": ["E004"] },
    "consent": { "documented": true, "raw": "Patient consented to telehealth visit", "not_found": false, "evidence_refs": ["E002"] },
    "conducting_provider": {
      "name_raw": "Smith, John", "name_format": "LNAME_FNAME",
      "display_name": "John Smith, MD", "credentials": "MD",
      "provider_type": "physician_md_do", "not_found": false, "evidence_refs": ["E005"]
    },
    "signature": {
      "is_signed": true,
      "signers": [
        {
          "name_raw": "John Smith MD", "name_format": "FNAME_LNAME",
          "display_name": "John Smith, MD", "credentials": "MD",
          "signature_type": "electronic", "date_signed": "2026-01-15",
          "is_primary": true, "evidence_refs": ["E005"]
        }
      ],
      "not_found": false
    },
    "flags": {
      "audio_only_flagged": false,
      "no_modality_documented": false,
      "no_patient_location": false,
      "no_provider_location": false,
      "no_consent": false,
      "synchronous_not_confirmed": false
    }
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "field": "modality",
      "verbiage": "Video Visit via Zoom for Healthcare",
      "page": 1, "line_start": 3, "line_end": 3, "section": "Header",
      "context": "Telehealth indicator confirmed — audio+video modality",
      "criterion_matched": "TH_MODALITY", "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E002",
      "field": "consent",
      "verbiage": "Patient consented to telehealth visit",
      "page": 1, "line_start": 6, "line_end": 6, "section": "Header",
      "context": "Telehealth consent documented",
      "criterion_matched": "TH_CONSENT", "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E003",
      "field": "patient_location",
      "verbiage": "Patient home — 123 Main St, Houston TX",
      "page": 1, "line_start": 4, "line_end": 4, "section": "Header",
      "context": "Patient (originating site) location",
      "criterion_matched": "TH_LOCATION", "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E004",
      "field": "provider_location",
      "verbiage": "Distant site — ABC Medical Clinic, Houston TX",
      "page": 1, "line_start": 5, "line_end": 5, "section": "Header",
      "context": "Provider (distant site) location",
      "criterion_matched": "TH_LOCATION", "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E005",
      "field": "conducting_provider",
      "verbiage": "Electronically signed by: John Smith, MD — 01/15/2026",
      "page": 3, "line_start": 40, "line_end": 40, "section": "Signature Block",
      "context": "Conducting provider — electronic signature",
      "criterion_matched": "TH_MODALITY", "signal_strength": "STRONG"
    }
  ],
  "rules_applied": {
    "cms": [
      { "section_id": "TH_MODALITY", "outcome": "PASSED",
        "evidence_refs": ["E001"], "detail": "Audio+video modality confirmed.", "negative_finding": null },
      { "section_id": "TH_AUDIO_ONLY", "outcome": "NOT_TRIGGERED",
        "evidence_refs": [], "detail": "Modality is audio+video — audio-only rule not triggered.", "negative_finding": null },
      { "section_id": "TH_LOCATION", "outcome": "PASSED",
        "evidence_refs": ["E001"], "detail": "Patient and provider locations documented.", "negative_finding": null },
      { "section_id": "TH_CONSENT", "outcome": "PASSED",
        "evidence_refs": ["E002"], "detail": "Consent language found.", "negative_finding": null },
      { "section_id": "TH_SYNCHRONOUS", "outcome": "PASSED",
        "evidence_refs": ["E001"], "detail": "Real-time connection language confirmed.", "negative_finding": null }
    ],
    "client": [
      {
        "directive_id": "TH-001", "directive_type": "EXTEND",
        "anchored_to": "TH_SYNCHRONOUS", "outcome": "PASSED",
        "evidence_refs": ["E001"],
        "detail": "Client-specific telehealth keyword matched.", "negative_finding": null
      }
    ]
  },
  "reasoning": {
    "status": "EXTRACTED",
    "summary": "Telehealth confirmed via Video Visit keyword. Audio+video modality. Patient at home, provider at clinic. Consent documented. Conducting provider identified.",
    "evidence_refs": ["E001", "E002", "E003", "E004", "E005"],
    "missing": null,
    "agency_warnings": []
  }
}
```

---

## Field Rules

| Field | Type | Rule |
|---|---|---|
| `schema_version` | string | always `"1.0"` |
| `parameter_id` | string | always `"telehealth_identity"` |
| `client_id` | string | from system prompt; `"DEFAULT"` if no client |
| `encounter_index` | integer | from classification output |
| `evaluated_at` | string | ISO 8601 runtime timestamp |
| `status` | enum | see Status Decision Rules |
| `confidence` | float | 0.0 – 1.0; must align with status — see Confidence Bands |
| `modality.type` | enum | `audio_video` \| `audio_only` \| `video_only` \| `unknown` |
| `name_format` | enum | `FNAME_LNAME` \| `FNAME_M_LNAME` \| `LNAME_FNAME` \| `LNAME_FNAME_M` |
| `display_name` | string | always `FNAME [M] LNAME, CREDENTIALS` per EP_NAME_NORMALIZATION |
| `signature_type` | enum | `electronic` \| `physical` \| `placeholder` \| `typed_unverified` \| `absent` |
| `<result value>.evidence_refs` | string[] | evidence_ids grounding `telehealth_indicator` / `modality` / `platform` / `patient_location` / `provider_location` / `consent` / `conducting_provider` / `signers[]`; `[]` when `not_found` |
| `evidence[].field` | string | result path this evidence primarily documents (e.g. `modality`, `consent`, `conducting_provider`) |
| `evidence[].verbiage` | string | exact copy from document — never paraphrase |
| `evidence[].signal_strength` | enum | `STRONG` \| `WEAK` \| `INCONCLUSIVE` |
| `rules_applied.cms[].outcome` | enum | see Outcome Values |
| `rules_applied.client[].directive_type` | enum | `ELEVATE` \| `EXTEND` \| `EXCLUDE` \| `REPLACE` |
| `rules_applied.client[].anchored_to` | string | TH_* section_id this directive targets |
| `reasoning.evidence_refs` | string[] | evidence_ids cited by the summary (replaces the old `sources` objects) |
| `reasoning.missing` | string \| null | null if EXTRACTED; gap description if PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures; empty if none |

---

## Evidence & Traceability

`evidence[]` is the **single source of truth** for all location data. Every entry carries the exact `verbiage`, `page`, `line_start`, `line_end`, and `section`. Everything else references it by `evidence_id` — no other section repeats page/line/verbiage.

- **Documented result values** (`telehealth_indicator`, `modality`, `platform`, `patient_location`, `provider_location`, `consent`, `conducting_provider`, `signature.signers[]`) MUST carry `evidence_refs` pointing at real `evidence[]` entries.
- **Absent / not-found / derived** values carry `evidence_refs: []` — there is no text to cite (all `flags.*` are derived; rely on `rules_applied.*.negative_finding`).
- **Reuse `evidence_id`s**: when several values are grounded by the same quote, all reference the same `E00x`; do not mint a new entry per field.
- Every `E00x` referenced anywhere MUST exist in `evidence[]` (no dangling refs). Inline `page`/`line` on result values has been removed — resolve location through `evidence_refs`.

---

## Confidence Bands

| Status | Range | Guidance |
|---|---|---|
| `EXTRACTED` | 0.80 – 1.00 | All key parameters found with strong signals |
| `PARTIAL` | 0.50 – 0.79 | Telehealth confirmed but 1+ parameters missing |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.49 | No telehealth indicator found |

---

## Outcome Values

| Outcome | Applies To | Meaning |
|---|---|---|
| `PASSED` | cms + client | Rule evaluated — condition satisfied |
| `FAILED` | cms + client | Rule evaluated — condition not satisfied |
| `NOT_TRIGGERED` | cms + client | Rule target not present in encounter |
| `BLOCKED` | client only | EXCLUDE or REPLACE targeted CMS regulation — not applied |

---

## Status Decision Rules

| Condition | status |
|---|---|
| Telehealth confirmed + all parameters extracted | `EXTRACTED` |
| Telehealth confirmed + one or more parameters not found | `PARTIAL` |
| No telehealth indicator found in document | `UNABLE_TO_DETERMINE` |
