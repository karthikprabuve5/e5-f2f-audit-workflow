# Output Schema — Skilled Services

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "skilled_services",
  "client_id": "DEFAULT",
  "encounter_index": 1,
  "evaluated_at": "2026-03-10T14:32:00Z",
  "status": "MET",
  "confidence": 0.90,
  "result": {
    "poc_ordered_services": ["SN", "PT", "HHA"],
    "is_documented": true,
    "services": [
      {
        "service_type": "SN",
        "justification_type": "wound_care",
        "is_justified": true,
        "rehabilitation_potential": "not_applicable",
        "reason_documented": "Infected post-surgical wound requiring sterile dressing changes and skilled assessment",
        "signal_strength": "STRONG",
        "evidence_refs": ["E001"]
      },
      {
        "service_type": "PT",
        "justification_type": null,
        "is_justified": true,
        "rehabilitation_potential": "documented",
        "reason_documented": "3/5 bilateral LE strength post right TKA; requires skilled gait training to restore ambulation",
        "signal_strength": "STRONG",
        "evidence_refs": ["E002"]
      },
      {
        "service_type": "HHA",
        "justification_type": null,
        "is_justified": true,
        "rehabilitation_potential": "not_applicable",
        "reason_documented": "Patient requires assistance with bathing during post-surgical recovery",
        "signal_strength": "MODERATE",
        "evidence_refs": ["E003"]
      }
    ],
    "flags": {
      "ot_initiation_flag": false,
      "mss_standalone_flag": false,
      "hha_standalone_flag": false,
      "venipuncture_only_flag": false,
      "continuous_care_flag": false,
      "custodial_risk": false,
      "maintenance_without_justification": false
    }
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "field": "services[0]",
      "verbiage": "Post-surgical wound care with sterile dressing changes required; wound infected",
      "page": 2,
      "line_start": 34,
      "line_end": 35,
      "section": "Plan",
      "context": "SN Justification",
      "criterion_matched": "SS_SKILLED_NECESSITY",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E002",
      "field": "services[1]",
      "verbiage": "3/5 bilateral LE strength post right TKA; requires skilled gait training to restore ambulation",
      "page": 2,
      "line_start": 40,
      "line_end": 42,
      "section": "Plan",
      "context": "PT Justification",
      "criterion_matched": "SS_QUALIFYING_SERVICES",
      "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E003",
      "field": "services[2]",
      "verbiage": "Patient requires assistance with bathing during post-surgical recovery",
      "page": 2,
      "line_start": 44,
      "line_end": 44,
      "section": "Plan",
      "context": "HHA Justification",
      "criterion_matched": "SS_CLINICAL_NEXUS",
      "signal_strength": "MODERATE"
    }
  ],
  "rules_applied": {
    "cms": [
      { "section_id": "SS_QUALIFYING_SERVICES", "outcome": "PASSED", "evidence_refs": ["E001", "E002"], "detail": "SN and PT are qualifying skilled services; HHA accompanies skilled care.", "negative_finding": null },
      { "section_id": "SS_SKILLED_NECESSITY", "outcome": "PASSED", "evidence_refs": ["E001"], "detail": "SN wound care requires sterile technique — not delegable.", "negative_finding": null },
      { "section_id": "SS_CLINICAL_NEXUS", "outcome": "PASSED", "evidence_refs": ["E001", "E002"], "detail": "Both services linked to post-surgical diagnosis; PT documents rehab potential.", "negative_finding": null }
    ],
    "client": []
  },
  "reasoning": {
    "status": "MET",
    "summary": "The F2F note documents clinical justification for SN wound care and PT gait training linked to post-surgical diagnosis; HHA is appropriately ordered as adjunct personal care.",
    "evidence_refs": ["E001", "E002", "E003"],
    "missing": null,
    "agency_warnings": []
  }
}
```

---

## Field Rules

| Field | Type | Rule |
|-------|------|------|
| `parameter_id` | string | always `"skilled_services"` |
| `status` | enum | `MET` / `NOT_MET` / `PARTIAL` / `UNABLE_TO_DETERMINE` |
| `result.poc_ordered_services` | array | parsed from system prompt anchor; source of truth — carries no `evidence_refs` (not from the F2F doc) |
| `result.is_documented` | boolean | true if any justification found for any ordered service |
| `services[].service_type` | enum | `SN` / `PT` / `OT` / `SLP` / `MSS` / `HHA` |
| `services[].justification_type` | enum or null | SN only; null for PT/OT/SLP/MSS/HHA |
| `services[].is_justified` | boolean | true if STRONG or MODERATE signal found |
| `services[].rehabilitation_potential` | enum or null | `documented` / `not_documented` / `not_applicable` |
| `services[].reason_documented` | string | exact or near-exact clinical reason from note; never fabricated |
| `services[].signal_strength` | enum | `STRONG` / `MODERATE` / `WEAK` / `ABSENT` |
| `services[].evidence_refs` | array | evidence_ids supporting this service; must resolve to real `evidence[]` entries |
| `evidence[].field` | string | result path this evidence primarily documents (e.g. `services[0]`) |
| `evidence[].context` | string | `<SERVICE_TYPE> Justification` |
| `reasoning.evidence_refs` | string[] | evidence_ids cited by the summary (replaces the old `sources` objects) |
| `reasoning.missing` | string or null | null if MET; gap description if NOT_MET or PARTIAL |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives; empty if none |

## Evidence & Traceability

`evidence[]` is the **single source of truth** for all location data. Every entry carries the exact `verbiage`, `page`, `line_start`, `line_end`, and `section`. Everything else references it by `evidence_id` — no other section repeats page/line/verbiage.

- **Documented result values** (`services[]`) MUST carry `evidence_refs` pointing at real `evidence[]` entries — one entry per justified service; **no dangling refs** (every `E00x` used must exist in `evidence[]`).
- **Absent / derived / prompt-anchor** values carry `evidence_refs: []` or omit it — `poc_ordered_services` comes from the system prompt; `is_documented` and all `flags.*` are derived (rely on `rules_applied.*.negative_finding`).
- **Reuse `evidence_id`s**: when several values are grounded by the same quote, all reference the same `E00x`; do not mint a new entry per field.

---

## Confidence Bands

| Status | Range |
|--------|-------|
| `MET` — all services STRONG | 0.85 – 1.00 |
| `MET` — some services MODERATE | 0.80 – 0.84 |
| `PARTIAL` | 0.50 – 0.79 |
| `NOT_MET` | 0.30 – 0.49 |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.29 |

---

## Status Decision Rules

| Condition | status |
|-----------|--------|
| All qualifying services justified at STRONG or MODERATE | `MET` |
| At least one qualifying service justified; one or more WEAK or ABSENT | `PARTIAL` |
| No qualifying service justified | `NOT_MET` |
| Only OT, MSS, or HHA ordered — no qualifying skilled service | `NOT_MET` |
| Document insufficient to evaluate any service | `UNABLE_TO_DETERMINE` |

Evaluate all CMS sections regardless of earlier results. Do not short-circuit.
