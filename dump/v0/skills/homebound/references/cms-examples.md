# Homebound Status — CMS Examples and Edge Cases
# Source: MBPM Pub. 100-02, Chapter 7, §30.1.1
# Rev. 208, Effective 01-01-15
# Use this file in Step 3 to map extracted language to CMS criteria.

---

## Qualifying Examples
<!-- cms_section_id: HB_QUALIFYING_EXAMPLES -->
<!-- element_type: ILLUSTRATION -->

Use to calibrate judgment when extracted language is ambiguous.

**Paralysis / Wheelchair / Crutches**
Stroke patient confined to wheelchair or requiring crutches.
→ Prong 1 met: supportive device needed
→ Signals: paralysis, wheelchair, crutches, stroke

**Blind or Cognitive Impairment**
Patient who is blind or has cognitive impairment requiring
another person's assistance to leave residence.
→ Prong 1 met: assistance of another person required
→ Signals: blind, dementia, cognitive impairment, requires escort

**Post-Surgical Recovery**
Patient returned from surgery with physician-restricted activity
such as limited weight bearing, stair restriction, or bed rest.
→ Prong 1 met: needs assistance; Prong 2 met: activity restricted
→ Signals: post-op, surgery, activity restriction, weight bearing

**Severe Cardiac or Pulmonary Condition**
Patient must avoid all stress and physical activity due to
cardiac or pulmonary severity — leaving is medically contraindicated.
→ Prong 1 met: medically contraindicated
→ Signals: severe CHF, COPD, avoid exertion, oxygen dependent

**Psychiatric Illness**
Patient refuses to leave home or is unsafe to leave unattended
even without physical limitations.
→ Prong 1 met: medically contraindicated / unsafe
→ Signals: psychiatric, refuses to leave, unsafe unattended, agoraphobia

**Neurodegenerative Disease**
Late-stage ALS, Parkinson's, MS, or similar.
Evaluate condition over time — frequent medical appointments
during one week do not disqualify if overall condition qualifies.
→ Prong 1 and Prong 2 met
→ Signals: ALS, Parkinson's, MS, neurodegenerative, late stage

---

## Non-Qualifying Examples
<!-- cms_section_id: HB_NON_QUALIFYING_EXAMPLES -->
<!-- element_type: ILLUSTRATION -->

**Advanced Age Alone**
Patient does not go out due to feebleness from aging only.
Fails if no Prong 1 criterion documented.
→ Signals to reject without Prong 1: elderly, frail, aged, feeble

---

## Language Mapping
<!-- cms_section_id: HB_LANGUAGE_MAPPING -->

| Extracted Language | Prong | Sub-Criterion | Strength |
|-------------------|-------|--------------|---------|
| wheelchair, walker, cane, crutches | 1 | device_needed | Strong |
| requires assistance of another person | 1 | assistance_of_person | Strong |
| special transportation required | 1 | special_transport | Strong |
| medically contraindicated to leave | 1 | medically_contraindicated | Strong |
| considerable and taxing effort | 2 | considerable_effort | Strong |
| unable to leave without assistance | 2 | normal_inability | Strong |
| oxygen dependent, cannot exert | 1 + 2 | medically_contraindicated + considerable_effort | Strong |
| confined to home due to [condition] | 1 + 2 | needs detail to confirm sub-criterion | Needs detail |
| difficulty leaving | 2 | considerable_effort | Weak — flag |
| does not go out | 2 | normal_inability | Weak — flag |
| patient is homebound | 1 + 2 | conclusory — sub-criterion unclear | Conclusory — flag |
| elderly, frail, advanced age | 1 | none — non-qualifying | Non-qualifying — flag |
| patient is weak | 2 | considerable_effort | Insufficient — flag |
