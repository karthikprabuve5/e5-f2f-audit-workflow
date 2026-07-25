<!-- ============================================================ -->
<!-- Client Rules Template — primary_diagnosis                    -->
<!-- Parameter: primary_diagnosis                                 -->
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
<!-- PD_F2F_DOCUMENTATION  — F2F encounter documentation req.    -->
<!-- PD_SPECIFICITY        — Primary diagnosis specificity std.  -->
<!-- PD_CLINICAL_RELEVANCE — Nexus to primary HH reason          -->
<!-- PD_POC_ALIGNMENT      — Plan of Care alignment requirement  -->
<!-- PD_ICD10_STANDARDS    — ICD-10-CM coding standards          -->
<!-- PD_NON_QUALIFYING     — Non-qualifying diagnosis situations  -->
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
<!-- WHAT IT DOES:                                                -->
<!-- Raises the bar above the CMS minimum for an existing rule.  -->
<!-- Both the CMS condition AND your client condition must be     -->
<!-- satisfied. If the client condition fails, the field fails    -->
<!-- even if the CMS condition alone was met.                     -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- You want stricter documentation than CMS requires because    -->
<!-- your MAC audit data shows that meeting only the CMS minimum  -->
<!-- still results in denials. Example: CMS accepts "CHF" as a   -->
<!-- named condition. Your MAC denies claims where CHF is not     -->
<!-- further specified as systolic or diastolic. You ELEVATE      -->
<!-- the specificity requirement.                                 -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- Do not use ELEVATE to add a brand new check that CMS has    -->
<!-- no rule about at all. Use EXTEND for that instead.          -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which extraction/validation step (1-8)      -->
<!-- Field         — which output field this affects             -->
<!-- Affects Status — always YES for ELEVATE                     -->
<!-- CMS Condition  — paste the exact CMS requirement being      -->
<!--                  raised (from cms-rules.md)                 -->
<!-- Client Condition — your stricter requirement                -->
<!-- If Not Met    — what the agent should do when client        -->
<!--                 condition fails                             -->
<!-- Business Reason — why this directive exists (audit data,    -->
<!--                   MAC patterns, internal policy)            -->
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- CMS accepts a named condition as specific.                  -->
<!-- Your MAC requires the ICD-10 code to be present in the      -->
<!-- F2F note itself (not just the POC) to pass the specificity  -->
<!-- check. You ELEVATE to require an explicit ICD-10 code.       -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | ELEVATE | <ANCHOR>

**Step:** <1-8>
**Field:** <output field name>
**Affects Status:** YES

**CMS Condition:**
<Paste the CMS condition from cms-rules.md that you are raising>

**Client Condition:**
<Describe your stricter requirement — what must ALSO be present>

**If Not Met:**
<What should the agent do — e.g. set specificity_met to false, populate missing>

**Business Reason:**
<Why does this directive exist — MAC audit data, denial patterns, policy>

---

<!-- ============================================================ -->
<!-- TYPE 2: EXTEND                                               -->
<!--                                                              -->
<!-- WHAT IT DOES:                                                -->
<!-- Adds a completely new check that CMS does not require.      -->
<!-- This is your internal quality standard beyond CMS.          -->
<!-- You control whether failure changes the status or just       -->
<!-- generates an agency warning.                                 -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- You want to catch a documentation gap that CMS does not     -->
<!-- require but your agency knows leads to audit questions.      -->
<!-- Example: CMS does not require the diagnosis to appear in     -->
<!-- a specific field on the F2F form. Your agency's standard     -->
<!-- form has a "Primary Diagnosis" field — you EXTEND to flag   -->
<!-- when the diagnosis is written in narrative only and not      -->
<!-- entered in the designated field.                             -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- Do not use EXTEND to make an existing CMS rule stricter.    -->
<!-- Use ELEVATE for that instead.                               -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which step this check runs at               -->
<!-- Field         — which output field this affects             -->
<!-- Affects Status — YES (failure changes status) or            -->
<!--                  NO (failure adds agency warning only)      -->
<!-- Check         — describe the new check in plain English     -->
<!-- If Not Met    — what the agent should do when check fails   -->
<!-- Business Reason — why this check exists                     -->
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- Your agency requires ICD-10 codes on the F2F note itself   -->
<!-- for cleaner claim submission. CMS does not require this.    -->
<!-- You EXTEND with Affects Status NO so the claim passes but   -->
<!-- the clinical team is alerted to add codes before billing.   -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXTEND | <ANCHOR>

