<!-- ============================================================ -->
<!-- Client Rules — poc_485_extraction                         -->
<!-- Client: CLIENT_A                                          -->
<!-- Effective: 2026-01-01                                     -->
<!-- Approved By: Compliance Director                          -->
<!-- Version: 1.0                                              -->
<!--                                                           -->
<!-- All directives apply ON TOP of CMS regulations.          -->
<!-- CMS requirements are never waived or reduced.            -->
<!-- EXCLUDE and REPLACE apply only to element_type:          -->
<!-- ILLUSTRATION / EXAMPLE / SUGGESTION                      -->
<!-- Never target REGULATION / REQUIREMENT / CRITERIA         -->
<!-- ============================================================ -->

## DIRECTIVE POC-001 | REPLACE | POC_SKILLED_SERVICES

**Step:** 4
**Field:** ordered_services
**Element Type:** EXAMPLE

**Replaces:**
Default section label: `**Frequency/Duration of Visits:**`

**Client Version:**
CLIENT_A 485 uses `**Visit Frequency Schedule:**` as the section header
for skilled services. Search for this label when the default label is absent.

**If Applied:**
Note in extraction: "Skilled services label replaced per POC-001 — used Visit Frequency Schedule."

**Approved By:** Compliance Director

---

## DIRECTIVE POC-002 | EXTEND | POC_F2F_DATE

**Step:** 6
**Field:** f2f_encounter_date
**Affects Status:** YES

**Check:**
CLIENT_A uses a third certification statement in addition to i_certify and undersigned:
Trigger: `"THE PROVIDER ATTESTS TO THE FACE-TO-FACE ENCOUNTER PERFORMED ON"`
Date anchor: `"ON"` — date follows immediately after this keyword.

Extract this as `f2f_encounter_date.custom` with the same field structure
as `i_certify` and `undersigned` (verbiage, line_start, line_end, value, raw,
is_present, page_start, page, not_found).

**If Not Met:**
Set `f2f_encounter_date.custom.not_found = true`. Do not error.

**Business Reason:**
CLIENT_A's EHR generates a third attestation block on the final page
that contains the actual signed date. The standard i_certify and undersigned
statements on earlier pages are pre-printed and often contain blank date fields.

**Approved By:** Compliance Director
