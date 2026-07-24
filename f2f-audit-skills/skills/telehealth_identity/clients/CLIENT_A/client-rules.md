<!-- ============================================================ -->
<!-- Client Rules — telehealth_identity                        -->
<!-- Client: CLIENT_A                                          -->
<!-- Effective: 2026-01-01                                     -->
<!-- Approved By: Compliance Director                          -->
<!-- Version: 1.0                                              -->
<!--                                                            -->
<!-- All directives apply ON TOP of CMS regulations.          -->
<!-- CMS requirements are never waived or reduced.            -->
<!-- EXCLUDE and REPLACE apply only to element_type:          -->
<!-- ILLUSTRATION / EXAMPLE / SUGGESTION                      -->
<!-- Never target REGULATION / REQUIREMENT / CRITERIA         -->
<!-- ============================================================ -->

## DIRECTIVE TH-001 | EXTEND | TH_MODALITY

**Step:** 3
**Field:** telehealth_indicator
**Affects Status:** NO

**Check:**
In addition to standard telehealth keywords, CLIENT_A uses "VVC" and
"Virtual Health Visit" as platform-specific telehealth identifiers.
Treat these as confirming telehealth indicators equivalent to "Telehealth"
or "Video Visit".

**If Not Met:**
No action — this directive only adds keywords. If none of the standard
or CLIENT_A keywords are found, `not_found = true` applies as normal.

**Business Reason:**
CLIENT_A uses VA Video Connect (VVC) as its telehealth platform.
Standard keyword matching misses VVC sessions, causing false negatives
in telehealth classification.

---

## DIRECTIVE TH-002 | REPLACE | TH_MODALITY

**Step:** 4
**Field:** platform
**Element Type:** EXAMPLE

**Replaces:**
Default platform extraction (extract platform name as documented).

**Client Version:**
CLIENT_A exclusively uses VA Video Connect (VVC). If any of the following
aliases are present, set `platform.name = "VA Video Connect"`:
"VVC", "VA Video", "Virtual Connect", "VA Video Connect".

**If Applied:**
Note in extraction: "Platform normalized to VA Video Connect per TH-002."

**Approved By:** Compliance Director

---

## DIRECTIVE TH-003 | EXTEND | TH_CONSENT

**Step:** 6
**Field:** consent
**Affects Status:** NO

**Check:**
In addition to standard consent phrases, CLIENT_A documents consent using:
- "Patient verbally agreed to virtual visit"
- "Telehealth agreement on file"
Treat these as valid consent documentation.

**If Not Met:**
No action — this directive only extends consent phrase recognition.
Standard `no_consent` flag applies if no consent language found.

**Business Reason:**
CLIENT_A's EHR system auto-populates these non-standard consent phrases.
Without this directive, valid consent documentation is missed.
