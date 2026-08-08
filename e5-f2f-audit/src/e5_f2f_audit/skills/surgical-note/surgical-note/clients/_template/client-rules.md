<!-- ============================================================ -->
<!-- Client Rules Template — surgical_note                    -->
<!-- Parameter: surgical_note                                 -->
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
<!-- SN_F2F_CONTENT        — F2F documentation content rules     -->
<!-- SN_NOTE_TYPE          — note type validity criteria         -->
<!-- SN_ANESTHESIA_EXCLUSION — anesthesia notes not valid F2F   -->
<!-- SN_HH_CONTENT         — HH-relevant content standards       -->
<!-- SN_SETTING            — acceptable surgical F2F locations   -->
<!-- SN_FLAGS              — flag summary                        -->
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
<!-- satisfied. If the client condition fails, f2f_adequate       -->
<!-- fails even if the CMS condition alone was met.              -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- Your MAC audit data shows claims denied even when CMS       -->
<!-- minimum is met — e.g., HH content must appear in specific   -->
<!-- sections of the note, not just anywhere in the document.    -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- Do not use ELEVATE to add a brand new check that CMS has    -->
<!-- no rule about at all. Use EXTEND for that instead.          -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which extraction step (1-8)                 -->
<!-- Field         — which output field this affects             -->
<!-- Affects Status — always YES for ELEVATE                     -->
<!-- CMS Condition  — paste the CMS requirement being raised     -->
<!-- Client Condition — your stricter requirement                -->
<!-- If Not Met    — what the agent should do                    -->
<!-- Business Reason — MAC data, denial patterns, policy         -->
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- CMS requires HH-relevant content anywhere in the note.     -->
<!-- Your MAC denies claims when HH content appears only in      -->
<!-- the procedure section. You ELEVATE to require it in         -->
<!-- Plan/Assessment/Discharge sections specifically.            -->
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
<What should the agent do — e.g. set f2f_adequate to false, populate missing>

**Business Reason:**
<Why does this directive exist — MAC audit data, denial patterns, policy>

---

<!-- ============================================================ -->
<!-- TYPE 2: EXTEND                                               -->
<!--                                                              -->
<!-- WHAT IT DOES:                                                -->
<!-- Adds a completely new check that CMS does not require.      -->
<!-- You control whether failure changes the status or just       -->
<!-- generates an agency warning.                                 -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- Your agency uses non-standard surgical documentation forms  -->
<!-- or abbreviations that standard CMS signal phrases miss.     -->
<!-- Example: Client uses "DC orders: HHC" as the HH referral   -->
<!-- indicator rather than the standard CMS phrase patterns.     -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- Do not use EXTEND to make an existing CMS rule stricter.    -->
<!-- Use ELEVATE for that instead.                               -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step          — which step this check runs at               -->
<!-- Field         — which output field this affects             -->
<!-- Affects Status — YES (changes status) or NO (warning only)  -->
<!-- Check         — describe the new check in plain English     -->
<!-- If Not Met    — what the agent should do                    -->
<!-- Business Reason — why this check exists                     -->
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- Your agency's surgeons use a proprietary abbreviation for   -->
<!-- home PT referrals that the standard search misses. You      -->
<!-- EXTEND with Affects Status NO to capture it as HH content  -->
<!-- without changing the overall F2F adequacy status.          -->
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
<!-- suggestion. The CMS regulation applies in full — only the   -->
<!-- named illustration is excluded.                             -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- A CMS illustration creates false negatives for your         -->
<!-- patient population or document format. Example: CMS         -->
<!-- illustrates "procedure steps alone" as insufficient — but   -->
<!-- your surgeons document HH assessment inline with procedure  -->
<!-- steps, making the illustration misleading.                  -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- NEVER use EXCLUDE to target a CMS regulation, requirement,  -->
<!-- or criteria. Only illustrations, examples, and suggestions. -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step, Field, Element Type (ILLUSTRATION/EXAMPLE/SUGGESTION) -->
<!-- Excludes, Client Exception, If Applied, Approved By         -->
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- SN_HH_CONTENT lists "Patient will need home care" as a     -->
<!-- weak/vague signal. Your agency's standard form uses exactly -->
<!-- this phrase alongside a checked HH checkbox. You EXCLUDE    -->
<!-- the weak signal illustration for your form type.           -->
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
<!-- Substitutes a CMS language example or suggestion with your  -->
<!-- agency's version. The CMS regulation applies in full.       -->
<!--                                                              -->
<!-- WHEN TO USE:                                                 -->
<!-- CMS lists specific HH-content signal phrases, but your      -->
<!-- agency's surgeons use different but clinically equivalent   -->
<!-- language. You REPLACE the example so your phrases are       -->
<!-- recognized as strong HH-content signals.                    -->
<!--                                                              -->
<!-- WHEN NOT TO USE:                                             -->
<!-- NEVER use REPLACE to target a CMS regulatory threshold      -->
<!-- or criteria. Only language examples and suggestions.        -->
<!--                                                              -->
<!-- REQUIRED FIELDS:                                             -->
<!-- Step, Field, Element Type (EXAMPLE/ILLUSTRATION/SUGGESTION) -->
<!-- Replaces, Client Version, If Applied, Approved By           -->
<!--                                                              -->
<!-- EXAMPLE USE CASE:                                            -->
<!-- SN_HH_CONTENT lists "Home PT 3x/week" as strong language.  -->
<!-- Your agency uses "HHC Rehab QIW" as the equivalent. You    -->
<!-- REPLACE so "HHC Rehab QIW" is treated as a strong signal.  -->
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
