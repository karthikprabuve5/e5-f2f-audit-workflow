# Skilled Services — CMS Examples
# MBPM Pub. 100-02, Chapter 7, §30.1–§30.4, §30.5.1.2
# Use in Step 5 to calibrate justification judgments.

---

## Qualifying Examples
<!-- cms_section_id: SS_QUALIFYING_EXAMPLES -->
<!-- element_type: ILLUSTRATION -->

**Skilled Nursing — Wound Care**
F2F: "Post-surgical wound dehiscence with signs of infection; requires daily sterile dressing changes and wound assessment by RN."
→ justification_type: wound_care | Signal: STRONG | Outcome: MET
→ Named condition, sterile technique required, not delegable to caregiver.

**Physical Therapy — Post-Surgical Rehab**
F2F: "Patient presents with 3/5 bilateral LE strength following right TKA; requires skilled PT for therapeutic exercise and gait training to restore safe ambulation."
→ rehabilitation_potential: documented | Signal: STRONG | Outcome: MET
→ Specific functional deficit, named procedure, functional goal stated, rehab potential clear.

**Skilled Nursing — Observation and Assessment (Valid)**
F2F: "Patient with new-onset atrial fibrillation on anticoagulation therapy; requires skilled nursing observation for bleeding risk, INR monitoring, and medication titration."
→ justification_type: observation_assessment | Signal: STRONG | Outcome: MET
→ Unstable condition, high-risk medication, specific risk requiring clinical judgment documented.

---

## Non-Qualifying Examples
<!-- cms_section_id: SS_NON_QUALIFYING_EXAMPLES -->
<!-- element_type: ILLUSTRATION -->

**Vague Therapy Justification**
F2F: "Patient would benefit from physical therapy to improve strength and mobility."
→ Signal: WEAK | Outcome: NOT_MET
→ "Would benefit" does not establish necessity; no functional deficit or goal stated.

**O&A on Stable Patient**
F2F: "Patient is stable with chronic CHF, well-controlled. Skilled nursing for observation and monitoring."
→ justification_type: observation_assessment | Signal: WEAK | Outcome: NOT_MET
→ Stable, well-controlled condition does not justify O&A-based SN; no instability documented.

**Custodial Only**
F2F: "Patient needs help with bathing, dressing, and meal preparation. Home health aide ordered."
→ Signal: ABSENT for skilled services | Outcome: NOT_MET (if only HHA ordered)
→ Personal care is custodial; HHA alone cannot establish HH eligibility.

---

## Language Mapping
<!-- cms_section_id: SS_LANGUAGE_MAPPING -->

| Extracted Language | Service | Signal | Notes |
|---|---|---|---|
| "requires skilled nursing for wound assessment and sterile dressing" | SN | STRONG | Specificity + non-delegable |
| "SN ordered for daily wound care" | SN | MODERATE | Wound care stated; assessment detail absent |
| "patient needs nursing visits" | SN | WEAK | No clinical basis stated |
| "requires skilled PT for gait training post-TKA; rehab potential present" | PT | STRONG | Deficit + goal + potential |
| "PT recommended to improve strength" | PT | WEAK | "Recommended" ≠ necessary; no functional goal |
| "SLP necessary due to dysphagia following CVA" | SLP | STRONG | Diagnosis + functional disorder + causal link |
| "stable CHF, observation needed" | SN (O&A) | WEAK | Stable condition; instability not documented |
| "new AF on warfarin, INR monitoring required" | SN (O&A) | STRONG | High-risk medication + instability documented |
| "MSS for social support needs" | MSS | WEAK | No link to illness impact on treatment |
| "MSS to address caregiver stress impeding wound care compliance" | MSS | STRONG | Direct illness nexus stated |
