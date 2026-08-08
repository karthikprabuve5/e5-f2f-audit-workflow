<!-- ============================================================ -->
<!-- Client Rules Template — telehealth_identity               -->
<!-- Parameter: telehealth_identity                            -->
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
<!-- TH_MODALITY       — telehealth modality detection rules     -->
<!-- TH_AUDIO_ONLY     — audio-only restriction rules            -->
<!-- TH_LOCATION       — patient and provider location rules     -->
<!-- TH_CONSENT        — telehealth consent documentation rules  -->
<!-- TH_SYNCHRONOUS    — synchronous confirmation rules          -->
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
<!-- satisfied. If the client condition fails, the field fails   -->
<!-- even if the CMS condition alone was met.                    -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- You want stricter documentation than CMS requires because   -->
<!-- your MAC audit data shows that meeting only the CMS minimum -->
<!-- still results in denials. You are raising the standard to   -->
<!-- reduce claim denial rates.                                  -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- Do not use ELEVATE to add a brand new check that CMS has   -->
<!-- no rule about at all. Use EXTEND for that instead.         -->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step           — which extraction step (1-7)               -->
<!-- Field          — which output field this affects           -->
<!-- Affects Status — always YES for ELEVATE                    -->
<!-- CMS Condition  — paste the exact CMS requirement being     -->
<!--                  raised (from telehealth-rules.md)         -->
<!-- Client Condition — your stricter requirement               -->
<!-- If Not Met     — what the agent should do when client      -->
<!--                  condition fails                           -->
<!-- Business Reason — why this directive exists (audit data,   -->
<!--                   MAC patterns, internal policy)           -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- CMS requires real-time communication for telehealth F2F.   -->
<!-- Your MAC denies claims where the note does not explicitly   -->
<!-- state "audio and video connection". You ELEVATE to require  -->
<!-- that exact phrase, not just any telehealth keyword.         -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | ELEVATE | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Affects Status:** YES

**CMS Condition:**
<Paste the CMS condition from telehealth-rules.md that you are raising>

**Client Condition:**
<Describe your stricter requirement — what must ALSO be present>

**If Not Met:**
<What should the agent do — e.g. set flag to true, populate missing>

**Business Reason:**
<Why does this directive exist — MAC audit data, denial patterns, policy>

---

<!-- ============================================================ -->
<!-- TYPE 2: EXTEND                                              -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Adds a completely new check that CMS does not require.     -->
<!-- This is your internal quality standard beyond CMS.         -->
<!-- You control whether failure changes the status or just      -->
<!-- generates an agency warning.                               -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- You want to catch a documentation gap that CMS does not    -->
<!-- require but your agency knows leads to audit questions.     -->
<!-- Example: CMS does not require a specific telehealth        -->
<!-- platform name in the note — but your agency requires it    -->
<!-- for internal billing verification. You EXTEND to flag      -->
<!-- when the platform name is absent.                          -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- Do not use EXTEND to make an existing CMS rule stricter.   -->
<!-- Use ELEVATE for that instead.                              -->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step          — which step this check runs at              -->
<!-- Field         — which output field this affects            -->
<!-- Affects Status — YES (failure changes status) or           -->
<!--                  NO (failure adds agency warning only)     -->
<!-- Check         — describe the new check in plain English    -->
<!-- If Not Met    — what the agent should do when check fails  -->
<!-- Business Reason — why this check exists                    -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- CMS does not require telehealth consent to be documented   -->
<!-- in the F2F note. Your agency policy requires it.           -->
<!-- You EXTEND with Affects Status NO so the claim passes but  -->
<!-- the clinical team is alerted to add consent documentation. -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXTEND | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Affects Status:** <YES | NO>

**Check:**
<Describe the new check in plain English>

**If Not Met:**
<What should the agent do — add to agency_warnings or set flag>

**Business Reason:**
<Why does this check exist>

---

