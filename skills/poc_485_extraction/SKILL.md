---
name: poc_485_extraction
description: >-
  Extracts five anchor values from a Medicare Home Health 485/POC document:
  primary diagnosis, skilled services, homebound statement, F2F encounter date,
  and certification signature. Pure extraction only — no CMS validation.
  Validation of extracted values is handled downstream by the audit engine and
  the F2F encounter skills.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Reads client_name from system prompt.
  CMS files: /skills/poc_485_extraction/references/
  Client file: /skills/poc_485_extraction/clients/<client_name>/client-rules.md
---

# poc-485-extraction

## Overview

Extracts five anchors from a single 485/POC document at `/workspace/documents/POC.md`.
Output is a flat anchor JSON consumed by the system prompts of all F2F skills.

**Anchors extracted:**
1. `primary_diagnosis` — ICD-10 code + description (Order = 1 row)
2. `skilled_services` — ordered discipline list from Frequency/Duration section
3. `homebound` — full text from Home Health Eligibility section
4. `f2f_encounter_date` — both `i_certify` and `undersigned` statements always extracted
5. `certification` — physician signature name + date from Signature of Physician field

**This skill does NOT validate** diagnosis specificity, service necessity, homebound status,
90/30-day timing, or physician credentials — all validation is downstream.

### Reference Files

| File | When to Read |
|------|-------------|
| `references/field-map.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the document, read:
- `references/field-map.md` — internalize all field IDs, label variants, and format rules
- `references/output-schema.md` — internalize the JSON structure and every field rule

Check `client_name` from system prompt:
- If `DEFAULT` → no additional file; apply field-map rules only
- If not `DEFAULT` → additionally read `clients/<client_name>/client-rules.md`

**If client-rules.md is loaded, parse each directive block:**

Each directive begins with: `## DIRECTIVE <ID> | <TYPE> | <ANCHOR>`
Read `TYPE` and apply this guard:
- `ELEVATE` → always valid; client condition IN ADDITION to CMS;
  failure changes status; populate reasoning.missing
- `EXTEND` → always valid; Affects Status YES → changes status;
  Affects Status NO → adds to agency_warnings only
- `EXCLUDE` → check Element Type;
  ILLUSTRATION / EXAMPLE / SUGGESTION → apply;
  REGULATION / REQUIREMENT / CRITERIA → do NOT apply;
  add to agency_warnings: "EXCLUDE [ID] targets CMS requirement — not applied"
- `REPLACE` → check Element Type;
  EXAMPLE / ILLUSTRATION / SUGGESTION → apply;
  REGULATION / REQUIREMENT / CRITERIA → do NOT apply;
  add to agency_warnings: "REPLACE [ID] targets CMS requirement — not applied"

For any anchor with no client override, apply DEFAULT behavior from `references/field-map.md`.
CMS rules not mentioned in client-rules.md remain fully in effect.
Do not proceed until all required files are read.

### 2. Read the Document

Read `/workspace/documents/POC.md` in full.
**Page rule:** Use only `### Page N` markers as page numbers for all citations.
The `<page_number>Page N of M</page_number>` tag is confirmation only — not the primary reference.

**Format rule:** Any section can appear in HTML table, markdown table, or plain text.
Entire pages may be raw HTML. Apply the correct extraction strategy per variant as
defined in `references/field-map.md` — never assume a single format for any anchor.

### 3. Extract Primary Diagnosis

Locate the ICD-10 Diagnoses section (label: `**ICD-10**` / `**Diagnoses:**`) in any format.
Find the row where `Order` = `1` (HTML `<td>1</td>`, markdown first data row, or plain text `1 `).
Extract: `icd10_code`, `description`, `onset_or_exacerbation` (`ONSET` or `EXACERBATION`), `oe_date`.
If not found or no Order=1 row: `not_found = true`.

### 4. Extract Skilled Services

Locate `**Frequency/Duration of Visits:**` (any format). Each non-empty line starts with a discipline code.
Extract code + raw frequency string per line. Known codes: `SN`, `PT`, `OT`, `SLP`/`ST`, `MSS`, `HHA`.
Capture each as an element in `ordered_services[]`. If not found: `not_found = true`.

### 5. Extract Homebound Statement

Locate `**Supporting Documentation for Home Health Eligibility:**` (any format per field-map.md).
Capture full verbatim text of all ELIG sub-sections (ELIG01, ELIG03, ELIG05, ELIG07…). Do not interpret.
Record page. If not found: `not_found = true`.

### 6. Extract F2F Encounter Date

Always extract **both** statements independently — each produces its own result object.

| Statement | Trigger | Date Anchor |
|---|---|---|
| `i_certify` | `"I certify that this patient"` … `"Face-to-Face Encounter"` … `"on"` | After `"on"` |
| `undersigned` | `"UNDERSIGN"` … `"FACE-TO-FACE ENCOUNTER"` … `"ON:"` | After `"ON:"` |

See `references/field-map.md` for the full expected verbatim text of each statement.

**For each statement:**
1. Search all pages for the trigger. Read forward across `### Page N` markers to end of the full certification paragraph (next blank line or major section header) — NOT to the first period, as the statement spans multiple sentences.
2. Capture the **complete verbatim text** exactly as it appears in the document.
3. Record `line_start` and `line_end` (exact document line numbers).
4. Record `page_start` (trigger page) and `page` (date page) — may differ if spans page break.
5. Extract date after `"on"` / `"ON:"`. Normalize to ISO 8601.

Blank/underscores at date position → `is_present = false`, `value = null`.
Trigger not found → `not_found = true`, `verbiage = null`.

**Custom (client-rules.md only):** If `statement_pattern: custom`, extract a third result using `custom_trigger` and `date_anchor`.

### 7. Extract Certification Signature

Search all pages for physician signature labels per `references/field-map.md`.
**Always read the label before a signature block to determine whose signature it is.**

**Physician signature labels (capture these):**
`Signature of Physician` | `Attending Physician's Signature and Date Signed` | `Physician's Signature`

**Skip these — nurse/staff labels:**
`Optional Name/Signature Of` | `Nurse's Signature and Date of Verbal SOC`

**The `<signature>` tag is not exclusively for nurses** — context label determines ownership.

| Signature indicator | Type |
|---|---|
| `<signature>Name</signature>` after physician label | `physical` |
| "Electronically signed by:", "/s/", "e-signed:" | `electronic` |
| `[signature]` literal | `placeholder` |
| Plain name, no tag, no electronic prefix | `typed_unverified` |
| Underscores / blank / bare heading / nothing after label | `absent` |

Non-physician credentials (RN, LPN…) in physician slot → extract as-is; flagged downstream.
Per occurrence: `signature_type`, `name_raw`, `name_format`, `display_name`
(EP_NAME_NORMALIZATION from encounter_identity/references/provider-rules.md),
`date_signed`, `page`, `is_signed`, `is_dated`, `is_primary`.
`is_primary = true` for page 1. Not found → `not_found = true`.

### 8. Generate Output

Follow `references/output-schema.md` exactly.

**Confidence scoring:**
EXTRACTED with all five anchors found and complete values → 0.80 – 1.00
PARTIAL → 0.50 – 0.79
UNABLE_TO_DETERMINE → 0.00 – 0.49
Never assign high confidence to a non-EXTRACTED status.

**Reasoning summary rules:**
- Extraction findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/poc_485_extraction/anchors.json`.
