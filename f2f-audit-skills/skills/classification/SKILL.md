---
name: classification
description: >-
  Use this skill when the task involves reading a paginated Medicare Home Health
  Face-to-Face (F2F) markdown document and segmenting it into individually typed
  clinical encounters. Covers boundary detection, same-page splits with line-level
  references, encounter type classification using a 14-category taxonomy, and
  structured JSON output. Apply before any parameter extraction, eligibility
  validation, or CMS audit work begins.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Requires read access to /workspace/documents/F2F.md and all files under
  /skills/classification/references/
---

# classification

## Overview

Segments a paginated F2F markdown document (`### Page N` format) into individual
typed clinical encounters. Each encounter is classified using a strict 14-category
taxonomy and returned as structured JSON.

This skill does **not** perform CMS eligibility validation, parameter extraction,
encounter scoring, or any inference beyond what is present in the document.

### Reference Files

| File | When to Read |
|------|-------------|
| `references/categories_classification.md` | Step 1 — always; taxonomy required before any classification |
| `references/output-schema.md` | Step 1 — always; JSON schema and field rules |
| `references/line-counting-rules.md` | Step 4 — always; how to count lines and assign line fields |
| `references/encounter-patterns-exclusive.md` | Step 4 — when all encounters start at page boundaries with no sharing |
| `references/same-page-split-cases.md` | Step 4 — when any page is shared by two or more encounters (cases 1–3) |
| `references/same-page-split-advanced.md` | Step 4 — when three or more encounters share a page, or an encounter straddles multiple shared pages (cases 4–6) |
| `references/encounter-patterns-edgecases.md` | Step 4 — when OCR noise, blank pages, embedded orders, or addenda are present |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the document, read:
- `references/categories_classification.md` — internalize all category keys and
  subcategory codes; use these values exactly in output
- `references/output-schema.md` — internalize the JSON schema and every field rule

Do not proceed until both files are read.

### 2. Read the Input Document

Read `/workspace/documents/F2F.md` in full.

**Page numbering rule:** Use only `### Page N` markers as official page numbers.
Ignore printed page numbers inside the document body — scanned copies may have
non-contiguous internal numbering due to missing or skipped pages.

### 3. Identify Encounter Boundaries

Segment by clinical narrative and document structure, **not** page boundaries alone.

**Start a new encounter when any of these occur:**
- A new document title or encounter header appears
- The encounter date, provider, or facility changes
- The clinical narrative clearly restarts
- The document type changes (e.g., Progress Note → F2F Note, H&P → Physician Order)

**Do NOT start a new encounter when:**
- The narrative continues onto the next page
- A signature or attestation belongs to the current encounter
- An Assessment or Plan section continues across pages
- Headers or footers repeat on each page

If multiple encounters share a page, create separate objects in original order
and apply line reference rules in Step 4.

### 4. Apply Line References

Read `references/line-counting-rules.md` first — always.

Then read the relevant pattern file based on what you found in the document:
- All encounters at page boundaries, no sharing → `references/encounter-patterns-exclusive.md`
- Any page shared by two encounters → `references/same-page-split-cases.md`
- Three or more encounters share a page, or encounter straddles multiple shared pages → `references/same-page-split-advanced.md`
- OCR noise, blank pages, embedded orders, or addenda present → `references/encounter-patterns-edgecases.md`

### 5. Classify Each Encounter

Use exact values from `references/categories_classification.md`.

**Priority order (apply in sequence — first match wins):**
1. Explicit F2F title, no telehealth → `f2f_encounter / 1.1`
2. Telehealth indicators present + explicit F2F → `telehealth_encounter / 3.5`
3. Telehealth indicators present, no F2F → `telehealth_encounter / 3.1`–`3.4`
4. CMS-485 / "Certification Period" / "Frequency/Duration of Visits" → `poc_485`
5. "Hospital Course" + "Discharge Diagnosis" → `discharge_and_transition / 9.1`
6. Explicit Addendum → `addendum / ADDENDUM` (set `parent_encounter_index`)
7. `UNPLACED` — only when classification cannot be made with confidence

**Provider name:** Extract exactly as written. Return `null` if absent. Do not infer.

**Telehealth:** Flag in `classification_notes`:
`"TELEHEALTH — disqualifying for F2F certification."`

### 6. Validate Before Output

- Every `### Page N` belongs to at least one encounter's `pages` array
- No line ranges overlap between encounters
- All category and subcategory values match the taxonomy exactly
- Same-page encounters have line fields populated; exclusive-page encounters have `null`

### 7. Generate and Save Output

Refer to `references/output-schema.md` for the exact JSON structure.
Return **only** the valid JSON object — no explanations, reasoning, or markdown fences.
Save to `/workspace/documents/outputs/classification/results.json`.
