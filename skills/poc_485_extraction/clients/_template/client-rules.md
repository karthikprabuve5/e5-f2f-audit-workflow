<!-- ============================================================ -->
<!-- Client Rules Template — poc_485_extraction                -->
<!-- Parameter: poc_485_extraction                             -->
<!--                                                           -->
<!-- HOW TO USE THIS TEMPLATE:                                 -->
<!-- 1. Create folder: clients/<YOUR_CLIENT_NAME>/            -->
<!-- 2. Copy this file into that folder as client-rules.md    -->
<!-- 3. Update the header below with your client details      -->
<!-- 4. Add directive blocks using the templates in this file -->
<!-- 5. Delete unused directive type templates before deploy  -->
<!-- 6. Get compliance director approval before deploying     -->
<!--                                                           -->
<!-- GOLDEN RULE:                                              -->
<!-- All directives apply ON TOP of CMS regulations.          -->
<!-- CMS requirements are NEVER waived or reduced.            -->
<!-- You can only raise the bar — never lower it.             -->
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
<!--                                                             -->
<!-- POC_PRIMARY_DX       — primary diagnosis label and format   -->
<!-- POC_SKILLED_SERVICES — skilled services section label       -->
<!-- POC_HOMEBOUND        — homebound eligibility section label  -->
<!-- POC_F2F_DATE         — F2F certification statement pattern  -->
<!-- POC_CERTIFICATION    — physician signature label            -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- DIRECTIVE TYPE GUIDE                                         -->
<!--                                                             -->
<!-- Four types are available. Read each explanation carefully   -->
<!-- before choosing which type fits your need.                  -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- TYPE 1: ELEVATE                                             -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Raises the bar above the CMS minimum for an existing rule. -->
<!-- Both the CMS condition AND your client condition must be    -->
<!-- satisfied. If the client condition fails, extraction is     -->
<!-- flagged even if the CMS condition alone was met.            -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- You want stricter extraction than the default standard      -->
<!-- because your MAC audit data shows the default approach      -->
<!-- still misses client-specific documentation patterns.        -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- Do not use ELEVATE to add a brand new extraction target     -->
<!-- that CMS has no rule about at all. Use EXTEND for that.    -->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step           — which extraction step (1-7)               -->
<!-- Field          — which output field this affects           -->
<!-- Affects Status — always YES for ELEVATE                    -->
<!-- CMS Condition  — paste the CMS extraction rule being       -->
<!--                  raised (from field-map.md)                -->
<!-- Client Condition — your stricter extraction requirement    -->
<!-- If Not Met     — what the agent should do when fails       -->
<!-- Business Reason — why this directive exists                -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- CMS-485 Order=1 row identifies primary diagnosis.          -->
<!-- Your client labels it "Primary" not "1". You ELEVATE       -->
<!-- extraction to also check the "Primary" label column.       -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | ELEVATE | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Affects Status:** YES

**CMS Condition:**
<Paste the default extraction rule from field-map.md that you are raising>

**Client Condition:**
<Describe your stricter or additional extraction requirement>

**If Not Met:**
<What should the agent do — e.g. set not_found, add flag>

**Business Reason:**
<Why does this directive exist — client format, EHR vendor, known quirks>

---

<!-- ============================================================ -->
<!-- TYPE 2: EXTEND                                              -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Adds a completely new extraction target that the default    -->
<!-- field-map does not cover. This handles client-specific     -->
<!-- section labels, alternative field names, or custom         -->
<!-- certification statement patterns.                          -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- Your client's 485 uses a non-standard section label or     -->
<!-- a third certification statement beyond i_certify and       -->
<!-- undersigned. You EXTEND to add the new target.             -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- Do not use EXTEND to make an existing extraction rule      -->
<!-- stricter. Use ELEVATE for that instead.                    -->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step          — which step this check runs at              -->
<!-- Field         — which output field this affects            -->
<!-- Affects Status — YES (failure changes status) or           -->
<!--                  NO (failure adds agency warning only)     -->
<!-- Check         — describe the new extraction target         -->
<!-- If Not Met    — what the agent should do when not found    -->
<!-- Business Reason — why this check exists                    -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- Your client has a third certification statement starting   -->
<!-- with "THE PROVIDER ATTESTS TO THE FACE-TO-FACE ENCOUNTER  -->
<!-- ON". You EXTEND to extract this as a custom f2f_date.      -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXTEND | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Affects Status:** <YES | NO>

