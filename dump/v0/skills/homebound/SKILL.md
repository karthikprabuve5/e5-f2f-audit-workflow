---
name: homebound
description: >-
  Use this skill to extract and validate homebound status clinical documentation
  from a classified Medicare Home Health encounter. Applies CMS two-prong test
  per MBPM Chapter 7 §30.1.1, checks allowable absences per §30.1.2, and
  validates documentation quality per §30.5.1.2. Does not validate provider
  eligibility, signatures, or any other parameter.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Requires classified encounter content with document-level line numbers.
  Reads client_name from system prompt.
  CMS files: /skills/homebound/references/
  Client file: /skills/homebound/clients/<client_name>/client-rules.md
---

# homebound-status

## Overview

Extracts and validates homebound status clinical documentation from a single
classified encounter. Returns structured JSON with exact verbiage, page and
line provenance, and a plain-English auditor reasoning statement.

**This skill does NOT validate:**
- Provider eligibility or credentials → eligible-provider skill
- Signature presence or certification timing → document-signature skill
- Time window, skilled services, or any other parameter

### Reference Files

| File | When to Read |
|------|-------------|
| `references/cms-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `references/cms-examples.md` | Step 3 — when mapping extracted language to criteria |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the encounter document, read:
- `references/cms-rules.md` — internalize all CMS criteria, thresholds,
  and section IDs; use these exactly in validation
- `references/output-schema.md` — internalize the JSON structure and
  every field rule

Check `client_name` from system prompt:
- If `DEFAULT` → no additional file; apply CMS rules only
- If not `DEFAULT` → additionally read
  `clients/<client_name>/client-rules.md`

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

**Page numbering rule:** Use only `### Page N` markers as official page
numbers. Ignore page numbers printed inside the document body — scanned
copies may have non-contiguous internal numbering.

### 3. Extract Homebound Statements

Focus on these clinical sections — note the section name for each finding:
`Homebound Status` / `Functional Status` / `Assessment` / `Plan` / `HPI` / `Orders`
Skip medication lists, lab results, vital signs unless they contain homebound language.

Extract:
- Explicit homebound or confined-to-home statements
- Functional limitation descriptions linked to leaving home
- Assistive device or caregiver dependency statements
- Medically contraindicated leaving-home statements
- Underlying diagnosis or condition linked to the limitation
- Any mention of absences from home

For every extracted piece:
- Assign a unique `evidence_id` starting from E001
- Copy **exact verbiage** — no paraphrase, no OCR correction
- Record `page` from nearest preceding `### Page N` marker
- Record `line_start` and `line_end` as document-level line numbers
- Record `section` — the clinical section where found
- Assign `context` label describing what this evidence represents
- Assign `criterion_matched` — the cms_section_id this evidence satisfies
- Assign `signal_strength`: STRONG (explicit, clearly meets criterion) /
  WEAK (vague, borderline) / INCONCLUSIVE (ambiguous)

Read `references/cms-examples.md` to map extracted language to criteria.
Apply any active EXTEND or REPLACE directives during this step.

If nothing relevant found → return empty `evidence` array
and set `status` to `UNABLE_TO_DETERMINE`.

### 4. Validate Against Two-Prong Test

Using criteria and logic from `references/cms-rules.md`:

**Prong 1 — OR Logic:**
Evaluate each of the four sub-criteria independently:
`device_needed` / `special_transport` / `assistance_of_person` / `medically_contraindicated`
`prong_1.met` = true if ANY ONE sub-criterion is present.
Record ALL criteria evaluated and which ones were met in `prong_1.criteria_met`.

**Prong 2 — AND Logic:**
Evaluate both sub-criteria independently:
`normal_inability` / `considerable_effort`
`prong_2.met` = true ONLY IF BOTH sub-criteria are present simultaneously.
One without the other → `prong_2.met` = false.
Record `prong_2.normal_inability_met` and `prong_2.considerable_effort_met` separately.

Apply any active ELEVATE or EXCLUDE directives during this step.

For each cms_section_id evaluated record in `rules_applied.cms`:
`outcome` / `evidence_refs` / `detail` (one sentence) /
`negative_finding` (what was looked for but not found; null if PASSED)

### 5. Check Allowable Absences

Using absence rules from `references/cms-rules.md`:
If any absence mentioned → determine if allowable.
Set `allowable_absences_noted` and populate `allowable_absences`.

### 6. Generate Output

Follow `references/output-schema.md` exactly.
This step validates clinical homebound content only.
Do not assess provider credentials, signatures, or certification timing.

**Confidence scoring:**
MET with strong explicit language → 0.80 – 1.00
PARTIAL → 0.50 – 0.79
NOT_MET → 0.30 – 0.49
UNABLE_TO_DETERMINE → 0.00 – 0.29
Never assign high confidence to a non-MET status.

**Reasoning summary rules:**
- Clinical findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/homebound/results.json`.
