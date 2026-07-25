# Encounter Identity — Output Schema
# parameter_id: encounter_identity | schema_version: 1.0

---

## JSON Structure

```json
{
  "schema_version": "1.0",
  "parameter_id": "encounter_identity",
  "client_id": "DEFAULT",
  "evaluated_at": "2026-01-15T14:32:00Z",
  "status": "MET",
  "confidence": 0.90,
  "result": {
    "encounter_date": {
      "value": "2025-01-15",
      "raw": "01/15/2025",
      "date_type": "date_of_service",
      "date_label": "Date of Service",
      "confidence": "high",
      "page": 1,
      "line": 4,
      "section": "Header",
      "flags": {
        "ambiguous_format": false, "partial_date": false,
        "multiple_dates_conflict": false, "late_documentation": false,
        "no_date_found": false, "has_addendum": false, "addendum_date": null
      }
    },
    "signature": {
      "signed": true,
      "signers": [
        {
          "name": "John Smith", "credentials": "MD",
          "name_format": "FNAME_LNAME",
          "display_name": "John Smith, MD",
          "signature_date": "2025-01-15", "signature_type": "electronic_verified",
          "source": "plain_text", "role_label": null
        }
      ],
      "flags": {
        "illegible_signature": false, "signature_undated": false,
        "multiple_signatures_found": false, "stamp_signature": false,
        "late_documentation": false
      }
    },
    "eligible_provider": {
      "performed_by_field_found": true,
      "performed_by_raw": "Smith, John",
      "performed_by_format": "LNAME_FNAME",
      "performed_by_display_name": "John Smith, MD",
      "conducting_provider": {
        "name": "John Smith", "credentials": "MD",
        "name_format": "FNAME_LNAME",
        "display_name": "John Smith, MD",
        "provider_type": "physician_md_do", "is_allowed": true,
        "identification_method": "performed_by_match", "confidence": "high"
      },
      "cosign": {
        "is_required": false, "required_reason": null,
        "cosign_found": false, "cosigner": null, "is_valid": null,
        "flags": {
          "cosign_required_but_absent": false,
          "cosigner_not_allowed_type": false, "cosign_undated": false
        }
      },
      "flags": {
        "performed_by_not_found": false, "conducting_provider_ambiguous": false,
        "multiple_signatures_found": false, "electronic_signature_mismatch": false,
        "resident_conductor": false,
        "specialty_mismatch": false,
        "cnm_state_authorization_note": false
      },
      "is_allowed": true,
      "overall_confidence": "high"
    }
  },
  "evidence": [
    {
      "evidence_id": "E001", "verbiage": "01/15/2025",
      "page": 1, "line_start": 4, "line_end": 4, "section": "Header",
      "context": "Encounter Date — Date of Service",
      "criterion_matched": "ED_DATE_PRIORITY", "signal_strength": "STRONG"
    },
    {
      "evidence_id": "E002",
      "verbiage": "Electronically signed by: John Smith, MD — 01/15/2025 14:32",
      "page": 3, "line_start": 42, "line_end": 42, "section": "Signature Block",
      "context": "Electronic Signature — conducting provider",
      "criterion_matched": "EP_ELIGIBLE_PROVIDER", "signal_strength": "STRONG"
    }
  ],
  "rules_applied": {
    "cms": [
      { "section_id": "ED_DATE_PRIORITY", "outcome": "PASSED",
        "evidence_refs": ["E001"], "detail": "Date of Service found in header; normalized to ISO 8601.", "negative_finding": null },
      { "section_id": "EP_ELIGIBLE_PROVIDER", "outcome": "PASSED",
        "evidence_refs": ["E002"], "detail": "MD confirmed via electronic signature matching Performed By.", "negative_finding": null },
      { "section_id": "EP_COSIGN", "outcome": "NOT_APPLICABLE",
        "evidence_refs": [], "detail": "Allowed practitioner — co-sign not required.", "negative_finding": null }
    ],
    "client": []
  },
  "reasoning": {
    "status": "MET",
    "summary": "Encounter date 01/15/2025 from labeled DOS header. Conducting provider John Smith MD identified via electronic signature matched to Performed By; allowed under 2026 CMS rules.",
    "sources": [
      {"evidence_id": "E001", "page": 1, "line_start": 4, "line_end": 4},
      {"evidence_id": "E002", "page": 3, "line_start": 42, "line_end": 42}
    ],
    "missing": null,
    "agency_warnings": []
  }
}
```

---

## Status Decision Table

| Condition | Status |
|---|---|
| All three components extracted + provider allowed + co-sign resolved | `MET` |
| One component is low confidence or a non-critical flag is raised | `PARTIAL` |
| No signature, provider not allowed, or co-sign required but absent | `NOT_MET` |
| Document insufficient to evaluate any component | `UNABLE_TO_DETERMINE` |

## Field Rules

| Field | Rule |
|---|---|
| `date_type` | `date_of_service`, `visit_date`, `signature_date`, `unknown` |
| `name_format` | `FNAME_LNAME`, `FNAME_M_LNAME`, `LNAME_FNAME`, `LNAME_FNAME_M` |
| `display_name` | Always `FNAME [M] LNAME, CREDENTIALS` — normalized per EP_NAME_NORMALIZATION |
| `signature_type` | From EP_SIGNATURE_TYPES in provider-rules.md |
| `identification_method` | From EP_IDENTIFICATION in provider-rules.md |
| `provider_type` | Code from EP_ELIGIBLE_PROVIDER table |
| `outcome` | `PASSED` / `FAILED` / `NOT_APPLICABLE` / `UNABLE_TO_DETERMINE` |
| `confidence` (top-level) | Float 0.00–1.00 per threshold table in SKILL.md |
