# F2F Audit — Encounter Classification Taxonomy

Use `encounter_category` (short snake_case key) and `encounter_subcategory` (numeric code)
exactly as defined below.

---

## Category: `eligibility_certification`
*Category 1 — Eligibility and Certification Documents*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 1.1  | `1.1` | Face to Face Encounter Note |
| 1.2  | `1.2` | Face to Face Encounter Narrative (standalone) |
| 1.3  | `1.3` | Home Health Certification (CMS-485) |
| 1.4  | `1.4` | Home Health Recertification (CMS-485 Recert) |
| 1.5  | `1.5` | Medical Necessity Letter or Statement |
| 1.6  | `1.6` | Certificate of Medical Necessity (CMN) |
| 1.7  | `1.7` | Advance Beneficiary Notice (ABN) |
| 1.8  | `1.8` | Prior Authorization Document |
| 1.9  | `1.9` | Physician Attestation or Co-signature Document |

**Key signals:** "Face-to-Face", "F2F", "CMS-485", "Certification", "Plan of Care" header,
"Medical Necessity", "CMN", "ABN", "Advance Beneficiary", "Attestation", "Co-signature"

---

## Category: `plan_of_care`
*Category 2 — Plan of Care Documents*
> Reference documents — will be skipped by the encounter filter.

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 2.1  | `2.1` | Plan of Care — Initial |
| 2.2  | `2.2` | Plan of Care — Updated or Amended |
| 2.3  | `2.3` | Verbal Order Plan of Care Update |
| 2.4  | `2.4` | Individualized Care Plan (ICP) |
| 2.5  | `2.5` | Interim Care Plan |
| 2.6  | `2.6` | Hospice Plan of Care |
| 2.7  | `2.7` | Palliative Care Plan |

**Key signals:** "Plan of Care", "ICP", "Care Plan", "Verbal Order POC", "Interim Plan",
"Hospice Plan", structured medication/frequency/diagnosis table

---

## Category: `clinical_encounter_notes`
*Category 3 — Clinical Encounter and Visit Notes*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 3.1  | `3.1` | History and Physical (H&P) |
| 3.2  | `3.2` | Office Visit or Outpatient Encounter Note |
| 3.3  | `3.3` | Inpatient Progress Note |
| 3.4  | `3.4` | Emergency Department Note |
| 3.5  | `3.5` | Urgent Care Note |
| 3.6  | `3.6` | Consultation Note |
| 3.7  | `3.7` | Telehealth or Telemedicine Visit Note |
| 3.8  | `3.8` | Annual Wellness Visit (AWV) |
| 3.9  | `3.9` | Transitional Care Management Note (TCM) |
| 3.10 | `3.10` | Chronic Care Management Note (CCM) |
| 3.11 | `3.11` | Post-Discharge Follow-up Note |
| 3.12 | `3.12` | Pre-Operative Assessment Note |
| 3.13 | `3.13` | Post-Operative Follow-up Note |
| 3.14 | `3.14` | Inpatient Discharge Note — Attending |
| 3.15 | `3.15` | Nursing Home or SNF Encounter Note |

**Key signals:** "H&P", "Office Visit", "Progress Note", "ED Note", "Emergency Department",
"Urgent Care", "Consultation", "Telehealth", "Video Visit", "Annual Wellness", "AWV",
"Transitional Care", "TCM", "CCM", "Post-Discharge", "Pre-Op", "Post-Op Follow-Up",
"Discharge Note", "SNF Encounter"

---

## Category: `skilled_hh_visit_notes`
*Category 4 — Skilled Home Health Visit Notes*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 4.1  | `4.1` | Skilled Nursing Visit Note — Start of Care |
| 4.2  | `4.2` | Skilled Nursing Visit Note — Routine |
| 4.3  | `4.3` | Skilled Nursing Visit Note — Resumption of Care |
| 4.4  | `4.4` | Skilled Nursing Visit Note — Recertification |
| 4.5  | `4.5` | Wound Care Visit Note |
| 4.6  | `4.6` | Infusion Therapy Visit Note |
| 4.7  | `4.7` | Medication Management Visit Note |
| 4.8  | `4.8` | Psychiatric or Mental Health Nursing Visit Note |
| 4.9  | `4.9` | Maternal or Postpartum Visit Note |
| 4.10 | `4.10` | Supervisory Visit Note |
| 4.11 | `4.11` | Home Health Aide Visit Note |
| 4.12 | `4.12` | Case Conference or Team Meeting Note |

