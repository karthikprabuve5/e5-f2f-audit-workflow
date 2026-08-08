---
name: encounter-identity
description: >-
  Extracts encounter date, validates signatures, and identifies the conducting
  provider from a single pre-classified clinical encounter document. Applies 2026
  CMS Final Rule provider eligibility rules (CMS-1828-F, 42 CFR §424.22(a)(1)(v)).
  Does not validate the 90/30-day timing window — handled by the audit engine.
  Document splitting and routing is handled by the classification skill.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Reads client_name from system prompt.
  CMS files: /skills/encounter-identity/encounter-identity/references/
  Client file: /skills/encounter-identity/encounter-identity/clients/<client_name>/client-rules.md
---

# encounter-identity

## Overview

Processes a single clinical encounter document and extracts three linked outputs:
- `encounter_date` — Date of Service, normalized to ISO 8601
- `signature` — all signers with type, source, and provenance
- `eligible_provider` — conducting provider, allowed status, and co-sign

**This skill does NOT validate:**
- Homebound status → homebound skill
- Primary diagnosis → primary_diagnosis skill
- Skilled services → skilled_services skill
- 90/30-day timing window → audit engine

**Input:** One pre-classified encounter document. The classification skill handles splitting and routing.

### Reference Files

| File | When to Read |
|------|-------------|
| `references/date-rules.md` | Step 1 — always |
| `references/provider-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `references/examples.md` | Steps 4–5 — borderline judgment |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the document, read:
- `references/date-rules.md` — internalize all date extraction rules and section IDs
- `references/provider-rules.md` — internalize EP eligibility, signature, and name normalization rules
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

### 2. Read the Document

Read `/workspace/documents/F2F.md` in full.
**Page rule:** Use only `### Page N` markers as page numbers for all citations.

### 3. Extract Encounter Date

Apply priority from `references/date-rules.md`:

1. Labeled: "Date of Service" / "DOS" / "Date Seen" / "Service Date" → `high`
2. Labeled: "Visit Date" / "Encounter Date" → `high`
3. Unlabeled date in header (only date on page 1) → `medium`
4. Body text with signal ("seen today on", "encounter on", "patient presented on") → `medium`
5. Signature date only → `low`
6. No date → `null` + `no_date_found = true`

Normalize to ISO 8601 (YYYY-MM-DD). Two-digit years → 20XX.
Set flags: `ambiguous_format`, `partial_date`, `multiple_dates_conflict`,
`late_documentation` (sig date − encounter date > 30 days), `has_addendum`.

### 4. Extract Signatures — Electronic Always First

**Electronic scan (highest priority):**
Patterns: "Electronically signed by:", "Signed electronically:", "/s/", "e-signed:"
→ Extract all: name, credentials, date, time → `source: plain_text`, `type: electronic_verified`

**Physical fallback (only if no electronic found):**
`<signature>` tag with name/credentials → `type: handwritten`; empty/signed-only → `illegible_signature = true`

**Signed-status fallback (only if neither above found):**
"signed" / "signature on file" in header or body text → `signed = true`, confidence `low`

For each signer: record name, credentials, signature_date, signature_time, role_label, source, type.
Apply `EP_NAME_NORMALIZATION` (provider-rules.md) → set `name_format` and `display_name` for each signer.
Set `signature_undated = true` if no date on the signature.

### 5. Determine Conducting Provider and Co-Sign

**Electronic cross-match (apply in order — stop at first resolved):**

1. Normalize "Performed By" / "Author" / "Authored by:" field → `performed_by_display_name` via `EP_NAME_NORMALIZATION`.
   Match against signer `display_name` (case-insensitive):
   - Match → `identification_method: performed_by_match`, confidence `high`
   - Mismatch → `electronic_signature_mismatch = true`, confidence `low`

2. Single electronic signer, no Performed By → conducting provider, confidence `medium`

3. Multiple electronic signers:
   - Role labels: "Resident/Intern/Student" → NOT conductor → `cosign_required = true`
   - "Attending/Ordering" → conductor; "Co-sign/Attestation" → NOT conductor
   - No labels → match against Performed By field
   - Still ambiguous → MD/DO priority over NPPs
   - Multiple MDs, no resolution → `conducting_provider_ambiguous = true` + reason

**Physical/status fallback:** use Performed By for provider details; physical/status confirms signed.

**Resident detection:** credentials contain "Resident", "PGY-", "Intern", "Student"
→ `resident_conductor = true` → `cosign_required = true`

**Provider type validation:**
Check against 2026 allowed list in `provider-rules.md`.
CNM → `cnm_state_authorization_note = true`.
Unrelated specialty → `specialty_mismatch = true`.

**Co-sign validation (if cosign_required):**
- Found + allowed + dated → `is_valid = true`
- Found + not allowed → `cosigner_not_allowed_type = true`, `is_valid = false`
- Found + no date → `cosign_undated = true`
- Absent → `cosign_required_but_absent = true` → status NOT_MET

### 6. Generate Output

Follow `references/output-schema.md` exactly.

**Status:**
- `MET` — date extracted + allowed provider + valid signature + co-sign resolved
- `PARTIAL` — low confidence on one component or non-critical flag raised
- `NOT_MET` — absent signature, not-allowed provider, or co-sign required but missing
- `UNABLE_TO_DETERMINE` — document insufficient to evaluate any component

**Confidence scoring:**
All high → 0.85–1.00 | Some medium → 0.70–0.84 | Some low → 0.50–0.69 |
PARTIAL → 0.30–0.49 | NOT_MET → 0.10–0.29
Never assign high confidence to a non-MET status.

**Reasoning summary rules:**
- Factual findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/encounter-identity/results.json`.
