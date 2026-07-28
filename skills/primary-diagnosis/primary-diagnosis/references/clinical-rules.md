# Primary Diagnosis — Clinical Audit Rules
# Source: Clinical operationalization of MBPM Ch. 7 §30.5.1.2
# FTF_Clinical_AI_Rules_v2 | Element5 Clinical Review | July 1, 2026
# Applies alongside cms-rules.md — does not replace CMS requirements

---

## CR_NECESSITY_PATHWAYS — Active Medical Necessity — Three-Pathway Test
<!-- cms_section_id: CR_NECESSITY_PATHWAYS -->
<!-- element_type: CRITERIA -->

Source: Clinical operationalization of Chapter 7 §30.5.1.2.

A primary diagnosis determination is **MET** only when the F2F note satisfies
**at least ONE** of the three pathways below. Diagnosis mention alone is NOT sufficient.

**Pathway A — Exacerbation or Change in Condition**
- New or worsening symptoms attributable to the primary diagnosis
- Recent hospitalization or ER visit related to the primary diagnosis
- Decline in functional status, ambulation, or self-care linked to the primary diagnosis
- New or significantly changed clinical findings (vitals, labs, wound status, neurological signs)

**Pathway B — New or Changed Medication / Treatment Regimen**
- New medication started for the primary diagnosis
- Dose adjustment, titration, or discontinuation of existing medication
- New injectable, infusion, or high-risk medication requiring skilled administration or monitoring
- Complex wound care, dressing changes, or new treatment orders requiring skilled nursing

**Pathway C — Active Skilled Service Need**
- Patient or caregiver requires skilled teaching/training for a new or complex regimen
- Patient requires skilled monitoring due to clinical instability or high-risk medication
- Physician explicitly orders SN, PT, OT, or SLP in context of the primary diagnosis
- Patient has safety risk at home requiring professional assessment (fall risk, cognitive
  impairment, medication mismanagement)

Set `result.pathways_met` to the codes of all satisfied pathways: `A`, `B`, `C`.
Set `result.medical_necessity_met` = true only if at least one pathway is satisfied.

## CR_MET_SIGNALS — Signal Language — MET Indicators
<!-- cms_section_id: CR_MET_SIGNALS -->
<!-- element_type: ILLUSTRATION -->

Source: FTF_Clinical_AI_Rules_v2, Section 3.
Clients may REPLACE this section with MAC-specific signal phrases via client-rules.md.

| Signal Category | MET Example Language |
|---|---|
| Exacerbation / Worsening | "BP uncontrolled, readings 178/102–192/108. Medication adjustment made." |
| Recent Hospitalization / ER | "Discharged 5 days ago following acute CHF exacerbation, 12 lb weight gain." |
| New or Changed Medication | "Started Eliquis 5mg BID for new AFib. Patient requires anticoagulant education." |
| Functional Decline | "Unable to perform ADLs independently post-CVA. PT ordered." |
| New Clinical Findings | "HbA1c 11.2 (up from 8.4). Insulin initiated. SN needed for glucose monitoring." |
| Explicit Skilled Order | "Refer to HH: SN wound care left heel stage III, medication management, fall risk." |
| Safety / Cognitive Risk | "Moderate dementia, lives alone, unable to self-administer medications. SN ordered." |
| Post-Surgical Need | "8 days post TKA. Wound requiring daily dressing changes. PT for ROM." |

## CR_NOT_MET_SIGNALS — Disqualifying Language — Auto NOT MET Triggers
<!-- cms_section_id: CR_NOT_MET_SIGNALS -->
<!-- element_type: ILLUSTRATION -->

Source: FTF_Clinical_AI_Rules_v2, Section 4.
Clients may EXTEND this section with additional disqualifying patterns via client-rules.md.

If the F2F note contains ONLY the following for the primary diagnosis, flag as NOT MET:

| Disqualifying Pattern | Why It Fails |
|---|---|
| "[Diagnosis] — controlled. Continue current medications." | Stable chronic. No active change. No skilled service justified. |
| "Stable. No new concerns. Follow up in X months." | No exacerbation, no new orders, no functional change. |
| "Patient doing well. Continue treatment plan as directed." | Generic stable language — no active skilled need. |
| "History of [diagnosis]." | Past medical history only — no current active clinical need. |
| "[Diagnosis] noted on problem list. No active complaints." | Problem list entry only — no current skilled need. |
| "Lab values within normal limits. No medication changes." | Normal findings, no new orders or interventions. |
| "Patient denies symptoms related to [diagnosis]." | Patient-reported absence of symptoms — no acuity. |

## CR_DIAGNOSIS_SIGNALS — Diagnosis-Category Qualifying Language Guide
<!-- cms_section_id: CR_DIAGNOSIS_SIGNALS -->
<!-- element_type: ILLUSTRATION -->

Source: FTF_Clinical_AI_Rules_v2, Section 5.
Clients may REPLACE this section with MAC-specific or payer-specific signal phrases.

| Primary Diagnosis Category | Qualifying Language to Look For in F2F Note |
|---|---|
| Cardiac (CHF, AFib, CAD, Hypertension) | Uncontrolled BP/HR, new AFib, fluid overload, weight gain, SOB, new anticoagulant education, post-hospitalization cardiac event, medication adjustment |
| Respiratory (COPD, Asthma, Pneumonia) | Acute exacerbation, increased SOB, O2 requirement change, new inhaler/nebulizer, post-hospitalization, new steroid/antibiotic course |
| Diabetes (Type 1, Type 2, Complications) | Elevated HbA1c, new insulin or dose change, hypoglycemia episodes, new/worsening diabetic wound, glucose monitoring instruction, neuropathy progression |
| Neurological (CVA, TBI, MS, Parkinson's) | New CVA/TIA, post-stroke functional deficits, new fall, progression of deficits, new PT/OT/SLP order, medication change for spasticity or seizure |
| Orthopedic (Fracture, TKA, THA, Spine) | Post-op wound requiring skilled dressing, weight-bearing restrictions, PT for ROM/strength, fall risk assessment, new surgical complication |
| Wounds (Pressure Ulcer, Venous Stasis, Surgical) | Active wound requiring skilled dressing, wound deterioration, infection signs, debridement orders, wound measurement/staging documented |
| Dementia / Cognitive (Alzheimer's, Vascular) | Cognitive decline, unsafe at home, medication mismanagement, new behavioral changes, caregiver unable to manage, new safety concern |
| Oncology (Active or Post-Treatment) | New chemo/radiation side effects, pain management changes, IV medication teaching, fatigue/weakness requiring SN, new wound/ostomy care |
| Urinary / Renal (UTI, CKD, Catheter Care) | Active UTI with skilled treatment, catheter change or teaching, CKD labs significantly worsened, new dietary/fluid restriction teaching needed |

## Citation
FTF_Clinical_AI_Rules_v2 | Element5 Clinical Review | July 1, 2026
Clinical operationalization of MBPM Pub. 100-02, Chapter 7, §30.5.1.2
42 CFR §424.22(a)(1)(v)
