<!-- ============================================================ -->
<!-- Client Rules — homebound_status                              -->
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

## DIRECTIVE HB-001 | ELEVATE | HB_CRITERIA_TWO

**Step:** 4
**Field:** prong_2_met
**Affects Status:** YES

**CMS Condition:**
Leaving home requires considerable and taxing effort.

**Client Condition:**
Considerable and taxing effort language must be present AND
an assistive device or specific diagnosis must be explicitly
mentioned in the same statement as the effort language.

**If Not Met:**
Set prong_2_met to false. Populate reasoning.missing with gap description.

**Business Reason:**
23% higher first-pass approval rate when effort language
includes device or diagnosis specificity per internal audit data.

---

## DIRECTIVE HB-002 | EXTEND | HB_SUPPORTING_DOCS

**Step:** 3
**Field:** evidence
**Affects Status:** NO

**Check:**
Homebound statement must appear in the F2F encounter note itself —
not only in a progress note or discharge summary.

**If Not Met:**
Add to reasoning.agency_warnings. Do not change overall status.

**Business Reason:**
Reduces auditor queries by 40% when homebound statement
appears directly in F2F note per internal data.

---

## DIRECTIVE HB-003 | EXCLUDE | HB_NON_QUALIFYING

**Step:** 4
**Field:** prong_1_met
**Element Type:** ILLUSTRATION

**Excludes:**
Advanced age alone non-qualifying illustration from CMS §30.1.1.

**Client Exception:**
Advanced age (90+) combined with explicit physician attestation
of functional limitation is acceptable for Prong 1 when
documented by MD or DO in the encounter note.

**If Applied:**
Note in reasoning.agency_warnings:
"Advanced age non-qualifier illustration excluded per HB-003."

**Approved By:** Compliance Director

---

## DIRECTIVE HB-004 | REPLACE | HB_LANGUAGE_STANDARDS

**Step:** 3
**Field:** evidence
**Element Type:** EXAMPLE

**Replaces:**
CMS classification of "Patient is homebound" as unacceptable
(conclusory without clinical basis).

**Client Version:**
"Patient is homebound" is acceptable IF accompanied by physician
attestation checkbox on client standard F2F form (Form HH-2026).

**If Applied:**
Note in reasoning.agency_warnings:
"Language standard replaced per HB-004. Two-prong test
still validated independently."

**Approved By:** Compliance Director
