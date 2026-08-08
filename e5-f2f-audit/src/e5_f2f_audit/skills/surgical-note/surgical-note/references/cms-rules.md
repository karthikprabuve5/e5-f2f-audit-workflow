# Surgical Note Validation — CMS Audit Rules
# Source: MBPM Pub. 100-02, Chapter 7
# §30.5, §30.5.1, §30.5.1.1, §30.5.1.2
# 42 CFR §424.22(a)(1)(v) — amended CY2026 (CMS-1828-F)

---

## SN_F2F_CONTENT — F2F Documentation Content Requirements
<!-- cms_section_id: SN_F2F_CONTENT -->
<!-- element_type: CRITERIA -->

Source: Chapter 7 §30.5.1; 42 CFR §424.22(a)(1)(v).

A Face-to-Face encounter document must satisfy ALL of the following:
1. Documents a direct physician-patient clinical encounter (not procedure steps alone)
2. Contains clinical findings that support the patient's need for home health services
3. Includes the date of the encounter (extracted by `encounter_identity`)
4. Is related to the primary reason the patient requires HH services

For surgical notes, "clinical findings supporting HH need" means documentation of:
- Post-surgical wound care requirements (wound management, drain care, dressing changes)
- Post-surgical rehabilitation needs (PT, OT, SLP ordered or anticipated)
- Functional limitations resulting directly from the procedure or surgical condition
- Medication or infusion therapy to be administered at home
- Physician assessment of recovery requirements that necessitate skilled home care

**Inadequate alone:** Procedure description, anesthesia record, consent form,
intraoperative vital signs, or sponge/instrument counts do not establish HH need.

## SN_NOTE_TYPE — Note Type Validity for F2F
<!-- cms_section_id: SN_NOTE_TYPE -->
<!-- element_type: CRITERIA -->

| Code | Valid F2F? | CMS Basis |
|---|---|---|
| `pre_op_note` | CONDITIONAL | Valid only if it also documents anticipated post-surgical HH need — a note addressing only pre-surgical condition without HH planning is insufficient |
| `post_op_note` | YES | Clinical encounter documenting recovery — strongest surgical F2F |
| `surgical_consult` | YES | Consulting physician's clinical assessment; certifier must be the consultant |
| `discharge_summary` | YES | Physician-authored summary documenting clinical condition and discharge plan |
| `operative_note` | CONDITIONAL | Valid only if a physician clinical assessment is embedded (pre/post-op section); procedure steps alone are insufficient |
| `anesthesia_note` | NO | Documents anesthesia administration only; anesthesiologist is not the HH certifying physician |
| `unknown` | UNABLE_TO_DETERMINE | Note type cannot be determined |

**Operative note adequacy test:** An operative note is valid F2F only when it contains
a documented clinical assessment of the patient's condition and functional status
beyond the procedure steps themselves. A post-operative note embedded within the
operative report satisfies this requirement.

## SN_ANESTHESIA_EXCLUSION — Anesthesia Notes Are Not Valid F2F
<!-- cms_section_id: SN_ANESTHESIA_EXCLUSION -->
<!-- element_type: CRITERIA -->

Source: Chapter 7 §30.5.1; 42 CFR §424.22(a)(1)(v).

An anesthesia record, pre-anesthesia evaluation, or CRNA note is NOT valid as
a F2F encounter document because:
- The anesthesiologist or CRNA is not the certifying physician for HH services
- The document focuses on anesthesia administration, not clinical assessment for HH
- The encounter is with the anesthesia provider, not the certifying physician

If the ONLY surgical documentation available is an anesthesia note, the F2F
encounter is not adequately documented — the prebill claim requires additional
clinical documentation from the certifying physician.

## SN_HH_CONTENT — HH-Relevant Content Standards
<!-- cms_section_id: SN_HH_CONTENT -->
<!-- element_type: CRITERIA -->

Source: Chapter 7 §30.5.1.2 — Documentation Standards.

**Strong HH-content signals (STRONG signal_strength):**
- Explicit HH referral: "Patient to be discharged home with home health services"
- Specific skilled care ordered: "Home PT 3x/week for gait training", "wound care daily"
- Functional limitation detail: "Unable to ambulate without assistance due to [procedure]"
- Physician assessment of post-surgical home care requirements with clinical specificity

**Weak HH-content signals (WEAK signal_strength):**
- Vague: "Patient will need home care", "follow-up at home"
- Conclusory: "HH needed" without clinical basis
- Implied: discharge plan mentions HH without physician assessment context

**No HH content (set no_hh_content = true):**
- Procedure steps only, no patient assessment
- Post-op vital signs without functional assessment
- Only anesthesia, consent, or instrument counts documented

## SN_SETTING — Acceptable Surgical F2F Locations
<!-- cms_section_id: SN_SETTING -->
<!-- element_type: CRITERIA -->

Source: Chapter 7 §30.5.1.1.

All surgical settings are acceptable F2F encounter locations:
- Hospital Operating Room (inpatient or outpatient surgery)
- Ambulatory Surgical Center (ASC)
- Hospital Outpatient Department (HOPD)
- Physician office procedure room

Setting type does not affect F2F validity — all surgical locations are permitted.
Note: ASC and HOPD encounters are outpatient (Part B); inpatient OR is Part A.
Inpatient status is determined by `inpatient_detection` skill, not this skill.

## SN_FLAGS — Flag Summary
<!-- cms_section_id: SN_FLAGS -->

| Flag | Condition |
|---|---|
| `anesthesia_only` | note_type is `anesthesia_note` — not a valid F2F |
| `operative_note_only` | note_type is `operative_note` with no embedded clinical assessment |
| `no_hh_content` | No content linking surgical condition to HH need found anywhere |
| `procedure_only` | Document contains only procedural steps and intraoperative data |
| `hh_content_weak` | HH-relevant content found but vague or conclusory without clinical specificity |
| `discharge_summary_hh_referenced` | Discharge summary explicitly references HH — strongest surgical F2F signal |

## Citation
MBPM Pub. 100-02, Chapter 7, §30.5 | §30.5.1 | §30.5.1.1 | §30.5.1.2
42 CFR §424.22(a)(1)(v) | CMS-1828-F (CY2026 HH Final Rule, eff. Jan 1, 2026)
