---
name: primary_diagnosis
description: >-
  Use this skill to extract and validate primary diagnosis documentation from a
  classified Medicare Home Health Face-to-Face encounter. Validates diagnosis
  specificity, clinical relevance to the home health need, and alignment against
  the 485 anchor per MBPM Chapter 7 §30.5.1.2 and §40.2. Does not validate
  homebound status, provider eligibility, signatures, or timing.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Requires classified encounter content with document-level line numbers.
  Reads client_name, poc_icd10_code, and poc_description from system prompt.
  CMS files: /skills/primary_diagnosis/references/
  Client file: /skills/primary_diagnosis/clients/<client_name>/client-rules.md
---

# primary-diagnosis

## Overview

Extracts and validates the primary diagnosis from the F2F encounter note.
Compares it against the 485 anchor values supplied in the system prompt.
Returns structured JSON with exact verbiage, page and line provenance,
and a plain-English auditor reasoning statement.

**This skill does NOT validate:**
- Homebound status → homebound skill
- Provider credentials or supervision → eligible-provider skill
- Encounter date or time window → encounter-timing skill
- Signature or certification timing → document-signature skill

### Reference Files

| File | When to Read |
|------|-------------|
| `references/cms-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `references/clinical-rules.md` | Step 1 — always |
| `references/cms-examples.md` | Step 4 — when specificity judgment is borderline |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the encounter document, read:
- `references/cms-rules.md` — internalize all CMS criteria, thresholds, and section IDs
- `references/output-schema.md` — internalize the JSON structure and every field rule
- `references/clinical-rules.md` — internalize the three-pathway test, signal language,
  disqualifying patterns, and diagnosis-category guides

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

### 2. Load Anchors and Read Document

From the system prompt, record:
- `poc_icd10_code` — the 485 primary diagnosis code
- `poc_description` — the 485 primary diagnosis description

Read `/workspace/documents/F2F.md` in full.
**Page rule:** Use only `### Page N` markers as page numbers. Ignore printed page numbers.

### 3. Extract F2F Primary Diagnosis

Focus on these sections of the F2F certification encounter:
`Diagnosis` / `Assessment` / `Impression` / `Problem List` / `Chief Complaint`

Skip medication lists, vitals, and administrative fields unless they contain
a named diagnosis.

Extract the condition most prominently linked to the ordered skilled services:
- Assign `evidence_id` starting E001 — exact verbiage, no paraphrase
- Record `page`, `line_start`, `line_end` (document-level), `section`
- Set `context`: `F2F Primary Diagnosis`
- Set `criterion_matched`: `PD_SPECIFICITY`
- Set `signal_strength`: STRONG / WEAK / INCONCLUSIVE
- Extract `icd10_code` if coded in the note; set null if narrative-only
- List all other diagnoses as secondary (same structure, context: `F2F Secondary Diagnosis`)

If no diagnosis found → set `is_documented = false`; skip to Step 6.
If note says "see attached H&P" without naming a condition → `is_documented = false`.
If a `1.9` (Physician Attestation or Co-signature) encounter is present, treat its
clinical content as part of the physician's record — not as HHA-only documentation.

### 4. Validate Specificity

Apply `PD_SPECIFICITY` from `references/cms-rules.md`.
Use `references/cms-examples.md` when judgment is borderline.

Assign `result.f2f_primary_diagnosis.specificity`:
- `SPECIFIC` — named condition with type, acuity, or anatomic site; unambiguous ICD-10 mapping
- `VAGUE` — condition named but too general ("heart disease", "CHF" alone)
- `CONCLUSORY` — no condition named; only a statement of need
- `SYMPTOM_ONLY` — symptoms listed without underlying diagnosis when diagnosis is known

Set `result.specificity_met` = true only if specificity = `SPECIFIC`.
Apply active ELEVATE or EXCLUDE directives anchored to `PD_SPECIFICITY`.

### 5. Evaluate Active Medical Necessity and 485 Alignment

**Clinical Relevance (`PD_CLINICAL_RELEVANCE`):**
Does the F2F diagnosis explain why the ordered skilled services are needed?
Set `result.clinical_relevance_met` = true if the nexus is clear; false if
the F2F encounter addresses a routine or unrelated condition.

**Active Medical Necessity (`CR_NECESSITY_PATHWAYS`):**
Apply the three-pathway test from `references/clinical-rules.md`.
Scan the entire note — not just the section where the diagnosis appears —
for pathway signals. Use `CR_DIAGNOSIS_SIGNALS` to apply diagnosis-category-aware
pattern matching. Use `CR_NOT_MET_SIGNALS` to identify disqualifying-only language.

- Pathway A: exacerbation, functional decline, new clinical findings
- Pathway B: new or changed medication, new treatment orders, wound care orders
- Pathway C: explicit skilled service order, safety/cognitive risk, teaching need

Set `result.pathways_met` to the list of satisfied pathway codes (`A`, `B`, `C`).
Set `result.medical_necessity_met` = true if at least one pathway is satisfied.
If ONLY disqualifying language is present → `medical_necessity_met` = false.

Record in `rules_applied.clinical`:
`section_id: CR_NECESSITY_PATHWAYS` / `outcome` / `evidence_refs` / `detail` /
`negative_finding` (which pathways were searched but not found; null if satisfied).

**485 Alignment (`PD_POC_ALIGNMENT`):**
Compare the F2F primary diagnosis against `poc_icd10_code` / `poc_description`
from the system prompt:
- `ALIGNED` — same condition at equivalent or higher specificity
- `PARTIALLY_ALIGNED` — related condition at lower specificity
- `MISALIGNED` — clinically distinct condition; no causal relationship

Write one sentence in `result.alignment.basis`.

For each CMS section evaluated, record in `rules_applied.cms`:
`outcome` / `evidence_refs` / `detail` / `negative_finding` (null if PASSED).

### 6. Generate Output

Follow `references/output-schema.md` exactly.

**Confidence scoring:**
MET + coded + aligned → 0.85–1.00 | MET + narrative only → 0.80–0.84 |
PARTIAL → 0.60–0.79 | NOT_MET → 0.30–0.49 | UNABLE_TO_DETERMINE → 0.00–0.29
Never assign high confidence to a non-MET status.

**Reasoning summary rules:**
- Clinical findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.clinical** for every clinical section evaluated (CR_NECESSITY_PATHWAYS).
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/primary_diagnosis/results.json`.
