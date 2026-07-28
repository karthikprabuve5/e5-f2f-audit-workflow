<!-- ============================================================ -->
<!-- Client Rules Template — skilled_services                    -->
<!-- Parameter: skilled_services                                 -->
<!--                                                              -->
<!-- HOW TO USE THIS TEMPLATE:                                    -->
<!-- 1. Create folder: clients/<YOUR_CLIENT_NAME>/               -->
<!-- 2. Copy this file into that folder as client-rules.md       -->
<!-- 3. Update the header below with your client details         -->
<!-- 4. Add directive blocks using the templates in this file    -->
<!-- 5. Delete unused directive type templates before deploying  -->
<!-- 6. Get compliance director approval before deploying        -->
<!--                                                              -->
<!-- GOLDEN RULE:                                                 -->
<!-- All directives apply ON TOP of CMS regulations.             -->
<!-- CMS requirements are NEVER waived or reduced.               -->
<!-- You can only raise the bar — never lower it.                -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- Client: <YOUR_CLIENT_NAME>                                   -->
<!-- Effective: YYYY-MM-DD                                        -->
<!-- Approved By: <Name, Role>                                    -->
<!-- Version: 1.0                                                 -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- AVAILABLE ANCHORS                                            -->
<!-- Use these exact values in the ANCHOR position of your       -->
<!-- directive header: ## DIRECTIVE ID | TYPE | ANCHOR           -->
<!--                                                              -->
<!-- SS_QUALIFYING_SERVICES    — Which services qualify; OT/MSS/ -->
<!--                             HHA non-initiating rules        -->
<!-- SS_SKILLED_NECESSITY      — Professional skill requirement;  -->
<!--                             custodial vs skilled line        -->
<!-- SS_OBSERVATION_ASSESSMENT — O&A instability requirement      -->
<!-- SS_INTERMITTENT_BASIS     — SN intermittent; venipuncture    -->
<!--                             only rule                       -->
<!-- SS_CLINICAL_NEXUS         — Diagnosis link; necessity vs     -->
<!--                             beneficial; rehab potential;     -->
<!--                             MSS short-term rule             -->
<!-- SS_MAINTENANCE_THERAPY    — Maintenance PT/OT/SLP therapist  -->
<!--                             skill requirement               -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- DIRECTIVE TYPE GUIDE                                         -->
<!--                                                              -->
<!-- Four types are available. Read each explanation carefully    -->
<!-- before choosing which type fits your need.                   -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- TYPE 1: ELEVATE                                              -->
<!--                                                              -->
<!-- Raises the bar above the CMS minimum for an existing rule.  -->
<!-- Both the CMS condition AND your client condition must be     -->
<!-- satisfied. If the client condition fails, the field fails    -->
<!-- even if the CMS condition alone was met.                     -->
<!--                                                              -->
<!-- Example: CMS accepts "SN ordered for wound care" without    -->
<!-- specifying wound type. Your MAC requires the wound type      -->
<!-- (surgical, pressure, diabetic) to be explicitly named.      -->
<!-- You ELEVATE to require wound type documentation.            -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | ELEVATE | <ANCHOR>

**Step:** <1-6>
**Field:** <output field name>
**Affects Status:** YES

**CMS Condition:**
<Paste the CMS condition from cms-rules.md that you are raising>

**Client Condition:**
<Describe your stricter requirement — what must ALSO be present>

**If Not Met:**
<What should the agent do — e.g. set is_justified to false, populate missing>

**Business Reason:**
<Why does this directive exist — MAC audit data, denial patterns, policy>

---

<!-- ============================================================ -->
<!-- TYPE 2: EXTEND                                              -->
<!--                                                              -->
<!-- Adds a completely new check that CMS does not require.      -->
<!-- This is your internal quality standard beyond CMS.          -->
<!-- You control whether failure changes the status or just       -->
<!-- generates an agency warning.                                 -->
<!--                                                              -->
<!-- Example: CMS does not require a specific therapy evaluation  -->
<!-- form. Your agency requires PT evaluations to reference the  -->
<!-- LSVT or Berg Balance Score. You EXTEND to flag when these   -->
<!-- outcome measures are absent from the F2F justification.     -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXTEND | <ANCHOR>

**Step:** <1-6>
**Field:** <output field name>
**Affects Status:** <YES | NO>

**Check:**
<Describe the new check in plain English>

**If Not Met:**
<What should the agent do — add to agency_warnings or change status>

**Business Reason:**
<Why does this check exist>

---

<!-- ============================================================ -->
<!-- TYPE 3: EXCLUDE                                              -->
<!--                                                              -->
<!-- Sets aside a specific CMS illustration, example, or         -->
<!-- suggestion that does not apply to your patient population.  -->
<!-- The CMS regulation itself still applies in full.            -->
<!--                                                              -->
<!-- Example: CMS illustrates that "oral medication management"  -->
<!-- is not skilled. Your agency serves a complex polypharmacy   -->
<!-- population where high-risk oral medication reconciliation   -->
<!-- is performed by RN with clinical judgment. You EXCLUDE the  -->
<!-- oral medication illustration for these patients.            -->
<!--                                                              -->
<!-- NEVER target a CMS regulation — only illustrations,         -->
<!-- examples, or suggestions.                                   -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXCLUDE | <ANCHOR>

**Step:** <1-6>
**Field:** <output field name>
**Element Type:** <ILLUSTRATION | EXAMPLE | SUGGESTION>

**Excludes:**
<Describe exactly which CMS illustration or example is excluded>

**Client Exception:**
<Describe what your agency accepts in place of this illustration>

**If Applied:**
<What should the agent note in agency_warnings when this is applied>

**Approved By:** <Name, Role>

---

<!-- ============================================================ -->
<!-- TYPE 4: REPLACE                                              -->
<!--                                                              -->
<!-- Substitutes a specific CMS language example or suggestion   -->
<!-- with your agency's version. The CMS regulation and          -->
<!-- criteria still apply in full.                               -->
<!--                                                              -->
<!-- Example: CMS illustrates "would benefit from PT" as WEAK.  -->
<!-- Your agency's standard F2F form uses "PT indicated per      -->
<!-- clinical assessment" which your MAC accepts as STRONG.      -->
<!-- You REPLACE the CMS language mapping for this phrase.       -->
<!--                                                              -->
<!-- NEVER target a CMS regulatory threshold or criteria.        -->
<!-- Only language examples and suggestions can be replaced.     -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | REPLACE | <ANCHOR>

**Step:** <1-6>
**Field:** <output field name>
**Element Type:** <EXAMPLE | ILLUSTRATION | SUGGESTION>

**Replaces:**
<Describe exactly which CMS language example is being replaced>

**Client Version:**
<Describe your agency's replacement language or standard>

**If Applied:**
<What should the agent note in agency_warnings when this is applied>

**Approved By:** <Name, Role>
