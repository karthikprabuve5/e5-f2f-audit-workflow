# POC/485 — Field Location Map
# Maps each anchor to its label, format variants, and fallbacks in POC.md

---

## Format Variants — Applies to All Anchors

OCR output format is not guaranteed. Any section can appear in one of three forms.
Always apply the correct extraction strategy based on what is actually present.

| Format | Indicators | Extraction Strategy |
|---|---|---|
| HTML table | `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`, `<th>` tags | Parse cell content by tag; entire page may be raw HTML |
| Markdown table | Lines starting with `\|`, separator row with `\|---|` | Parse columns by pipe-delimited position |
| Plain text | No table tags or pipes; labels in bold (`**Label:**`) or plain text | Extract by label keyword + surrounding text |

Apply this variant logic to every anchor below. Never assume a single format.

---

## Anchor 1 — Primary Diagnosis
<!-- cms_section_id: POC_PRIMARY_DX -->

**Section label variants:** `**ICD-10**` / `**Diagnoses:**` / `ICD-10 Diagnoses` / `Diagnoses:`

| Format | How to Find Order=1 Row |
|---|---|
| HTML table | `<td>1</td>` in the first `<td>` of a `<tr>` inside the diagnoses `<tbody>` |
| Markdown table | First data row after the `\|---|` separator row in the diagnoses table |
| Plain text | Line starting with `1 ` or `1.` followed by ICD code and description |

Columns to extract: Order, Code, Description, Onset or Exacerbation, O/E Date.
Typical page: Page 1. Fallback: search all pages if not on page 1.

---

## Anchor 2 — Skilled Services
<!-- cms_section_id: POC_SKILLED_SERVICES -->

**Section label variants:**
- `**Frequency/Duration of Visits:**` (primary — most reliable)
- `Frequency/Duration of Visits:` (plain text)
- HTML `<p>` or `<div>` containing "Frequency/Duration"

**Line format variants within the section:**

| Variant | Example |
|---|---|
| Code + frequency | `SN 2WK1,1WK1,2WK1,1WK6` |
| Code + EFFECTIVE date + frequency | `PT EFFECTIVE 04/26/2026 1WK1` |
| HTML wrapped | `<p>SN 2WK1,1WK1</p>` — strip tags, apply same logic |
| Plain sentence | `Skilled Nursing: 2 visits/week × 1 week` — extract discipline keyword |

Known discipline codes: `SN`, `PT`, `OT`, `SLP`, `ST`, `MSS`, `HHA`

**Fallback:** If Frequency/Duration section is absent, scan
`**Orders of Discipline and Treatments:**` for lines beginning with "SKILLED NURSE",
"PHYSICAL THERAPIST", "OCCUPATIONAL THERAPIST", "SPEECH", "SOCIAL WORKER", "HOME HEALTH AIDE"
and map to discipline codes accordingly.

---

## Anchor 3 — Homebound Statement
<!-- cms_section_id: POC_HOMEBOUND -->

**Section label variants:**
- `**Supporting Documentation for Home Health Eligibility:**`
- `Supporting Documentation for Home Health Eligibility:` (plain)
- HTML heading or `<p>` containing "Home Health Eligibility"
- `CRITERIA 1` / `CRITERIA 2` pattern (older form format — no ELIG codes)

**Sub-section variants:**

| Variant | Format |
|---|---|
| ELIG-coded | `(ELIG01)`, `(ELIG03)`, `(ELIG05)`, `(ELIG07)` prefix per paragraph |
| CRITERIA-coded | `CRITERIA 1 —` / `CRITERIA 2 —` prefix per paragraph |
| Plain narrative | No sub-codes; continuous paragraph describing homebound status |

Capture full verbatim text regardless of sub-section format.
Record which sub-codes/criteria were found in `elig_sections_found`.
Typical page: last page or second-to-last page. Search all pages.

---

## Anchor 4 — F2F Encounter Date
<!-- cms_section_id: POC_F2F_DATE -->

The certification statement can appear on any page, including within the
Orders of Discipline and Treatments section. Search the entire document.

Both standard statements always extracted independently. Capture full verbatim text and exact line numbers.
Client-rules override needed only for `custom` patterns beyond these two.

**Statement A — `i_certify` (always extracted):**
Full verbiage: `"I certify that this patient is confined to his/her home and needs intermittent skilled nursing care, physical therapy and/or speech therapy, or continues to need occupational therapy. This patient is under my care, and I have authorized the services on this plan of care and will periodically review the plan. I further certify that this patient had a Face-to-Face Encounter performed by a physician or allowed non-physician practitioner that was related to the primary reason the patient requires Home Health Services on [DATE]."`
Trigger start: `"I certify that this patient"` | Date anchor: after `"on"` at end.

**Statement B — `undersigned` (always extracted):**
Full verbiage: `"THE UNDERSIGNED PROVIDER CERTIFIES THAT THEY HAVE REVIEWED AND COLLABORATED ON THE FACE TO FACE ENCOUNTER, PERFORMED BY A PHYSICIAN OR ALLOWED NON-PHYSICIAN PRACTITIONER, RELATED TO THE PRIMARY REASON FOR HOME HEALTH SERVICES ON: [DATE]"`
Trigger start: `"UNDERSIGN"` | Date anchor: after `"ON:"` at end.

**Custom pattern (client-rules.md only):**
| Pattern Code | Trigger | Date Anchor |
|---|---|---|
| `custom` | `custom_trigger` value from client-rules.md | `date_anchor` value |

**Cross-page rule:** Statement may start on page N, date on page N+1. Read across `### Page N`
markers until date found or a new major section begins. Record `page_start` and `page` separately.

**Blank/missing:** `____________`, `______`, `[date]`, whitespace only → `is_present = false`.
**Not found:** Trigger absent from all pages → `not_found = true` for that statement.

---

## Anchor 5 — Certification Signature
<!-- cms_section_id: POC_CERTIFICATION -->

**Target label variants (physician only):**
`Signature of Physician` | `Attending Physician's Signature and Date Signed` | `Physician's Signature`

**The label before a signature block determines whose it is — always read context first.**
A `<signature>` tag is NOT exclusively for nurses — it wraps any physical signature.

### Signature Types

| Type | Code | Indicator |
|---|---|---|
| Physical / handwritten | `physical` | `<signature>Name</signature>` after physician label |
| Electronic | `electronic` | "Electronically signed by:", "/s/", "e-signed:" near physician label |
| Placeholder | `placeholder` | `[signature]` or `[date]` literal |
| Typed unverified | `typed_unverified` | Plain name, no tag, no electronic prefix |
| Blank / unsigned | `absent` | `____________`, `_____`, empty after label, or bare heading with nothing following |

### Do NOT capture — nurse and staff labels
`Optional Name/Signature Of` | `Nurse's Signature and Date of Verbal SOC`
A `<signature>` tag following one of these labels → skip entirely.

**Date label variants:** `Date` / `Date Signed` / `Date ____________` — same or next line.

### Format Variants
| Format | Example |
|---|---|
| Plain blank | `Signature of Physician ____________ Date ____________` |
| Physical tag | `Signature of Physician` → next line: `<signature>John Smith, MD</signature>` → `Date 04/22/2026` |
| Placeholder | `Signature of Physician: [signature] Date: [date]` |
| Electronic | `Signature of Physician: Electronically signed by John Smith MD 04/22/2026` |
| HTML | `<td>Signature of Physician</td><td><signature>Name</signature></td><td>Date</td>` |

Capture all occurrences across all pages. Mark the page 1 occurrence as `is_primary = true`.
