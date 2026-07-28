---
name: inpatient-detection
description: >-
  Use this skill to detect and extract inpatient setting context from a
  classified Medicare Home Health Face-to-Face encounter document. Identifies
  setting type (including observation status), facility name, admission and
  discharge dates, and discharge disposition per MBPM Chapter 7 §30.1.2,
  §30.5.1.1, and 42 CFR §412.3. Does not validate timing windows,
  Part A/B conflicts, or any other parameter.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Requires classified encounter content with document-level line numbers.
  Reads client_name from system prompt.
  CMS files: /skills/inpatient-detection/inpatient-detection/references/
  Client file: /skills/inpatient-detection/inpatient-detection/clients/<client_name>/client-rules.md
---

# inpatient-detection

## Overview

Extracts inpatient setting context from a single classified F2F encounter for use
in prebill audit. Identifies setting type (including observation status), facility
name, admission date, discharge date, and discharge disposition. Results feed the
audit engine to determine whether concurrent HH billing is at risk before the
claim is submitted.

**This skill does NOT validate:**
- Timing window (90/30-day rule) → audit engine
- Part A / HH concurrent coverage conflict → audit engine
- Provider eligibility or credentials → encounter_identity skill
- Encounter date or signature → encounter_identity skill
- Homebound status → homebound skill

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
- `references/cms-rules.md` — internalize all CMS criteria, section IDs, and setting rules
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

### 3. Detect Setting Type

Search document headers, letterhead, footers, and body for facility signals.

First check for observation status — if found, set `setting_type = hospital_observation`
and do NOT set `inpatient_flag`. Then check for confirmed inpatient. Otherwise classify
from facility indicators.

| Code | Key Indicators |
|---|---|
| `hospital_observation` | "Observation status", "Obs", "Under observation", "Outpatient observation", "23-hour obs", "observation order", "not admitted as inpatient" |
| `hospital` | "Admitted as inpatient", "Admission order", "IP status", room/bed/unit with no observation language, "H&P", "Medical Center", "Acute Care" |
| `snf` | "Skilled Nursing Facility", "SNF", "Nursing Home", "Long-Term Care", "LTC" |
| `post_acute_care` | "Rehabilitation Center", "IRF", "LTACH", "Step-Down Unit", "Sub-Acute" |
| `outpatient_clinic` | "Outpatient", "Clinic", "Ambulatory", "Dialysis Center" — no inpatient signals |
| `physician_office` | "MD Office", "Physician Practice", "Private Practice" — no facility admission language |
| `patient_home` | "Home Visit", patient address as visit location |
| `unknown` | No setting indicators found anywhere |

Hospital and SNF are valid F2F locations (§30.5.1.1); they trigger a timing check only.
Set `inpatient_flag = true` for `hospital` / `snf` / `post_acute_care`.
Set `observation_status_flagged = true` for `hospital_observation`.
Set `inpatient_status_unclear = true` if hospital letterhead present but status unclear.
Set `no_setting_documented = true` for `unknown`.

### 4. Extract Facility Information

Search for: facility name in document letterhead, header, or body text.
Capture `facility_name` verbatim. Set `not_found = true` if absent.

### 5. Extract Admission and Discharge Dates

**Admission date:** Search for "Admit Date", "Admission Date", "Date Admitted",
"Admitted:", or "Date of Admission". Normalize to ISO 8601.
Set `no_admission_date = true` if inpatient_flag is true but no admission date found.

**Discharge date:** Search for "Discharge Date", "Date of Discharge", "Discharged:",
"D/C Date", "Expected Discharge". Normalize to ISO 8601.
Set `no_discharge_date = true` if inpatient_flag is true but no discharge date found.

### 6. Extract Discharge Disposition and Community Physician

**Discharge disposition:**
Search for: "Discharge Disposition", "Discharge To", "Discharged To",
"Plan for discharge", "Follow-up care", "Post-discharge plan".
Capture full verbatim text. Set `direct_to_hh = true` if disposition text
explicitly references home health (e.g., "home with home health services",
"HHA follow-up", "home health agency").
Set `not_found = true` if no discharge disposition language found.

**Community physician (when direct_to_hh = true):**
Search for: "follow up with Dr.", "referred to:", "will be followed by:", "PCP:",
"community physician:", "attending after discharge:". Capture name verbatim.
Set `community_physician_absent = true` if `direct_to_hh` is true and none found.

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

Set `observation_status_flagged = true` if setting_type is `hospital_observation`.
Set `inpatient_status_unclear = true` if hospital letterhead detected but no
inpatient or observation language is present.
Set `community_physician_absent = true` if `direct_to_hh = true` but no follow-up
physician identified in the note.
Set `part_a_signal = true` if document contains explicit Medicare Part A language
("Part A", "inpatient claim", "DRG", "Medicare inpatient") concurrent with HH.

### 8. Generate Output

Follow `references/output-schema.md` exactly.

**Confidence scoring:**
INPATIENT_DETECTED with clear facility + dates → 0.80 – 1.00
OBSERVATION_DETECTED with clear observation language → 0.80 – 1.00
NOT_INPATIENT → 0.70 – 1.00
PARTIAL → 0.50 – 0.79
UNABLE_TO_DETERMINE → 0.00 – 0.49
Never assign high confidence to a non-INPATIENT_DETECTED status without evidence.

**Reasoning summary rules:**
- Findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/inpatient-detection/results.json`.