**Key signals:** "Skilled Nursing Visit", "SN Visit", "Start of Care", "SOC", "Resumption",
"ROC", "Wound Care", "Infusion", "Medication Management", "Home Health Aide", "HHA Visit",
"Case Conference", "Team Meeting"

---

## Category: `therapy_visit_notes`
*Category 5 — Therapy Visit Notes*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 5.1  | `5.1` | Physical Therapy Evaluation Note |
| 5.2  | `5.2` | Physical Therapy Progress Note |
| 5.3  | `5.3` | Physical Therapy Discharge Note |
| 5.4  | `5.4` | Occupational Therapy Evaluation Note |
| 5.5  | `5.5` | Occupational Therapy Progress Note |
| 5.6  | `5.6` | Occupational Therapy Discharge Note |
| 5.7  | `5.7` | Speech Language Pathology Evaluation Note |
| 5.8  | `5.8` | Speech Language Pathology Progress Note |
| 5.9  | `5.9` | Speech Language Pathology Discharge Note |
| 5.10 | `5.10` | Respiratory Therapy Note |
| 5.11 | `5.11` | Therapy Re-evaluation Note |

**Key signals:** "Physical Therapy", "PT Evaluation", "PT Progress", "Occupational Therapy",
"OT Evaluation", "OT Progress", "Speech Language Pathology", "SLP Evaluation",
"Respiratory Therapy", "RT Note", "Therapy Discharge", "Re-evaluation"

---

## Category: `standardized_assessments`
*Category 6 — Standardized Assessment Instruments*
> Structured data collection forms — will be skipped by the encounter filter.

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 6.1  | `6.1` | OASIS Assessment — Start of Care |
| 6.2  | `6.2` | OASIS Assessment — Resumption of Care |
| 6.3  | `6.3` | OASIS Assessment — Recertification |
| 6.4  | `6.4` | OASIS Assessment — Discharge |
| 6.5  | `6.5` | OASIS Assessment — Transfer to Inpatient |
| 6.6  | `6.6` | Fall Risk Assessment |
| 6.7  | `6.7` | Cognitive or Mental Status Assessment |
| 6.8  | `6.8` | Pain Assessment |
| 6.9  | `6.9` | Wound or Skin Assessment |
| 6.10 | `6.10` | Nutritional or Functional Assessment |
| 6.11 | `6.11` | Depression or Behavioral Health Screening |
| 6.12 | `6.12` | Medication Reconciliation Record |

**Key signals:** "OASIS", "OASIS-E", "M0010", "Start of Care Assessment", "Fall Risk",
"Morse Fall Scale", "Braden Scale", "PHQ-9", "Mini-Cog", "Pain Scale",
"Wound Assessment", "Braden Score", "Medication Reconciliation"

---

## Category: `discharge_and_transition`
*Category 7 — Discharge and Transition Documents*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 7.1  | `7.1` | Hospital Discharge Summary |
| 7.2  | `7.2` | Skilled Nursing Facility Discharge Summary |
| 7.3  | `7.3` | Inpatient Rehabilitation Facility Discharge Summary |
| 7.4  | `7.4` | Long Term Acute Care Discharge Summary |
| 7.5  | `7.5` | Home Health Discharge Summary |
| 7.6  | `7.6` | Hospice Discharge Summary |
| 7.7  | `7.7` | Transfer Summary |
| 7.8  | `7.8` | Referral Note or Letter |

**Key signals:** "Discharge Summary", "D/C Summary", "Hospital Course", "Discharge Diagnosis",
"Discharge Date", "SNF Discharge", "IRF Discharge", "LTACH Discharge", "HH Discharge",
"Transfer Summary", "Referral Note", "Referral Letter"

---

## Category: `physician_orders`
*Category 8 — Physician and Specialist Orders*
> Standalone order documents — will be skipped by the encounter filter.

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 8.1  | `8.1` | Verbal Order |
| 8.2  | `8.2` | Telephone Order |
| 8.3  | `8.3` | Written Physician Order |
| 8.4  | `8.4` | Medication Prescription |
| 8.5  | `8.5` | Home Health Order (non-485) |
| 8.6  | `8.6` | DME or Equipment Order |
| 8.7  | `8.7` | Laboratory Order |
| 8.8  | `8.8` | Imaging Order |
| 8.9  | `8.9` | Specialty Referral Order |
| 8.10 | `8.10` | Hospice Order |

**Key signals:** "Verbal Order", "Telephone Order", "Physician Order", "Medication Order",
"Home Health Order", "DME Order", "Lab Order", "Imaging Order", "Referral Order",
"Hospice Order" — standalone order pages with no accompanying clinical narrative

---

