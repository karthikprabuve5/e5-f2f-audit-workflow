<!-- ============================================================ -->
<!-- Client Rules Template — encounter_selection                  -->
<!-- Parameter: encounter_selection                               -->
<!--                                                              -->
<!-- HOW TO USE THIS TEMPLATE:                                    -->
<!-- 1. Create folder: clients/<YOUR_CLIENT_NAME>/                -->
<!-- 2. Copy this file into that folder as client-rules.md        -->
<!-- 3. Update the header below with your client details          -->
<!-- 4. Add directive blocks using the templates in this file     -->
<!-- 5. Delete unused directive type templates before deploying   -->
<!-- 6. Get compliance director approval before deploying         -->
<!--                                                              -->
<!-- GOLDEN RULE:                                                 -->
<!-- All directives apply ON TOP of CMS selection rules.          -->
<!-- CMS gates (timing, allowed practitioner, relatedness) are    -->
<!-- NEVER waived or lowered. You can only raise the bar.         -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- Client: <YOUR_CLIENT_NAME>                                   -->
<!-- Effective: YYYY-MM-DD                                        -->
<!-- Approved By: <Name, Role>                                    -->
<!-- Version: 1.0                                                 -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- AVAILABLE ANCHORS                                            -->
<!-- Use these exact values in the ANCHOR position of your        -->
<!-- directive header: ## DIRECTIVE ID | TYPE | ANCHOR            -->
<!--                                                              -->
<!-- SEL_TIMING_WINDOW           — 90/30-day timing window        -->
<!-- SEL_ALLOWED_PRACTITIONER    — CY2026 allowed-provider gate   -->
<!-- SEL_SUBSTANTIATING_NOTE     — signed clinical note required  -->
<!-- SEL_CERTIFIED_ENCOUNTER_IDENTITY — certified-date identity   -->
<!-- SEL_WATERFALL               — clinical-relevance priority     -->
<!-- SEL_DATE_RECONCILIATION     — date-match reconciliation      -->
<!-- SEL_TIEBREAKERS             — tie-breaker chain              -->
<!-- SEL_DECISION_STATES         — decision states/escalation     -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- DIRECTIVE TYPE GUIDE                                         -->
<!--                                                              -->
<!-- ELEVATE — raise the bar on an existing CMS selection rule.   -->
<!--   Both CMS and client conditions must hold. Affects Outcome. -->
<!-- EXTEND  — add a new selection check CMS does not require.     -->
<!--   Affects Outcome YES (changes the pick) or NO (warning).    -->
<!-- EXCLUDE — set aside a CMS ILLUSTRATION/EXAMPLE/SUGGESTION.    -->
<!--   Never a REGULATION/REQUIREMENT/CRITERIA.                   -->
<!-- REPLACE — substitute a CMS EXAMPLE/ILLUSTRATION/SUGGESTION.  -->
<!--   Never a REGULATION/REQUIREMENT/CRITERIA.                   -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | ELEVATE | <ANCHOR>

**Step:** <4-6>
**Field:** <output field name>
**Affects Outcome:** YES

**CMS Condition:**
<Paste the CMS selection condition from cms-selection-rules.md that you are raising>

**Client Condition:**
<Describe your stricter requirement — what must ALSO hold for an encounter to win>

**If Not Met:**
<What should the agent do — e.g. down-rank the encounter, force NEEDS_HUMAN_REVIEW>

**Business Reason:**
<Why this directive exists — MAC audit data, denial patterns, internal policy>

---

## DIRECTIVE <ID> | EXTEND | <ANCHOR>

**Step:** <4-6>
**Field:** <output field name>
**Affects Outcome:** <YES | NO>

**Check:**
<Describe the new selection check in plain English>

**If Not Met:**
<Add to agency_warnings, or change the pick / force review>

**Business Reason:**
<Why this check exists>

---

## DIRECTIVE <ID> | EXCLUDE | <ANCHOR>

**Step:** <4-6>
**Field:** <output field name>
**Element Type:** <ILLUSTRATION | EXAMPLE | SUGGESTION>

**Excludes:**
<Describe exactly which CMS illustration or example is excluded>

**Client Exception:**
<Describe what your agency accepts in place of this illustration>

**If Applied:**
<What the agent should note in agency_warnings when applied>

**Approved By:** <Name, Role>

---

## DIRECTIVE <ID> | REPLACE | <ANCHOR>

**Step:** <4-6>
**Field:** <output field name>
**Element Type:** <EXAMPLE | ILLUSTRATION | SUGGESTION>

**Replaces:**
<Describe exactly which CMS language example is being replaced>

**Client Version:**
<Describe your agency's replacement language or standard>

**If Applied:**
<What the agent should note in agency_warnings when applied>

**Approved By:** <Name, Role>
