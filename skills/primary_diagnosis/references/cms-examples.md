# Primary Diagnosis — CMS Examples
# MBPM Pub. 100-02, Chapter 7, §30.5.1.2
# Use in Step 4 to calibrate specificity and relevance judgments.

---

## Qualifying Examples
<!-- cms_section_id: PD_QUALIFYING_EXAMPLES -->
<!-- element_type: ILLUSTRATION -->

**Cardiac — CHF**
F2F: "Acute on chronic systolic congestive heart failure."
485: I50.31
→ Specificity: SPECIFIC | Relevance: MET | Alignment: ALIGNED
→ Named condition with type and acuity; maps directly to 485 code.

**Diabetic Wound**
F2F: "Non-healing plantar ulcer of right foot, type 2 diabetes with peripheral neuropathy."
485: E11.621
→ Specificity: SPECIFIC | Relevance: MET | Alignment: ALIGNED
→ Underlying disease, complication, and anatomic site all present.

**Post-Surgical**
F2F: "Status post right total knee arthroplasty; wound dehiscence, skilled wound care and PT ordered."
485: M96.811
→ Specificity: SPECIFIC | Relevance: MET | Alignment: ALIGNED
→ Procedure, complication, and ordered services create a clear nexus.

---

## Non-Qualifying Examples
<!-- cms_section_id: PD_NON_QUALIFYING_EXAMPLES -->
<!-- element_type: ILLUSTRATION -->

**Conclusory**
F2F: "Patient requires home health services. Homebound confirmed."
→ Specificity: CONCLUSORY | Outcome: NOT_MET
→ No named condition; statement of need only.

**Vague**
F2F: "Patient has heart disease and needs monitoring."
→ Specificity: VAGUE | Outcome: NOT_MET
→ "Heart disease" lacks type, acuity, or specificity for ICD-10 mapping.

**Coincidental F2F**
F2F: "Annual diabetes check. A1c 7.1%, BP controlled." | 485 primary: post-surgical wound care.
→ Relevance: NOT MET | Outcome: NOT_MET
→ Routine diabetes check does not relate to the surgical wound driving home health.

---

## Language Mapping
<!-- cms_section_id: PD_LANGUAGE_MAPPING -->

| Extracted Language | Specificity | Alignment Signal | Strength |
|---|---|---|---|
| Named condition + ICD-10 code | SPECIFIC | Strong match to 485 | Strong |
| Named condition + type/acuity/site | SPECIFIC | Maps to 485 code | Strong |
| "CHF" alone (no type or acuity) | VAGUE | Partial match only | Weak |
| "Heart disease", "lung condition" | VAGUE | Cannot map to 485 | Failing |
| "Patient requires home health" | CONCLUSORY | No match possible | Failing |
| Symptoms only, no diagnosis | SYMPTOM_ONLY | No match possible | Failing |
| Same condition, different descriptor style | SPECIFIC | ALIGNED | Strong |
| Related condition at lower specificity | SPECIFIC/VAGUE | PARTIALLY_ALIGNED | Weak |
| Clinically unrelated to 485 primary | SPECIFIC | MISALIGNED | Failing |