## Category: `operative_procedural_notes`
*Category 9 — Operative and Procedural Notes*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 9.1  | `9.1` | Operative Report |
| 9.2  | `9.2` | Anesthesia Note |
| 9.3  | `9.3` | Pre-Anesthesia Assessment |
| 9.4  | `9.4` | Procedure Note — Minor or Bedside |
| 9.5  | `9.5` | Endoscopy or Colonoscopy Report |
| 9.6  | `9.6` | Cardiac Catheterization Report |

**Key signals:** "Operative Report", "Operation Note", "Anesthesia Record", "CRNA Note",
"Pre-Anesthesia", "Procedure Note", "Endoscopy Report", "Colonoscopy", "Cardiac Cath",
incision/closure/sterile field language

---

## Category: `hospice_palliative_care`
*Category 10 — Hospice and Palliative Care Documents*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 10.1 | `10.1` | Hospice Election Form |
| 10.2 | `10.2` | Hospice Certification of Terminal Illness |
| 10.3 | `10.3` | Hospice Recertification |
| 10.4 | `10.4` | Hospice IDG Meeting Note |
| 10.5 | `10.5` | Hospice Nursing Visit Note |
| 10.6 | `10.6` | Hospice Social Work Note |
| 10.7 | `10.7` | Hospice Chaplaincy Note |
| 10.8 | `10.8` | Palliative Care Consultation Note |
| 10.9 | `10.9` | Goals of Care or Advance Care Planning Note |

**Key signals:** "Hospice Election", "Terminal Illness Certification", "IDG Meeting",
"Hospice Visit", "Palliative Care Consultation", "Goals of Care", "Advance Care Planning",
"POLST", "DNR", "Comfort Care"

---

## Category: `social_work_support`
*Category 11 — Social Work and Support Services*

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 11.1 | `11.1` | Social Work Assessment Note |
| 11.2 | `11.2` | Social Work Progress Note |
| 11.3 | `11.3` | Social Work Discharge Plan |
| 11.4 | `11.4` | Caregiver Assessment Note |
| 11.5 | `11.5` | Patient Education Note |

**Key signals:** "Social Work Assessment", "MSW Assessment", "Social Work Progress",
"Discharge Plan", "Caregiver Assessment", "Patient Education", "Teaching Note"

---

## Category: `administrative_operational`
*Category 12 — Administrative, Operational, and Compliance Documents*
> Administrative documents — will be skipped by the encounter filter.

| Code | encounter_subcategory | Label |
|------|-----------------------|-------|
| 12.1  | `12.1` | Admission Agreement or Service Agreement |
| 12.2  | `12.2` | Patient Rights and Responsibilities |
| 12.3  | `12.3` | HIPAA Notice of Privacy Practices |
| 12.4  | `12.4` | Emergency Preparedness Plan |
| 12.5  | `12.5` | Home Safety Assessment |
| 12.6  | `12.6` | Infection Control Documentation |
| 12.7  | `12.7` | Physician Acknowledgment or Communication Log |
| 12.8  | `12.8` | Insurance Verification or Authorization Record |
| 12.9  | `12.9` | Incident or Occurrence Report |
| 12.10 | `12.10` | Agency Internal Audit or QA Record |
| 12.11 | `12.11` | Orientation and Training Record |

**Key signals:** "Admission Agreement", "Service Agreement", "Patient Rights", "HIPAA",
"Privacy Notice", "Emergency Plan", "Home Safety", "Infection Control", "QA Record",
"Insurance Verification", "Incident Report", "Occurrence Report"

---

## Special Codes

| encounter_category | encounter_subcategory | Condition |
|-------------------|----------------------|-----------|
| `unplaced` | `UNPLACED` | Page content does not fit any category or sub-type |
| `addendum` | `ADDENDUM` | Addition to a previously classified encounter; inherits parent encounter type; requires `parent_encounter_index` field |

---

## Classification Priority Rules

When a document matches multiple categories, apply these rules in order:

1. **F2F / Certification first:** If homebound + skilled services + eligible provider +
   orders all present → `eligibility_certification / 1.1` even without explicit F2F title.
2. **Telehealth flag:** If telehealth indicators are present → `clinical_encounter_notes / 3.7`
3. **Discharge summary > Progress note:** If "Hospital Course" and "Discharge Diagnosis" both
   present → `discharge_and_transition / 7.1` not `clinical_encounter_notes / 3.3`.
4. **Addendum:** If page is explicitly labeled as an addendum to a prior note → `addendum / ADDENDUM`.
5. **UNPLACED only when nothing fits:** If content is heavily OCR-corrupted or uninterpretable.
