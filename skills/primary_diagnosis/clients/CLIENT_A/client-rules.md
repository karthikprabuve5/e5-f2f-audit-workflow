<!-- ============================================================ -->
<!-- Client Rules — primary_diagnosis                             -->
<!-- Client: CLIENT_A                                             -->
<!-- Effective: 2026-01-01                                        -->
<!-- Approved By: Compliance Director                             -->
<!-- Version: 1.0                                                 -->
<!--                                                              -->
<!-- All directives apply ON TOP of CMS regulations.             -->
<!-- CMS requirements are never waived or reduced.               -->
<!-- EXCLUDE and REPLACE apply only to element_type:             -->
<!-- ILLUSTRATION / EXAMPLE / SUGGESTION                         -->
<!-- Never target REGULATION / REQUIREMENT / CRITERIA            -->
<!-- ============================================================ -->

## DIRECTIVE PD-001 | ELEVATE | PD_SPECIFICITY

**Step:** 4
**Field:** specificity_met
**Affects Status:** YES

**CMS Condition:**
Named condition with type, acuity, or anatomic site = SPECIFIC.

**Client Condition:**
An explicit ICD-10 code must also be present in the F2F note itself —
narrative description alone, however specific, is not sufficient.

**If Not Met:**
Set specificity_met to false. Populate reasoning.missing with:
"ICD-10 code absent from F2F note — required per CLIENT_A directive PD-001."

**Business Reason:**
CGS MAC denied 18% of narrative-only claims where the diagnosis
could not be unambiguously coded by the reviewer. Requiring an
explicit code in the note reduced denials to under 3%.

---

## DIRECTIVE PD-002 | EXTEND | PD_F2F_DOCUMENTATION

**Step:** 3
**Field:** evidence
**Affects Status:** NO

**Check:**
The primary diagnosis must appear in the `Assessment`, `Impression`,
or `Diagnosis` section of the F2F note. A diagnosis found only in
the HPI or Plan section does not satisfy this check.

**If Not Met:**
Add to reasoning.agency_warnings:
"Primary diagnosis not in Assessment/Impression/Diagnosis section — found only in [section]. Clinical team should reposition per CLIENT_A standard."

**Business Reason:**
Internal QA data shows a 35% higher MAC reviewer query rate when
the primary diagnosis appears only in narrative sections rather than
the structured Assessment or Impression field.

---

## DIRECTIVE PD-003 | EXCLUDE | PD_NON_QUALIFYING

**Step:** 4
**Field:** specificity_met
**Element Type:** ILLUSTRATION

**Excludes:**
CMS non-qualifying illustration: "single abbreviation without context
(e.g., DM, HTN, CVA) is not acceptable as a primary diagnosis."

**Client Exception:**
On CLIENT_A standard Form PD-2026, the following pre-printed
checkboxes are acceptable as SPECIFIC when the form legend is
attached to the submission:
- `DM2` → E11.9 (Type 2 diabetes mellitus without complications)
- `CHF-S` → I50.20 (Unspecified systolic heart failure)
- `CHF-D` → I50.30 (Unspecified diastolic heart failure)
- `HTN` → I10 (Essential hypertension)

The checkbox + attached form legend = specific coded diagnosis.

**If Applied:**
Note in reasoning.agency_warnings:
"Abbreviation non-qualifier illustration excluded per PD-003.
Form PD-2026 checkbox with legend treated as coded specific diagnosis."

**Approved By:** Compliance Director

---

## DIRECTIVE PD-004 | REPLACE | PD_SPECIFICITY

**Step:** 3
**Field:** evidence
**Element Type:** EXAMPLE

**Replaces:**
CMS example: abbreviations alone ("DM", "HTN", "CVA") = Not Acceptable.

**Client Version:**
On CLIENT_A Form PD-2026, the following abbreviations in the
diagnosis field ARE acceptable as SPECIFIC when:
1. The Form PD-2026 legend page is present in the submission, AND
2. The 485 anchor codes to the same ICD-10 condition.

Accepted mappings: `DM2` = E11.9 | `HTN` = I10 |
`CHF-SYS` = I50.20 | `CVA-R` = I69.354 | `COPD-AE` = J44.1

**If Applied:**
Note in reasoning.agency_warnings:
"Abbreviation standard replaced per PD-004. Form PD-2026 legend
present — abbreviation treated as coded specific diagnosis.
485 alignment still validated independently."

**Approved By:** Compliance Director
