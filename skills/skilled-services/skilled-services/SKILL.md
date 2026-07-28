---
name: skilled-services
description: >-
  Use this skill to extract and validate skilled services documentation from a
  classified Medicare Home Health Face-to-Face encounter. Validates that each
  ordered service (SN, PT, OT, SLP, MSS, HHA) is clinically justified in the
  F2F note per MBPM Chapter 7 §30.1, §30.2, §30.3, §30.4, and §30.5.1.2.
  Does not validate homebound status, provider eligibility, or timing.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Requires classified encounter content with document-level line numbers.
  Reads client_name and poc_skilled_services from system prompt.
  CMS files: /skills/skilled-services/skilled-services/references/
  Client file: /skills/skilled-services/skilled-services/clients/<client_name>/client-rules.md
---

# skilled-services

## Overview

Validates that the F2F encounter note provides sufficient clinical justification
for each skilled service ordered on the 485. Extracts the documented reason for
each service and applies service-specific CMS rules.

**This skill does NOT validate:**
- Homebound status → homebound skill
- Primary diagnosis specificity → primary_diagnosis skill
- Provider credentials → eligible-provider skill
- Encounter date or time window → encounter-timing skill
- Signature or certification timing → document-signature skill

### Reference Files

| File | When to Read |
|------|-------------|
| `references/cms-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `references/cms-examples.md` | Step 4 — when justification judgment is borderline |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the encounter document, read:
- `references/cms-rules.md` — internalize all CMS criteria, section IDs, and service rules
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

### 2. Load Anchors and Parse Ordered Services

From the system prompt, record `poc_skilled_services` — e.g., `"SN 3x/week, PT 3x/week, HHA 7x/week"`.
Parse into a distinct list of service types: `SN`, `PT`, `OT`, `SLP`, `MSS`, `HHA`.

Read `/workspace/documents/F2F.md` in full.
**Page rule:** Use only `### Page N` markers as page numbers. Ignore printed page numbers.

### 3. Extract Justification for Each Ordered Service

For each service in the parsed list, locate the physician's clinical justification.
Focus on: `Assessment` / `Plan` / `Impression` / `Physical Examination` / `Reason for HH`

For each service:
- Assign `evidence_id` starting E001 — exact verbiage only, no paraphrase
- Record `page`, `line_start`, `line_end`, `section`
- Set `context`: `<SERVICE_TYPE> Justification` (e.g., `SN Justification`)
- Set `criterion_matched`: `SS_CLINICAL_NEXUS`
- Set `signal_strength`: STRONG / MODERATE / WEAK / ABSENT
- For SN only: set `justification_type` — see `SS_SKILLED_NECESSITY` in cms-rules.md

If a `1.9` (Physician Attestation or Co-signature) encounter is present, treat its
clinical content as part of the physician's record — not as HHA-only documentation.

If no justification found for an ordered service → `is_justified = false`, `signal_strength = ABSENT`.

### 4. Apply Service-Specific CMS Rules

**SN:**
- `SS_SKILLED_NECESSITY`: Is the service non-custodial and non-delegable after training?
- `SS_OBSERVATION_ASSESSMENT`: If justification_type is `observation_assessment` or `management_evaluation` — is condition unstable/complex requiring professional judgment? Stable/routine = WEAK.
- `SS_INTERMITTENT_BASIS`: Does documentation imply 24hr continuous care? → `continuous_care_flag`.
- If SN is justified ONLY by venipuncture → `venipuncture_only_flag = true`.

**Therapy (PT, OT, SLP):**
- `SS_CLINICAL_NEXUS`: Language check — "requires" = STRONG; "would benefit" or "may help" = WEAK.
- Rehabilitation potential OR maintenance rationale must be documented.
- Functional goal must be stated; vague goals ("improve strength") = WEAK.
- `SS_MAINTENANCE_THERAPY`: If maintenance — therapist skill must be explicitly required.

**OT:** If OT is the ONLY ordered qualifying service → `ot_initiation_flag = true`.

**MSS:** If MSS is ordered without any qualifying skilled service → `mss_standalone_flag = true`.
MSS must be directly linked to a social/emotional barrier impacting current illness — short-term only.

**HHA:** If HHA is ordered without any qualifying skilled service → `hha_standalone_flag = true`.

### 5. Score and Set Flags

Set all flags based on Step 4 checks.
Assign `signal_strength` per service based on rules applied.

**overall_status:**
- `MET` — all qualifying ordered services justified at STRONG or MODERATE
- `PARTIAL` — at least one justified; at least one WEAK or ABSENT
- `NOT_MET` — no qualifying service justified; or only non-initiating services ordered
- `UNABLE_TO_DETERMINE` — document insufficient to evaluate

Use `references/cms-examples.md` for borderline judgments.

### 6. Generate Output

Follow `references/output-schema.md` exactly.

**Confidence scoring:**
All STRONG → 0.85–1.00 | Some MODERATE → 0.80–0.84 |
PARTIAL → 0.50–0.79 | NOT_MET → 0.30–0.49 | UNABLE_TO_DETERMINE → 0.00–0.29
Never assign high confidence to a non-MET status.

**Reasoning summary rules:**
- Clinical findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/skilled-services/results.json`.