<!-- ============================================================ -->
<!-- TYPE 3: EXCLUDE                                             -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Sets aside a specific CMS illustration, example, or        -->
<!-- suggestion that does not apply to your patient population   -->
<!-- or clinical context. The CMS regulation itself still       -->
<!-- applies in full — only the named illustration is excluded. -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- CMS published an illustration that flags something as       -->
<!-- non-qualifying — but for your specific patient population  -->
<!-- that illustration creates false negatives. You EXCLUDE the -->
<!-- illustration while keeping the underlying CMS rule.        -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- NEVER use EXCLUDE to target a CMS regulation, requirement, -->
<!-- or criteria. Only illustrations, examples, and suggestions -->
<!-- can be excluded. If the Element Type field would need to    -->
<!-- say REGULATION — stop and do not create this directive.    -->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step          — which step this applies at                 -->
<!-- Field         — which output field this affects            -->
<!-- Element Type  — MUST be ILLUSTRATION, EXAMPLE, or          -->
<!--                 SUGGESTION — never REGULATION              -->
<!-- Excludes      — describe exactly what CMS illustration     -->
<!--                 is being excluded                          -->
<!-- Client Exception — what your agency accepts instead        -->
<!-- If Applied    — what the agent should note when applied    -->
<!-- Approved By   — compliance director name and role          -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- CMS illustration: telephone call alone is non-qualifying.  -->
<!-- Your agency serves a rural population with no broadband    -->
<!-- and has documented inability to use video. You EXCLUDE     -->
<!-- the illustration for documented audio-only cases while     -->
<!-- the synchronous requirement still applies in full.         -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | EXCLUDE | <ANCHOR>

**Step:** <1-7>
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
<!-- TYPE 4: REPLACE                                             -->
<!--                                                             -->
<!-- WHAT IT DOES:                                               -->
<!-- Substitutes a specific CMS language example or suggestion   -->
<!-- with your agency's version. The CMS regulation and         -->
<!-- criteria still apply in full. Only the named example is    -->
<!-- replaced with your version.                                -->
<!--                                                             -->
<!-- WHEN TO USE:                                                -->
<!-- CMS provides a language example that does not fit your     -->
<!-- agency's documentation standards or EHR templates.         -->
<!-- Example: CMS says "telehealth" as the keyword — your       -->
<!-- EHR prints "VVC Session". You REPLACE so that "VVC         -->
<!-- Session" is treated as a valid telehealth indicator.       -->
<!--                                                             -->
<!-- WHEN NOT TO USE:                                            -->
<!-- NEVER use REPLACE to target a CMS regulatory threshold     -->
<!-- or criteria. Only language examples and suggestions can    -->
<!-- be replaced. The underlying CMS rule always stays.         -->
<!--                                                             -->
<!-- REQUIRED FIELDS:                                            -->
<!-- Step          — which step this applies at                 -->
<!-- Field         — which output field this affects            -->
<!-- Element Type  — MUST be EXAMPLE, ILLUSTRATION, or          -->
<!--                 SUGGESTION — never REGULATION              -->
<!-- Replaces      — describe exactly which CMS language        -->
<!--                 example is being replaced                  -->
<!-- Client Version — your agency's replacement language        -->
<!-- If Applied    — what the agent should note when applied    -->
<!-- Approved By   — compliance director name and role          -->
<!--                                                             -->
<!-- EXAMPLE USE CASE:                                           -->
<!-- CMS keyword list includes "Telehealth" and "Video Visit".  -->
<!-- Your agency EHR uses "VA Video Connect" or "VVC".          -->
<!-- You REPLACE the keyword example so your system's phrase    -->
<!-- is accepted as a valid telehealth indicator.               -->
<!-- ============================================================ -->

## DIRECTIVE <ID> | REPLACE | <ANCHOR>

**Step:** <1-7>
**Field:** <output field name>
**Element Type:** <EXAMPLE | ILLUSTRATION | SUGGESTION>

**Replaces:**
<Describe exactly which CMS language example is being replaced>

**Client Version:**
<Describe your agency's replacement language or standard>

**If Applied:**
<What should the agent note in agency_warnings when this is applied>

**Approved By:** <Name, Role>