**Check:**
<Describe the new extraction target in plain English>

**If Not Met:**
<What should the agent do — set not_found or add agency warning>

**Business Reason:**
<Why does this check exist — client format, EHR vendor, known quirks>

---

<!-- ============================================================ -->
<!-- TYPE 3: EXCLUDE                                             -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Sets aside a specific default extraction illustration or    -->
<!-- example that does not apply to this client's documents.    -->
<!-- The extraction rule itself still applies — only the named  -->
<!-- example label or format is excluded.                       -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- The default field-map lists a label or format that causes  -->
<!-- false matches on this client's 485. You EXCLUDE the        -->
<!-- specific example while keeping the extraction rule.        -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- NEVER use EXCLUDE to bypass a CMS extraction requirement.  -->
<!-- Only label examples and format suggestions can be excluded.-->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step          — which step this applies at                 -->
<!-- Field         — which output field this affects            -->
<!-- Element Type  — MUST be ILLUSTRATION, EXAMPLE, or          -->
<!--                 SUGGESTION — never REGULATION              -->
<!-- Excludes      — describe exactly which label/format        -->
<!--                 example is being excluded                  -->
<!-- Client Exception — what label/format your client uses      -->
<!-- If Applied    — what the agent should note when applied    -->
<!-- Approved By   — compliance director name and role          -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- field-map default: "Frequency/Duration of Visits:" label.  -->
<!-- Your client's 485 does not use this label at all — it      -->
<!-- uses "Visit Orders". You EXCLUDE the default label and     -->
<!-- use REPLACE to substitute your client's label.             -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXCLUDE | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Element Type:** <ILLUSTRATION | EXAMPLE | SUGGESTION>

**Excludes:**
<Describe exactly which default label or format example is excluded>

**Client Exception:**
<Describe what your client's 485 uses instead>

**If Applied:**
<What should the agent note in agency_warnings when this is applied>

**Approved By:** <Name, Role>

---

<!-- ============================================================ -->
<!-- TYPE 4: REPLACE                                             -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Substitutes a specific default label, trigger, or format   -->
<!-- example with your client's version. The CMS extraction     -->
<!-- logic still applies — only the named label is replaced.    -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- Your client's 485 uses a different section label, column   -->
<!-- header, or certification statement trigger than the default.-->
<!-- You REPLACE the default label with your client's label.    -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- NEVER use REPLACE to bypass a CMS extraction requirement.  -->
<!-- Only label examples and format suggestions can be replaced.-->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step          — which step this applies at                 -->
<!-- Field         — which output field this affects            -->
<!-- Element Type  — MUST be EXAMPLE, ILLUSTRATION, or          -->
<!--                 SUGGESTION — never REGULATION              -->
<!-- Replaces      — describe exactly which default label       -->
<!--                 or format is being replaced                -->
<!-- Client Version — your client's label or format             -->
<!-- If Applied    — what the agent should note when applied    -->
<!-- Approved By   — compliance director name and role          -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- Default trigger for skilled services:                      -->
<!-- "Frequency/Duration of Visits:".                           -->
<!-- Your client uses "Visit Frequency Schedule:".              -->
<!-- You REPLACE so the agent searches for the correct label.   -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | REPLACE | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Element Type:** <EXAMPLE | ILLUSTRATION | SUGGESTION>

**Replaces:**
<Describe exactly which default label or format is being replaced>

**Client Version:**
<Describe your client's label or format>

**If Applied:**
<What should the agent note in agency_warnings when this is applied>

**Approved By:** <Name, Role>
