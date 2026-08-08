<!-- ============================================================ -->
<!-- Client Rules — inpatient_detection                          -->
<!-- Client: CLIENT_A                                            -->
<!-- Effective: 2026-01-01                                       -->
<!-- Approved By: Compliance Director                            -->
<!-- Version: 1.0                                                -->
<!--                                                             -->
<!-- All directives apply ON TOP of CMS regulations.            -->
<!-- CMS requirements are never waived or reduced.              -->
<!-- EXCLUDE and REPLACE apply only to element_type:            -->
<!-- ILLUSTRATION / EXAMPLE / SUGGESTION                        -->
<!-- Never target REGULATION / REQUIREMENT / CRITERIA           -->
<!-- ============================================================ -->

## DIRECTIVE IP-001 | EXTEND | IP_SETTING_TYPES

**Step:** 3
**Field:** setting_type
**Affects Status:** NO

**Check:**
When setting_type is `unknown`, additionally search for CLIENT_A-specific
facility codes in the document header: "ACH", "SNF-A", "ALF-A".
Map "ACH" → `hospital`; "SNF-A" → `snf`; "ALF-A" → `outpatient_clinic`.

**If Not Met:**
Add to reasoning.agency_warnings: "CLIENT_A facility code not found — setting remains unknown."

**Business Reason:**
CLIENT_A facilities embed short codes in OCR output rather than full
facility names; code mapping prevents false UNABLE_TO_DETERMINE outcomes.

---

## DIRECTIVE IP-002 | EXTEND | IP_DIRECT_ADMISSION

**Step:** 6
**Field:** discharge_disposition.direct_to_hh
**Affects Status:** NO

**Check:**
In addition to standard HH disposition language, treat CLIENT_A discharge
phrase "DC w/ HHC" as a direct-to-HH indicator.

**If Not Met:**
Add to reasoning.agency_warnings: "CLIENT_A shorthand not found — standard HH disposition search applied."

**Business Reason:**
CLIENT_A uses abbreviated discharge language in OCR output;
standard search alone misses this common phrase.
