<!-- ============================================================ -->
<!-- Client Rules — surgical_note                             -->
<!-- Client: CLIENT_A                                         -->
<!-- Effective: 2026-01-01                                    -->
<!-- Approved By: Compliance Director                         -->
<!-- Version: 1.0                                             -->
<!--                                                          -->
<!-- All directives apply ON TOP of CMS regulations.         -->
<!-- CMS requirements are never waived or reduced.           -->
<!-- EXCLUDE and REPLACE apply only to element_type:         -->
<!-- ILLUSTRATION / EXAMPLE / SUGGESTION                     -->
<!-- Never target REGULATION / REQUIREMENT / CRITERIA        -->
<!-- ============================================================ -->

## DIRECTIVE SN-001 | EXTEND | SN_HH_CONTENT

**Step:** 5
**Field:** hh_relevant_content
**Affects Status:** NO

**Check:**
In addition to standard HH-content signals, treat CLIENT_A's standard
post-surgical order phrase "DC orders: HHC" (Home Health Care) as a
strong direct HH referral indicator even without further specification.

**If Not Met:**
Add to reasoning.agency_warnings: "CLIENT_A HHC order phrase not found — standard HH content search applied."

**Business Reason:**
CLIENT_A uses a standardized discharge order abbreviation that standard
CMS signal phrases do not capture, causing false no_hh_content flags.

---

## DIRECTIVE SN-002 | ELEVATE | SN_F2F_CONTENT

**Step:** 6
**Field:** f2f_adequate
**Affects Status:** YES

**CMS Condition:**
HH-relevant content must be present in the surgical note.

**Client Condition:**
HH-relevant content must appear in the Plan, Assessment, or Discharge sections
of the note specifically — not only in procedure or intraoperative sections.

**If Not Met:**
Set f2f_adequate to false. Populate reasoning.missing with:
"HH-relevant content not found in Plan/Assessment/Discharge sections per CLIENT_A directive SN-002."

**Business Reason:**
CLIENT_A MAC reviewers consistently question HH referrals documented only
within the procedure body rather than the clinical assessment sections.
