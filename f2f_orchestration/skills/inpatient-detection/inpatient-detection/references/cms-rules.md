# Inpatient Detection — CMS Audit Rules
# Source: MBPM Pub. 100-02, Chapter 7
# §30.1.2 | §30.5.1.1
# §1814(a)(2)(C), §1835(a)(2)(A) — Social Security Act
# 42 CFR §412.3 (Two-Midnight Rule) | 42 CFR §424.22(a)(1)(v) — CY2026 (CMS-1828-F)

---

## IP_INPATIENT_EXCLUSION — Inpatient Exclusion Rule
<!-- cms_section_id: IP_INPATIENT_EXCLUSION -->

Under Chapter 7 §30.1.2, if a patient is in a hospital or SNF that institution
may not be considered their place of residence — the patient is
**not entitled to payment for HH services under either Part A or Part B**.
Source: §§1814(a)(2)(C) and 1835(a)(2)(A) of the Act; Chapter 7 §30.1.2.

This is a **timing conflict only** — not a restriction on where the F2F occurs.
The F2F may legitimately occur in a hospital or SNF (see IP_ACCEPTABLE_LOCATIONS).
The audit engine resolves the overlap using the discharge date extracted by this skill.

**Important:** This exclusion applies only to confirmed **inpatient** status.
A patient in **observation status** (outpatient Part B) is NOT subject to this exclusion.
See IP_TWO_MIDNIGHT for inpatient vs. observation distinction.

## IP_TWO_MIDNIGHT — Inpatient vs. Observation Status
<!-- cms_section_id: IP_TWO_MIDNIGHT -->
<!-- element_type: CRITERIA -->

Source: 42 CFR §412.3 (Two-Midnight Rule); CMS Hospital IPPS Rules.

A hospital encounter note may be from an **inpatient** or an **observation** patient:

| Status | Basis | Inpatient Exclusion? | HH Conflict? |
|---|---|---|---|
| `inpatient` | Physician expected 2+ midnight stay; formal admission order | YES — Part A | Timing check required |
| `observation` | Expected stay < 2 midnights; outpatient Part B | NO | HH may proceed concurrently |

**Observation signals in F2F document:**
"Observation status", "Obs", "Outpatient observation", "Under observation",
"Observation order", "Not admitted as inpatient", "23-hour observation"

**Inpatient signals:**
"Admitted as inpatient", "Admission order", "IP status", "Part A admission",
"Inpatient admission", room/bed/unit assignment with no observation language

If hospital setting is detected but neither inpatient nor observation language found:
→ set `setting_type = hospital` and `inpatient_status_unclear = true`.
If observation language found → set `setting_type = hospital_observation`,
`inpatient_flag = false`.

## IP_PLACE_OF_RESIDENCE — Inpatient ≠ Patient's Home
<!-- cms_section_id: IP_PLACE_OF_RESIDENCE -->

Chapter 7 §30.1.2: A patient's residence is wherever he or she makes his or her home.
An institution is NOT a patient's residence if it meets §§1861(e)(1) or 1819(a)(1):
hospitals and SNFs, as well as most Medicaid nursing facilities.

**SNF after active care:** When a patient remains in a participating SNF following
discharge from active care, the SNF may still NOT be considered their residence
for HH coverage purposes.

An assisted living facility not primarily engaged in providing inpatient diagnostic,
treatment, or rehabilitation services CAN qualify as a patient's residence.

## IP_ACCEPTABLE_LOCATIONS — Acceptable F2F Encounter Locations
<!-- cms_section_id: IP_ACCEPTABLE_LOCATIONS -->
<!-- element_type: CRITERIA -->

Chapter 7 §30.5.1.1 explicitly permits F2F encounters at:
- Hospitals and Critical Access Hospitals (CAH)
- Hospital-based or CAH-based Renal Dialysis Centers
- Skilled Nursing Facilities (SNF)
- Physician offices, outpatient clinics, patient's home, and any other setting

A hospital or SNF setting does NOT invalidate the F2F encounter.

## IP_SETTING_TYPES — Setting Classification
<!-- cms_section_id: IP_SETTING_TYPES -->
<!-- element_type: CRITERIA -->

| Code | CMS Classification | `inpatient_flag` |
|---|---|---|
| `hospital` | Acute inpatient — admission confirmed | `true` |
| `hospital_observation` | Hospital outpatient observation — NOT inpatient | `false` |
| `snf` | Skilled Nursing Facility — inpatient | `true` |
| `post_acute_care` | IRF, LTACH, sub-acute rehab | `true` |
| `outpatient_clinic` | Outpatient clinic / dialysis center | `false` |
| `physician_office` | Private practice / group practice | `false` |
| `patient_home` | Patient's residence / home visit | `false` |
| `unknown` | No setting indicators found | `false` — set `no_setting_documented = true` |

## IP_DIRECT_ADMISSION — Direct Admission to HH and Community Physician
<!-- cms_section_id: IP_DIRECT_ADMISSION -->

When the F2F is conducted by an inpatient physician who will NOT follow the patient
after discharge, that physician must identify a community physician/allowed practitioner
who will continue the patient's care (Chapter 7 §30.5.1.1).
Signals: "follow up with Dr.", "referred to:", "will be followed by:",
"community physician:", "PCP:", "attending after discharge:"
Post-2026 (CMS-1828-F): any allowed provider may conduct the F2F in any setting.

## IP_F2F_SETTING_2026 — F2F Setting Flexibility (CY2026)
<!-- cms_section_id: IP_F2F_SETTING_2026 -->

Under CY2026 Final Rule (CMS-1828-F), effective January 1, 2026:
- §424.22(a)(1)(v)(C) is **removed** — hospital-based physician restriction eliminated.
- Any allowed provider (MD/DO/NP/CNS/PA/CNM) may conduct the F2F in any setting.
- Pre-2026: Inpatient F2F required hospital-privileged physician who cared for the patient
  in the acute/post-acute facility from which the patient was directly admitted to HH.

This skill extracts setting and dates — the audit engine applies pre/post-2026 rules
based on encounter date from `encounter_identity`.

## IP_FLAGS — Flag Summary
<!-- cms_section_id: IP_FLAGS -->

| Flag | Condition |
|---|---|
| `inpatient_flag` | setting_type is `hospital`, `snf`, or `post_acute_care` |
| `observation_status_flagged` | setting_type is `hospital_observation` |
| `inpatient_status_unclear` | Hospital detected but neither inpatient nor observation language found |
| `no_setting_documented` | No setting indicators found anywhere; code is `unknown` |
| `no_admission_date` | inpatient_flag is true but no admission date found |
| `no_discharge_date` | inpatient_flag is true but no discharge date found |
| `direct_to_hh` | Discharge disposition explicitly references home health |
| `community_physician_absent` | Direct-to-HH detected but no follow-up physician identified |
| `part_a_signal` | Explicit Medicare Part A / inpatient billing language in document |

## Citation
MBPM Pub. 100-02, Chapter 7, §30.1.2 | §30.5.1.1
§1814(a)(2)(C) | §1835(a)(2)(A) — Social Security Act
42 CFR §412.3 (Two-Midnight Rule) | 42 CFR §424.22(a)(1)(v)
CMS-1828-F (CY2026 HH Final Rule, eff. Jan 1, 2026)
