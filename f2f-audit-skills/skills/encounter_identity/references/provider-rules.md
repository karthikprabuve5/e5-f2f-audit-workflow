# Eligible Provider + Signature — CMS Audit Rules
# Source: MBPM Pub. 100-02, Chapter 7, §30.5.1.2
# 42 CFR §424.22(a)(1)(v) — amended by CY2026 HH PPS Final Rule (CMS-1828-F)
# CMS PIM Pub. 100-08, Chapter 3, §3.3.2.4
# Effective: January 1, 2026

---

## Allowed F2F Practitioners — 2026
<!-- cms_section_id: EP_ELIGIBLE_PROVIDER -->

| Provider Type | Code | Notes |
|---|---|---|
| Physician — MD or DO | `physician_md_do` | Any physician (2026 rule removes restriction to certifying physician) |
| Nurse Practitioner | `nurse_practitioner_np` | Authorized under §1861(aa)(5) |
| Clinical Nurse Specialist | `clinical_nurse_specialist_cns` | Authorized under §1861(aa)(6) |
| Physician Assistant | `physician_assistant_pa` | Authorized under §1861(aa)(5) |
| Certified Nurse-Midwife | `certified_nurse_midwife_cnm` | Added CY2026; must be authorized by state law |
| Unknown | `unknown` | Credentials illegible or not found |
| Not Allowed | `not_allowed` | RN (non-NP), LPN, PT, OT, SW, HHA, aide, non-credentialed staff |

**2026 Key Changes:**
- Any physician may conduct the F2F — not limited to certifying physician or hospital physician.
  (§424.22(a)(1)(v)(C) exception removed effective Jan 1, 2026.)
- CNM added as allowed practitioner if authorized by state law.

**Specialty relevance:** Conducting provider must have firsthand knowledge of the
patient's primary HH reason. Unrelated specialist → `specialty_mismatch = true`.

**Care coordination:** Whether the conducting provider matches the certifying
physician is validated by the audit engine — not this skill.

---

## Signature Types
<!-- cms_section_id: EP_SIGNATURE_TYPES -->

| Type Code | Description | Confidence | Source Tag |
|---|---|---|---|
| `electronic_verified` | "Electronically signed by:" / "/s/" / EHR timestamp | High | Plain text |
| `handwritten` | Physical signature — name and credentials readable | Medium | `<signature>` tag |
| `typed_unverified` | Typed name only, no EHR authentication prefix | Low | Plain text |
| `stamp` | Rubber/pre-printed stamp — generally rejected by MACs | Low | `<signature>` tag |
| `handwritten_unreadable` | Illegible content in `<signature>` tag | Low | `<signature>` tag |
| `absent` | No signature found anywhere in encounter | None | — |

**Priority:** `electronic_verified` > `handwritten` > `typed_unverified` > `stamp` > signed-status text

---

## Conducting Provider — Identification Methods
<!-- cms_section_id: EP_IDENTIFICATION -->

Apply in order — stop at first resolved match:

| Method Code | Rule | Confidence |
|---|---|---|
| `performed_by_match` | Electronic signer name = "Performed By" / "Author" / "Authored by:" field | High |
| `role_label_attending` | Signer has explicit role label "Attending" or "Ordering Provider" | High |
| `role_label_cosign` | Label is "Co-sign" / "Attestation" → NOT the conductor | — |
| `single_electronic` | Only one electronic signer; no Performed By field | Medium |
| `multiple_resolved` | Multiple signers; role label or Performed By resolves conductor | Medium |
| `md_do_priority` | Multiple signers, no labels; MD/DO given priority over NPPs | Medium |
| `earliest_signature` | Multiple same-credential signers; earliest date/time wins | Low |
| `ambiguous` | No rule resolves it; set `conducting_provider_ambiguous = true` | Low |

When `ambiguous`: document all signers in the output; state the disambiguation
reason explicitly in the reasoning summary.

---

## Resident / Student Detection
<!-- cms_section_id: EP_RESIDENT -->

Credential or role indicators that trigger resident detection:
"Resident", "PGY-1", "PGY-2", "PGY-3", "PGY-4", "Intern",
"MD Candidate", "DO Student", "R1", "R2", "R3", "R4", "Medical Student"

When detected: `resident_conductor = true` → `cosign_required = true`.
The valid co-signer must be from the 2026 allowed provider list and must be dated.

---

## Co-Sign Requirements
<!-- cms_section_id: EP_COSIGN -->

| Situation | Co-sign Required? |
|---|---|
| Note authored by resident / intern / student | YES |
| Note authored by HHA staff (RN, LPN, PT, OT, SW, aide) | YES — HHA corroboration rule |
| Note authored by allowed provider (MD/DO/NP/PA/CNS/CNM) | NO per 2026 rules |
| Allowed provider + voluntary co-sign present | Capture — no status impact |

**Co-signer validity:** Must be from the 2026 allowed list. Must carry a date.
For HHA-authored notes: preferred co-signer is the certifying physician.

**Co-sign flags:**

| Flag | Condition |
|---|---|
| `cosign_required_but_absent` | Required; no co-signer signature found → NOT_MET |
| `cosigner_not_allowed_type` | Co-signer credentials not on 2026 allowed list → `is_valid = false` |
| `cosign_undated` | Co-sign signature has no associated date |

---

## Provider Name Normalization
<!-- cms_section_id: EP_NAME_NORMALIZATION -->

Names appear in four formats in both "Performed By" and electronic signature blocks.
Always detect, normalize, and store — then use `display_name` for all cross-matching.

| Format Code | Pattern | Example |
|---|---|---|
| `FNAME_LNAME` | First Last | `John Smith` |
| `FNAME_M_LNAME` | First Middle Last | `John A Smith` |
| `LNAME_FNAME` | Last, First | `Smith, John` |
| `LNAME_FNAME_M` | Last, First Middle | `Smith, John A` |

**Algorithm:**
1. Strip credentials (MD, DO, NP, PA, CNS, CNM, RN, APRN…) from the raw string.
2. Comma present → Last-First format; one token after comma = `LNAME_FNAME`, two = `LNAME_FNAME_M`.
3. No comma → First-Last format; two tokens = `FNAME_LNAME`, three = `FNAME_M_LNAME`.
4. Build `display_name`: `FNAME [M] LNAME, CREDENTIALS` (omit credentials if not found).

**Cross-match rule:** Always compare `display_name` values case-insensitively.
Never compare raw strings — format differences cause false mismatches.

**Required fields on each signer and on conducting_provider:**
`name` (raw) | `name_format` | `display_name`

**Required fields on eligible_provider:**
`performed_by_raw` | `performed_by_format` | `performed_by_display_name`

---

## Citation
42 CFR §424.22(a)(1)(v) | CMS-1828-F (CY2026 HH PPS Final Rule, eff. Jan 1, 2026)
MBPM Pub. 100-02, Chapter 7, §30.5.1.2 | CMS PIM Pub. 100-08, Chapter 3, §3.3.2.4
Consolidated Appropriations Act, 2021 (NP/PA/CNS ordering authority, eff. Jan 1, 2022)