**Step:** <1-8>
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
<!-- WHAT IT DOES:                                                -->
<!-- Sets aside a specific CMS illustration, example, or         -->
<!-- suggestion that does not apply to your patient population    -->
<!-- or clinical context. The CMS regulation itself still        -->
<!-- applies in full — only the named illustration is excluded.  -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- CMS illustration flags something as non-qualifying — but    -->
<!-- for your specific patient population, that illustration     -->
<!-- creates false negatives. Example: CMS illustrates           -->
<!-- "weakness alone" as non-qualifying. Your agency serves a    -->
<!-- documented ALS population where weakness IS the diagnosis.  -->
<!-- You EXCLUDE the illustration for ALS patients while the     -->
<!-- specificity requirement still applies in full.              -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- NEVER use EXCLUDE to target a CMS regulation, requirement,  -->
<!-- or criteria. Only illustrations, examples, and suggestions  -->
<!-- can be excluded. If the Element Type field would need to     -->
<!-- say REGULATION — stop and do not create this directive.     -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which step this applies at                  -->
<!-- Field         — which output field this affects             -->
<!-- Element Type  — MUST be ILLUSTRATION, EXAMPLE, or           -->
<!--                 SUGGESTION — never REGULATION               -->
<!-- Excludes      — describe exactly what CMS illustration      -->
<!--                 is being excluded                           -->
<!-- Client Exception — what your agency accepts instead         -->
<!-- If Applied    — what the agent should note when applied     -->
<!-- Approved By   — compliance director name and role           -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXCLUDE | <ANCHOR>

**Step:** <1-8>
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
<!-- WHAT IT DOES:                                                -->
<!-- Substitutes a specific CMS language example or suggestion    -->
<!-- with your agency's version. The CMS regulation and          -->
<!-- criteria still apply in full. Only the named example is     -->
<!-- replaced with your version.                                 -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- CMS provides a language example that does not fit your      -->
<!-- agency's documentation standards or forms. Example: CMS     -->
<!-- illustrates that a condition written as a single            -->
<!-- abbreviation (e.g., "DM") is non-qualifying. Your agency's  -->
<!-- standard F2F form uses "DM2" (which expands to Type 2 DM    -->
<!-- in your form legend). You REPLACE the CMS abbreviation      -->
<!-- example with your form-specific standard.                   -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- NEVER use REPLACE to target a CMS regulatory threshold      -->
<!-- or criteria. Only language examples and suggestions can     -->
<!-- be replaced. The underlying CMS rule always stays.          -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which step this applies at                  -->
<!-- Field         — which output field this affects             -->
<!-- Element Type  — MUST be EXAMPLE, ILLUSTRATION, or           -->
<!--                 SUGGESTION — never REGULATION               -->
<!-- Replaces      — describe exactly which CMS language         -->
<!--                 example is being replaced                   -->
<!-- Client Version — your agency's replacement language         -->
<!-- If Applied    — what the agent should note when applied     -->
<!-- Approved By   — compliance director name and role           -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | REPLACE | <ANCHOR>

**Step:** <1-8>
**Field:** <output field name>
**Element Type:** <EXAMPLE | ILLUSTRATION | SUGGESTION>

**Replaces:**
<Describe exactly which CMS language example is being replaced>

**Client Version:**
<Describe your agency's replacement language or standard>

**If Applied:**
<What should the agent note in agency_warnings when this is applied>

**Approved By:** <Name, Role>
