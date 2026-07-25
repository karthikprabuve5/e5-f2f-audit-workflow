---
name: telehealth_identity
description: >-
  Extracts telehealth-specific identity parameters from a single pre-classified
  telehealth encounter document: modality, platform, patient/provider locations,
  consent, conducting provider, and signature.
  Pure extraction only — no CMS eligibility validation.
metadata:
  author: f2f-audit-system
  version: "1.0"
compatibility: >-
  Processes one telehealth encounter document per invocation
  (category: telehealth_encounter). Splitting and routing handled by
  the classification skill. Reads client_name from system prompt.
  CMS files: /skills/telehealth_identity/references/
  Client file: /skills/telehealth_identity/clients/<client_name>/client-rules.md
---

# telehealth_identity

## Overview

Extracts eight parameter groups from a single telehealth encounter document
passed as `/workspace/documents/F2F.md`.
Output saved to `/workspace/documents/outputs/telehealth_identity/results.json`.

**Parameters extracted:**
1. `telehealth_indicator` — exact keyword/phrase confirming telehealth modality
2. `modality` — audio+video / audio-only / video-only / unknown
3. `platform` — technology/software used if documented
4. `patient_location` — patient's location during the encounter
5. `provider_location` — provider's location during the encounter
6. `consent` — whether telehealth consent is documented
7. `conducting_provider` — name, credentials, type (with name normalization)
8. `signature` — type, signer details, cosign status

Encounter date, provider eligibility, and cosign validation are handled by
`encounter_identity` and the audit engine — not duplicated here.

**This skill does NOT validate** timing (90/30-day rule), provider eligibility,
audio-only restrictions, or modality sufficiency — all validation is downstream.

### Reference Files

| File | When to Read |
|------|-------------|
| `references/telehealth-rules.md` | Step 1 — always |
| `references/output-schema.md` | Step 1 — always |
| `encounter_identity/references/provider-rules.md` | Step 1 — EP_NAME_NORMALIZATION |
| `clients/<client_name>/client-rules.md` | Step 1 — only if client_name != DEFAULT |

---

## Instructions

### 1. Read Mandatory Reference Files

Before touching the encounter document, read:
- `references/telehealth-rules.md` — internalize all CMS criteria, section IDs, and flags
- `references/output-schema.md` — internalize the JSON structure and every field rule
- `encounter_identity/references/provider-rules.md` — EP_NAME_NORMALIZATION

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

Read `/workspace/documents/F2F.md` in full. One encounter per invocation.
**Page rule:** Use only `### Page N` markers as page numbers.

### 3. Extract Telehealth Indicator

Search all pages for explicit telehealth keywords.
Capture the first confirming phrase as `telehealth_indicator.keyword` and `verbatim`.

Known keywords: "Telehealth", "Telemedicine", "Video Visit", "Virtual Visit",
"Telephone Encounter", "Remote Visit", "audio-only", "audio/video", "E-Visit",
"Patient Portal Visit".

If none found: `not_found = true`.

### 4. Extract Modality

Determine modality from document text:

| Code | Indicators |
|---|---|
| `audio_video` | "video", "audio and video", "audio/video", "A/V", live video session language |
| `audio_only` | "audio only", "telephone only", "phone visit", "no video", "telephone call" |
| `video_only` | "video only" (rare; absence of audio reference) |
| `unknown` | Telehealth confirmed but modality not explicitly stated |

Capture `raw` text and page/line. Set `no_modality_documented = true` if unknown.

### 5. Extract Patient and Provider Locations

**Patient location:** Search for "patient location", "patient site", "originating site",
"patient was located at", "patient calling from". Capture verbatim, page.

**Provider location:** Search for "provider location", "distant site", "provider was located at",
"physician location", "provider calling from". Capture verbatim, page.

Not found → `not_found = true` for that field.

### 6. Extract Telehealth Consent

Search for: "telehealth consent", "patient consented", "informed consent for telehealth",
"consent obtained", "patient agreed to telehealth", "verbal consent".

`documented = true` if any consent language found. `false` if absent or declined.
Set `no_consent = true` flag if `documented = false`.

### 7. Extract Conducting Provider and Signature

Apply EP_NAME_NORMALIZATION from `encounter_identity/references/provider-rules.md`.

**Provider:** Look for "Performed By", "Attending Provider", "Treating Provider",
"Rendering Provider", provider header block. Capture name, credentials, provider_type.
Do NOT check eligibility or cosign — the audit engine uses encounter_identity output for that.

**Signature:** Prefer electronic over physical/typed. Capture signature_type, display_name,
date_signed. Do NOT assess cosign requirements — that is downstream.

Set `synchronous_not_confirmed = true` if no real-time language found anywhere in document.
Set all other applicable flags per `references/telehealth-rules.md` TH_FLAGS section.

### 8. Generate Output

Follow `references/output-schema.md` exactly.

**Confidence scoring:**
EXTRACTED with all parameters found and strong signals → 0.80 – 1.00
PARTIAL → 0.50 – 0.79
UNABLE_TO_DETERMINE → 0.00 – 0.49
Never assign high confidence to a non-EXTRACTED status.

**Reasoning summary rules:**
- Findings only — no PII of any kind
- No inline page or line references — those live in sources
- One to two sentences maximum

**Populate reasoning.sources** using evidence_ids cited in summary.
**Populate rules_applied.client** for every directive evaluated.
Return **only** the valid JSON object.
Save to `/workspace/documents/outputs/telehealth_identity/results.json`.
