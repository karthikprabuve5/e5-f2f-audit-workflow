---
name: surgical-note
description: >-
  Use this skill to validate whether a surgical or operative note meets CMS
  requirements to serve as a Face-to-Face encounter document for Medicare Home
  Health certification. Classifies note type, evaluates HH-relevant clinical
  content, and assesses F2F documentation adequacy per MBPM Chapter 7 §30.5,
  §30.5.1, §30.5.1.1, and §30.5.1.2. Does not validate provider eligibility, signatures,
  homebound status, or any other parameter.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Requires classified encounter content with document-level line numbers.
  Reads client_name from system prompt.
  CMS files: /skills/surgical-note/surgical-note/references/
  Client file: /skills/surgical-note/surgical-note/clients/<client_name>/client-rules.md
---

# surgical-note

## Overview

Validates whether a surgical or operative note provides adequate Face-to-Face
documentation for Medicare Home Health certification in a prebill audit context.
Classifies the note type, extracts surgical procedure and setting, evaluates
whether the note contains clinical content establishing the basis for HH need,
and returns a structured adequacy determination.

**This skill does NOT validate:**
- Provider eligibility or credentials → encounter_identity skill
- Encounter date or signature → encounter_identity skill
- Homebound status → homebound skill
- Skilled services → skilled_services skill
- Primary diagnosis alignment → primary_diagnosis skill
- Inpatient setting timing conflict → inpatient_detection skill

### Reference Files

| File | When to Read |
|------|-------------|
| `references/cms-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the encounter document, read:
- `references/cms-rules.md` — internalize all CMS criteria, section IDs, and note-type rules
- `references/output-schema.md` — internalize the JSON structure and every field rule

Check `client_name` from system prompt:
- If `DEFAULT` → no additional file; apply CMS rules only
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

CMS rules not mentioned in client-rules.md remain fully in effect.
Do not proceed until all required files are read.

### 2. Read the Encounter Document

Read `/workspace/documents/F2F.md` in full.

**Page numbering rule:** Use only `### Page N` markers as official page numbers.
Ignore page numbers printed inside the document body — scanned copies may have
non-contiguous internal numbering.

### 3. Classify Note Type

Identify the primary note type from title, header, and document structure.
Assign exactly ONE code. If multiple note types appear, use the most clinically
relevant to HH certification.

| Code | Key Indicators |
|---|---|
| `pre_op_note` | "Pre-Operative H&P", "Pre-Op Note", "History and Physical", "H&P", medical history + ROS before surgery — valid only if anticipated post-surgical HH need also documented |
| `operative_note` | "Operative Report", "Operative Note", "OR Note", procedure steps in sequence, "patient was prepped and draped", "incision", "closure" |
| `post_op_note` | "Post-Operative Note", "Post-Op Visit", "POD #", "wound check", "post-operative follow-up", "surgical site" |
| `anesthesia_note` | "Anesthesia Record", "Pre-Anesthesia Evaluation", "Anesthesiologist", "CRNA", "induction", "regional block" |
| `surgical_consult` | "Surgical Consult", "Consultation", "Referred by", consultant physician assessment |
| `discharge_summary` | "Discharge Summary", "D/C Summary", "Discharge Diagnosis", "Discharge Medications", "Follow-up instructions" |
| `unknown` | Note type not determinable from available content |

Set `note_type_valid` per `SN_NOTE_TYPE` in `references/cms-rules.md`.
Set `anesthesia_only = true` if note_type is `anesthesia_note`.
Set `operative_note_only = true` if note_type is `operative_note` and no
pre-op or post-op clinical assessment is embedded in the same document.

### 4. Extract Surgical Procedure and Setting

**Surgical procedure:** Search for procedure name in document title, header,
or body. Capture verbatim. Set `not_found = true` if absent.

**Setting:** Search for operating room, surgical center, or hospital indicators.

| Code | Key Indicators |
|---|---|
| `hospital_or` | "Operating Room", "OR", "Inpatient Surgery", hospital letterhead with surgical suite |
| `asc` | "Ambulatory Surgical Center", "ASC", "Surgery Center", "Outpatient Surgery Center" |
| `hospital_outpatient` | "Hospital Outpatient", "HOPD", "Same-Day Surgery", "Day Surgery" |
| `physician_office` | "Office procedure", "In-office", physician practice address as procedure location |
| `unknown` | Setting not documented |

### 5. Evaluate HH-Relevant Content

Search the entire document for content connecting the surgical condition or its
sequelae to a need for home health services. Focus on:
- Wound care, surgical site management, drain care
- Post-surgical rehabilitation (PT, OT, SLP) needs
- Medication administration or infusion therapy post-discharge
- Functional limitations resulting from surgery
- Homebound status indicators related to surgery
- Explicit HH referral or discharge-to-HH language
- Physician assessment of recovery requirements at home

Set `hh_relevant_content.found = true` if ANY of the above present.
Set `hh_content_weak = true` if content is vague or conclusory without
clinical specificity (e.g., "patient will need home care" with no detail).
Set `no_hh_content = true` if no HH-related content found anywhere.

### 6. Assess F2F Documentation Adequacy

Using criteria from `SN_F2F_CONTENT` and `SN_NOTE_TYPE` in cms-rules.md:

Set `f2f_adequate = true` only when ALL of the following are met:
1. `note_type_valid = true`
2. `hh_relevant_content.found = true`
3. `hh_content_weak = false` (content is clinically specific)

Set `f2f_adequate = false` if any of: note_type is `anesthesia_note`;
`operative_note_only = true` with no HH content; `no_hh_content = true`.

Set `discharge_summary_hh_referenced = true` if note_type is
`discharge_summary` AND explicit HH referral language found — this is the
strongest F2F signal for surgical cases.

Apply any active ELEVATE or EXCLUDE directives during this step.

### 7. Set Flags and Record Evidence

For every extracted item:
- Assign `evidence_id` starting E001
- Copy **exact verbatim** — no paraphrase, no OCR correction
- Record `page` from nearest preceding `### Page N` marker
- Record `line_start` and `line_end` as document-level line numbers
- Record `section` — the document section where found
- Assign `context` — auditor label describing what this evidence represents
- Assign `criterion_matched` — the cms_section_id this evidence satisfies
- Assign `signal_strength`: STRONG (explicit, clearly meets criterion) /
  WEAK (vague, borderline) / INCONCLUSIVE (ambiguous)

For each cms_section_id evaluated record in `rules_applied.cms`:
`outcome` / `evidence_refs` / `detail` (one sentence) /
`negative_finding` (what was looked for but not found; null if PASSED)

### 8. Generate Output

Follow `references/output-schema.md` exactly.

**Confidence scoring:**
ADEQUATE with specific HH content + valid note type → 0.80 – 1.00
PARTIAL → 0.50 – 0.79
INADEQUATE → 0.30 – 0.49
UNABLE_TO_DETERMINE → 0.00 – 0.29
Never assign high confidence to a non-ADEQUATE status without evidence.

**Reasoning summary rules:**
- Clinical findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/surgical-note/results.json`.
