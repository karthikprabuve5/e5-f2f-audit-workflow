# Output Schema — POC/485 Anchor Extraction
# parameter_id: poc_485_extraction | schema_version: 1.0

---

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "poc_485_extraction",
  "client_id": "DEFAULT",
  "evaluated_at": "2026-04-22T11:11:00Z",
  "status": "EXTRACTED",
  "confidence": 0.95,
  "result": {
    "primary_diagnosis": {
      "icd10_code": "D62",
      "description": "ACUTE POSTHEMORRHAGIC ANEMIA",
      "onset_or_exacerbation": "EXACERBATION",
      "oe_date": "2026-04-22",
      "page": 1,
      "not_found": false
    },
    "skilled_services": {
      "ordered_services": [
        { "discipline": "SN", "raw_frequency": "2WK1,1WK1,2WK1,1WK6", "effective_date": null },
        { "discipline": "PT", "raw_frequency": "1WK1", "effective_date": "2026-04-26" }
      ],
      "page": 1,
      "not_found": false
    },
    "homebound": {
      "full_text": "PATIENT USES A WALKER AND WHEELCHAIR FOR MOBILITY... [verbatim text]",
      "elig_sections_found": ["ELIG01", "ELIG03"],
      "page": 8,
      "not_found": false
    },
    "f2f_encounter_date": {
      "i_certify": {
        "verbiage": "I certify that this patient is confined to his/her home... on .",
        "line_start": 252, "line_end": 252,
        "value": null, "raw": null,
        "is_present": false, "page_start": 1, "page": 1, "not_found": false,
        "flags": { "date_blank": true }
      },
      "undersigned": {
        "verbiage": "THE UNDERSIGNS PROVIDER CERTIFIES... ON: 03/23/2026",
        "line_start": 378, "line_end": 378,
        "value": "2026-03-23", "raw": "03/23/2026",
        "is_present": true, "page_start": 3, "page": 3, "not_found": false,
        "flags": { "date_blank": false }
      },
      "custom": null
    },
    "certification": {
      "occurrences": [
        { "page": 1, "is_primary": true, "signature_type": "absent",
          "name_raw": null, "name_format": null, "display_name": null,
          "date_signed": null, "is_signed": false, "is_dated": false },
        { "page": 3, "is_primary": false, "signature_type": "physical",
          "name_raw": "GEORGE HANNA", "name_format": "FNAME_LNAME",
          "display_name": "George Hanna, MD",
          "date_signed": "2026-04-22", "is_signed": true, "is_dated": true }
      ],
      "any_signed": true,
      "not_found": false
    }
  },
  "evidence": [
    {
      "evidence_id": "E001",
      "anchor": "primary_diagnosis",
      "page": 1,
      "line_start": 58,
      "line_end": 63,
      "verbiage": "Order=1 | D62 | ACUTE POSTHEMORRHAGIC ANEMIA | EXACERBATION | 04/22/2026"
    },
    {
      "evidence_id": "E002",
      "anchor": "f2f_encounter_date",
      "page": 3,
      "line_start": 378,
      "line_end": 378,
      "verbiage": "THE UNDERSIGNS PROVIDER CERTIFIES... ON: 03/23/2026"
    }
  ],
  "rules_applied": {
    "cms": [
      {
        "section_id": "POC_PRIMARY_DX",
        "outcome": "EXTRACTED",
        "evidence_refs": ["E001"],
        "detail": "Primary diagnosis code and description found in order table.",
        "negative_finding": null
      },
      {
        "section_id": "POC_F2F_DATE",
        "outcome": "PARTIAL",
        "evidence_refs": ["E002"],
        "detail": "undersigned statement extracted with date; i_certify date blank.",
        "negative_finding": "i_certify date field empty on page 1"
      }
    ],
    "client": [
      {
        "directive_id": "POC-001",
        "directive_type": "REPLACE",
        "anchored_to": "POC_SKILLED_SERVICES",
        "outcome": "PASSED",
        "evidence_refs": [],
        "detail": "Client label override applied for skilled services section.",
        "negative_finding": null
      }
    ]
  },
  "reasoning": {
    "status": "EXTRACTED",
    "summary": "Four of five anchors fully extracted. F2F date partially extracted — undersigned statement present with date, i_certify date field blank.",
    "sources": [
      { "evidence_id": "E001", "page": 1, "line_start": 58, "line_end": 63,
        "description": "Primary diagnosis anchor" },
      { "evidence_id": "E002", "page": 3, "line_start": 378, "line_end": 378,
        "description": "F2F date — undersigned statement" }
    ],
    "missing": "i_certify date blank — may indicate incomplete POC",
    "agency_warnings": []
  }
}
```

---

## Field Rules

| Field | Type | Rule |
|-------|------|------|
| `schema_version` | string | always `"1.0"` |
| `parameter_id` | string | always `"poc_485_extraction"` |
| `client_id` | string | from system prompt; `"DEFAULT"` if no client |
| `evaluated_at` | string | ISO 8601 runtime timestamp |
| `status` | enum | `EXTRACTED` / `PARTIAL` / `UNABLE_TO_DETERMINE` |
| `confidence` | float | 0.0 – 1.0; must align with status |
| `result.primary_diagnosis.icd10_code` | string | exact code as written — do not reformat |
| `result.primary_diagnosis.onset_or_exacerbation` | string | `ONSET` or `EXACERBATION` exact value |
| `result.primary_diagnosis.oe_date` | string | ISO 8601 from O/E Date column |
| `result.skilled_services.ordered_services[].discipline` | string | `SN` `PT` `OT` `SLP` `MSS` `HHA` |
| `result.skilled_services.ordered_services[].effective_date` | string\|null | ISO 8601; `null` if not stated |
| `result.homebound.full_text` | string | verbatim homebound section text |
| `result.homebound.elig_sections_found` | string[] | ELIG codes detected; `[]` if none |
| `result.f2f_encounter_date.*.verbiage` | string | full verbatim statement text; `null` if not found |
| `result.f2f_encounter_date.*.line_start` / `line_end` | integer | exact document line numbers |
| `result.f2f_encounter_date.*.is_present` | boolean | `true` = date extracted; `false` = statement found, date blank |
| `result.f2f_encounter_date.*.not_found` | boolean | `true` = section label not found in document |
| `result.certification.occurrences[].signature_type` | enum | `physical` `electronic` `placeholder` `typed_unverified` `absent` |
| `result.certification.occurrences[].is_primary` | boolean | `true` for page 1 Signature of Physician occurrence |
| `result.certification.any_signed` | boolean | `true` if at least one occurrence has `is_signed = true` |
| `result.certification.occurrences[].display_name` | string | normalized per EP_NAME_NORMALIZATION |
| `evidence[].evidence_id` | string | unique ID starting E001; used for cross-referencing |
| `evidence[].anchor` | string | which anchor this evidence supports |
| `rules_applied.cms[].section_id` | string | field_id from field-map.md |
| `rules_applied.cms[].outcome` | enum | see Outcome Values |
| `rules_applied.client[].directive_id` | string | directive ID from client-rules.md |
| `reasoning.summary` | string | extraction summary; no PII; 1–2 sentences |
| `reasoning.missing` | string\|null | null if EXTRACTED; gap description otherwise |
| `reasoning.agency_warnings` | array | EXTEND failures and blocked directives |

---

## Confidence Bands

| Status | Range | Guidance |
|--------|-------|---------|
| `EXTRACTED` | 0.80 – 1.00 | All five anchors found with complete values |
| `PARTIAL` | 0.50 – 0.79 | Some anchors found; one or more missing or incomplete |
| `UNABLE_TO_DETERMINE` | 0.00 – 0.49 | Document not a valid 485/POC or no anchors found |

---

## Outcome Values

| Outcome | Meaning |
|---------|---------|
| `EXTRACTED` | Anchor section found and value captured |
| `PARTIAL` | Section found but value incomplete (e.g., date blank) |
| `NOT_FOUND` | Section label not found in document |
| `BLOCKED` | Client EXCLUDE or REPLACE targeted CMS field — not applied |

---

## Status Decision Rules

| Condition | status |
|-----------|--------|
| All five anchors extracted with complete values | `EXTRACTED` |
| One or more anchors partially extracted or not found | `PARTIAL` |
| Document is not a valid 485/POC | `UNABLE_TO_DETERMINE` |
