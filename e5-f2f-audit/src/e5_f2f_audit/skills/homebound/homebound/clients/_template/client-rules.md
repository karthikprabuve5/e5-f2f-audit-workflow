<!-- ============================================================ -->
<!-- Client Rules Template — homebound_status                     -->
<!-- Parameter: homebound_status                                  -->
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
<!-- HB_TWO_PRONG        — Overall two-prong homebound test      -->
<!-- HB_CRITERIA_ONE     — Prong 1 functional/medical basis      -->
<!-- HB_CRITERIA_TWO     — Prong 2 effort standard               -->
<!-- HB_LANGUAGE_STANDARDS — Acceptable/unacceptable language    -->
<!-- HB_ALLOWABLE_ABSENCES — Absence rules                       -->
<!-- HB_PLACE_OF_RESIDENCE — Residence definition                -->
<!-- HB_SUPPORTING_DOCS  — Clinical documentation standards      -->
<!-- HB_NON_QUALIFYING   — Non-qualifying condition illustration  -->
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
<!-- still results in denials. You are raising the standard to    -->
<!-- reduce claim denial rates.                                   -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- Do not use ELEVATE to add a brand new check that CMS has    -->
<!-- no rule about at all. Use EXTEND for that instead.          -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which extraction/validation step (1-6)      -->
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
<!-- CMS says "considerable effort" language = Prong 2 met.      -->
<!-- Your MAC denies claims where effort language has no device   -->
<!-- or diagnosis specificity. You ELEVATE to require both.       -->
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
<What should the agent do — e.g. set field to false, populate missing>

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
<!-- Example: CMS does not require homebound statement in the    -->
<!-- F2F note specifically — but your MAC reviewers look there   -->
<!-- first. You EXTEND to flag when it is missing from F2F.      -->
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
<!-- CMS allows homebound statement anywhere in medical record.  -->
<!-- Your agency wants it in the F2F note specifically.          -->
<!-- You EXTEND with Affects Status NO — so the claim still      -->
<!-- passes but the clinical team is alerted to strengthen docs. -->
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
<!-- WHAT IT DOES:                                                -->
<!-- Sets aside a specific CMS illustration, example, or         -->
<!-- suggestion that does not apply to your patient population    -->
<!-- or clinical context. The CMS regulation itself still        -->
<!-- applies in full — only the named illustration is excluded.  -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- CMS published an illustration that flags something as        -->
<!-- non-qualifying — but for your specific patient population   -->
<!-- that illustration creates false negatives. You EXCLUDE the  -->
<!-- illustration while keeping the underlying CMS rule.         -->
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
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- CMS illustration: advanced age alone is non-qualifying.     -->
<!-- Your agency serves 90+ patients with MD attestation.        -->
<!-- You EXCLUDE this illustration for your population while     -->
<!-- the two-prong test still applies in full.                   -->
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
<!-- WHAT IT DOES:                                                -->
<!-- Substitutes a specific CMS language example or suggestion    -->
<!-- with your agency's version. The CMS regulation and          -->
<!-- criteria still apply in full. Only the named example is     -->
<!-- replaced with your version.                                 -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- CMS provides a language example (acceptable or              -->
<!-- unacceptable) that does not fit your agency's               -->
<!-- documentation standards or forms. You REPLACE the           -->
<!-- example with your agency's equivalent.                      -->
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
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- CMS says "Patient is homebound" = unacceptable language.   -->
<!-- Your agency uses a standard F2F form with a physician       -->
<!-- attestation checkbox. You REPLACE this example so that      -->
<!-- "Patient is homebound" on your form with checkbox IS        -->
<!-- acceptable. The two-prong test still validates separately.  -->
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
