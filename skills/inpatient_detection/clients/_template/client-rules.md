<!-- ============================================================ -->
<!-- Client Rules Template — inpatient_detection              -->
<!-- Parameter: inpatient_detection                           -->
<!--                                                          -->
<!-- HOW TO USE THIS TEMPLATE:                                -->
<!-- 1. Create folder: clients/<YOUR_CLIENT_NAME>/           -->
<!-- 2. Copy this file into that folder as client-rules.md   -->
<!-- 3. Update the header below with your client details     -->
<!-- 4. Add directive blocks using the templates in this file -->
<!-- 5. Delete unused directive type templates before deploy  -->
<!-- 6. Get compliance director approval before deploying    -->
<!--                                                          -->
<!-- GOLDEN RULE:                                             -->
<!-- All directives apply ON TOP of CMS regulations.         -->
<!-- CMS requirements are NEVER waived or reduced.           -->
<!-- You can only raise the bar — never lower it.            -->
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
<!-- IP_INPATIENT_EXCLUSION  — inpatient exclusion rule          -->
<!-- IP_TWO_MIDNIGHT         — inpatient vs. observation rule    -->
<!-- IP_PLACE_OF_RESIDENCE   — inpatient ≠ patient's home        -->
<!-- IP_ACCEPTABLE_LOCATIONS — acceptable F2F encounter locations -->
<!-- IP_SETTING_TYPES        — setting classification criteria   -->
<!-- IP_DIRECT_ADMISSION     — direct admission to HH rule       -->
<!-- IP_F2F_SETTING_2026     — CY2026 setting flexibility rule   -->
<!-- IP_FLAGS                — flag summary                      -->
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
<!-- Step          — which extraction step (1-8)                 -->
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
<!-- CMS requires inpatient detection from any facility signal.  -->
<!-- Your MAC denies claims when admission date is absent even   -->
<!-- if the setting is clearly documented. You ELEVATE to also   -->
<!-- require an explicit admission date for INPATIENT_DETECTED.  -->
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
<What should the agent do — e.g. set inpatient_flag to false, populate missing>

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
<!-- Example: Your facilities use non-standard facility codes    -->
<!-- in OCR output that the CMS signals would miss entirely.     -->
<!-- You EXTEND to map those codes to standard setting types.    -->
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
<!-- Your facilities embed short codes ("ACH", "SNF-A") in OCR  -->
<!-- output rather than full facility names. Standard CMS        -->
<!-- signals miss these — setting_type stays unknown without     -->
<!-- your code mapping. You EXTEND with Affects Status NO so     -->
<!-- the claim still evaluates but the code lookup is applied.  -->
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
<!-- CMS published an illustration or example that creates false  -->
<!-- positives or negatives for your specific patient population  -->
<!-- or document formats. You EXCLUDE the illustration while     -->
<!-- keeping the underlying CMS rule intact.                     -->
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
<!-- IP_SETTING_TYPES has an EXAMPLE of standard observation     -->
<!-- language signals. Your facilities use a proprietary         -->
<!-- shorthand that those signals never match. You EXCLUDE       -->
<!-- the example and add your facility's specific terms via      -->
<!-- an EXTEND directive alongside it.                           -->
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
Note in reasoning.agency_warnings: "<message>"

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
<!-- CMS provides a signal-language example (e.g. standard       -->
<!-- discharge disposition phrases) that does not match your     -->
<!-- agency's OCR output or documentation forms. You REPLACE     -->
<!-- the example with your agency's equivalent phrasing.        -->
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
<!-- IP_DIRECT_ADMISSION lists standard discharge disposition    -->
<!-- phrases like "home with home health services". Your agency  -->
<!-- abbreviates this as "DC w/ HHC" in OCR output. You REPLACE -->
<!-- the example so "DC w/ HHC" is treated as a valid           -->
<!-- direct-to-HH indicator without changing the CMS rule.      -->
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
Note in reasoning.agency_warnings: "<message>"

**Approved By:** <Name, Role>
