# F2F Audit — Encounter Classification Taxonomy
Use `encounter_category` (snake_case) and `encounter_subcategory` (numeric code) exactly as defined.
The `Code` column value in every table below is the exact value to write into the `encounter_subcategory` JSON field.

---

## 1. `f2f_encounter` — F2F Explicit Documents
| Code | Label |
|---|---|
| 1.1 | Face-to-Face Encounter Note |
| 1.2 | F2F Narrative (standalone write-up) |
| 1.3 | F2F Attestation / Certification Statement |
| 1.4 | F2F Co-signature or Addendum Document |
**Signals:** "Face-to-Face", "F2F", "Face to Face Encounter", explicit F2F title, standalone F2F letter or form — document purpose is solely to establish the F2F encounter

---

## 2. `poc_485` — POC / CMS-485 Documents
| Code | Label |
|---|---|
| 2.1 | Home Health Certification — Initial (CMS-485) |
| 2.2 | Home Health Recertification (CMS-485 Recert) |
| 2.3 | Plan of Care — Updated or Amended |
| 2.4 | Verbal Order Plan of Care Update |
| 2.5 | Individualized / Interim Care Plan |
**Signals:** "CMS-485", "Plan of Care", "Home Health Certification", "Recertification", "Certification Period", "Frequency/Duration of Visits", "Verbal Order Plan of Care", ICD-10 Diagnoses table with Order column

---

## 3. `telehealth_encounter` — Telehealth / Remote Visit Notes
| Code | Label |
|---|---|
| 3.1 | Telehealth / Video Visit Note |
| 3.2 | Telephone Encounter Note |
| 3.3 | Remote Patient Monitoring (RPM) Note |
| 3.4 | E-Visit / Patient Portal Message Note |
| 3.5 | Telehealth F2F Encounter Note |
**Signals:** "Telehealth", "Video Visit", "Telemedicine", "Virtual Visit", "Telephone Encounter", "RPM", "Remote Patient Monitoring", "E-Visit", "Patient Portal", "audio-only", "audio/video"

---

## 4. `operative_procedural_notes` — Operative and Procedural Notes
| Code | Label |
|---|---|
| 4.1 | Operative Report (intraoperative) |
| 4.2 | Post-Operative Note (immediate — OR / PACU) |
| 4.3 | Anesthesia Note |
| 4.4 | Pre-Anesthesia Assessment |
| 4.5 | Procedure Note — Minor or Bedside |
| 4.6 | Endoscopy / Colonoscopy Report |
| 4.7 | Cardiac Catheterization Report |
| 4.8 | Interventional Radiology Report |
| 4.9 | Pre-Operative Assessment Note |
| 4.10 | Post-Operative Follow-up Note |
**Signals:** "Operative Report", "Operation Note", "Anesthesia Record", "CRNA Note", "Pre-Anesthesia", "Pre-Op Assessment", "Procedure Note", "Endoscopy", "Colonoscopy", "Cardiac Cath", "IR Report", "EBL", "PACU", "Post-Op Follow-Up", incision / closure / sterile field language

---

## 5. `eligibility_certification` — Certification and Compliance Docs
> Standalone certification forms — skipped by encounter filter.

| Code | Label |
|---|---|
| 5.1 | Medical Necessity Letter or Statement |
| 5.2 | Certificate of Medical Necessity (CMN) |
| 5.3 | Advance Beneficiary Notice (ABN) |
| 5.4 | Prior Authorization Document |
| 5.5 | Physician Attestation or Co-signature Document |
**Signals:** "Medical Necessity", "CMN", "ABN", "Advance Beneficiary", "Prior Authorization", "Attestation", "Co-signature" — standalone form or letter with no clinical encounter narrative

---

## 6. `clinical_encounter_notes` — In-Person Clinical Encounters
| Code | Label |
|---|---|
| 6.1 | History and Physical (H&P) |
| 6.2 | Office Visit or Outpatient Encounter Note |
| 6.3 | Inpatient Progress Note |
| 6.4 | Emergency Department Note |
| 6.5 | Urgent Care Note |
| 6.6 | Consultation Note |
| 6.7 | Annual Wellness Visit (AWV) |
| 6.8 | Transitional Care Management Note (TCM) |
| 6.9 | Chronic Care Management Note (CCM) |
| 6.10 | Post-Discharge Follow-up Note |
| 6.11 | Nursing Home or SNF Encounter Note |
**Signals:** "H&P", "Office Visit", "Progress Note", "ED Note", "Urgent Care", "Consultation", "AWV", "TCM", "CCM", "Post-Discharge", "SNF Encounter" — in-person only; no telehealth indicators; no operative or discharge document connection

---

## 7. `skilled_hh_visit_notes` — Skilled Home Health Visit Notes
| Code | Label |
|---|---|
| 7.1 | Skilled Nursing Visit Note — Start of Care |
| 7.2 | Skilled Nursing Visit Note — Routine |
| 7.3 | Skilled Nursing Visit Note — Resumption of Care |
| 7.4 | Skilled Nursing Visit Note — Recertification |
| 7.5 | Wound Care Visit Note |
| 7.6 | Infusion Therapy Visit Note |
| 7.7 | Medication Management Visit Note |
| 7.8 | Psychiatric or Mental Health Nursing Visit Note |
| 7.9 | Maternal or Postpartum Visit Note |
| 7.10 | Supervisory Visit Note |
| 7.11 | Home Health Aide Visit Note |
| 7.12 | Case Conference or Team Meeting Note |
**Signals:** "Skilled Nursing Visit", "SN Visit", "Start of Care", "SOC", "Resumption", "ROC", "Wound Care", "Infusion", "Medication Management", "HHA Visit", "Case Conference", "Team Meeting"

---

## 8. `therapy_visit_notes` — Therapy Visit Notes
| Code | Label |
|---|---|
| 8.1 | Physical Therapy Evaluation Note |
| 8.2 | Physical Therapy Progress Note |
| 8.3 | Physical Therapy Discharge Note |
| 8.4 | Occupational Therapy Evaluation Note |
| 8.5 | Occupational Therapy Progress Note |
| 8.6 | Occupational Therapy Discharge Note |
| 8.7 | Speech Language Pathology Evaluation Note |
| 8.8 | Speech Language Pathology Progress Note |
| 8.9 | Speech Language Pathology Discharge Note |
| 8.10 | Respiratory Therapy Note |
| 8.11 | Therapy Re-evaluation Note |
**Signals:** "Physical Therapy", "PT Evaluation", "PT Progress", "Occupational Therapy", "OT Evaluation", "Speech Language Pathology", "SLP", "Respiratory Therapy", "RT Note", "Therapy Discharge", "Re-evaluation"

---

## 9. `discharge_and_transition` — Discharge and Transition Documents
| Code | Label |
|---|---|
| 9.1 | Hospital Discharge Summary |
| 9.2 | Skilled Nursing Facility Discharge Summary |
| 9.3 | Inpatient Rehabilitation Facility Discharge Summary |
| 9.4 | Long Term Acute Care Discharge Summary |
| 9.5 | Home Health Discharge Summary |
| 9.6 | Hospice Discharge Summary |
| 9.7 | Transfer Summary |
| 9.9 | Inpatient Discharge Note — Attending |
**Signals:** "Discharge Summary", "D/C Summary", "Hospital Course", "Discharge Diagnosis", "Discharge Date", "SNF Discharge", "IRF Discharge", "LTACH Discharge", "Transfer Summary", "Attending Discharge Note"
> `9.8` moved to `referral_documents / 15.8` (see category 15). A referral **embedded within** a discharge summary stays here (`9.1`); a **standalone** referral note/letter → `15.8`. Code `9.8` is retired (gap left; rows not renumbered).

---

## 10. `standardized_assessments` — Standardized Assessment Instruments
> Structured data forms — skipped by encounter filter.

| Code | Label |
|---|---|
| 10.1 | OASIS Assessment — Start of Care |
| 10.2 | OASIS Assessment — Resumption of Care |
| 10.3 | OASIS Assessment — Recertification |
| 10.4 | OASIS Assessment — Discharge |
| 10.5 | OASIS Assessment — Transfer to Inpatient |
| 10.6 | Fall Risk Assessment |
| 10.7 | Cognitive or Mental Status Assessment |
| 10.8 | Pain Assessment |
| 10.9 | Wound or Skin Assessment |
| 10.10 | Nutritional or Functional Assessment |
| 10.11 | Depression or Behavioral Health Screening |
| 10.12 | Medication Reconciliation Record |
**Signals:** "OASIS", "OASIS-E", "M0010", "Fall Risk", "Morse Fall Scale", "Braden Scale", "PHQ-9", "Mini-Cog", "Pain Scale", "Wound Assessment", "Medication Reconciliation"

---

## 11. `physician_orders` — Physician and Specialist Orders
> Standalone physician orders — supporting documents (corroborate ordered services); not standalone F2F encounters. **Referral-type orders now live in category 15** (`referral_documents`).

| Code | Label |
|---|---|
| 11.1 | Verbal Order |
| 11.2 | Telephone Order |
| 11.3 | Written Physician Order |
| 11.4 | Medication Prescription |
| 11.6 | DME or Equipment Order |
| 11.7 | Laboratory Order |
| 11.8 | Imaging Order |
| 11.10 | Hospice Order |
**Signals:** "Verbal Order", "Telephone Order", "Physician Order", "Medication Order", "DME Order", "Lab Order", "Imaging Order" — no clinical narrative; standalone order page only
> `11.5` (Home Health Order, non-485) → `15.2` and `11.9` (Specialty Referral Order) → `15.7`. Codes `11.5` / `11.9` are retired (gaps left; rows not renumbered). A **referral/HH-initiation** order → category 15; a pure clinical order (med/lab/imaging/DME) stays here.

---

## 12. `hospice_palliative_care` — Hospice and Palliative Care Documents
| Code | Label |
|---|---|
| 12.1 | Hospice Election Form |
| 12.2 | Hospice Certification of Terminal Illness |
| 12.3 | Hospice Recertification |
| 12.4 | Hospice IDG Meeting Note |
| 12.5 | Hospice Nursing Visit Note |
| 12.6 | Hospice Social Work Note |
| 12.7 | Hospice Chaplaincy Note |
| 12.8 | Palliative Care Consultation Note |
| 12.9 | Goals of Care / Advance Care Planning Note |
| 12.10 | Hospice Plan of Care |
| 12.11 | Palliative Care Plan |
**Signals:** "Hospice Election", "Terminal Illness Certification", "IDG Meeting", "Hospice Visit", "Palliative Care", "Goals of Care", "Advance Care Planning", "POLST", "DNR", "Comfort Care", "Hospice Plan of Care"

---

## 13. `social_work_support` — Social Work and Support Services
| Code | Label |
|---|---|
| 13.1 | Social Work Assessment Note |
| 13.2 | Social Work Progress Note |
| 13.3 | Social Work Discharge Plan |
| 13.4 | Caregiver Assessment Note |
| 13.5 | Patient Education Note |
**Signals:** "Social Work Assessment", "MSW Assessment", "Social Work Progress", "Discharge Plan", "Caregiver Assessment", "Patient Education", "Teaching Note"

---

## 14. `administrative_operational` — Administrative and Compliance Documents
> Administrative documents — skipped by encounter filter.

| Code | Label |
|---|---|
| 14.1 | Admission Agreement or Service Agreement |
| 14.2 | Patient Rights and Responsibilities |
| 14.3 | HIPAA Notice of Privacy Practices |
| 14.4 | Emergency Preparedness Plan |
| 14.5 | Home Safety Assessment |
| 14.6 | Infection Control Documentation |
| 14.7 | Physician Acknowledgment or Communication Log |
| 14.8 | Insurance Verification or Authorization Record |
| 14.9 | Incident or Occurrence Report |
| 14.10 | Agency Internal Audit or QA Record |
| 14.11 | Orientation and Training Record |
**Signals:** "Admission Agreement", "Service Agreement", "Patient Rights", "HIPAA", "Privacy Notice", "Emergency Plan", "Home Safety", "Infection Control", "QA Record", "Insurance Verification", "Incident Report"

---

## 15. `referral_documents` — Referral and Intake Documents
> Supporting/referral documents — they corroborate skilled need, the primary reason for home health, and physician intent/relatedness. A referral is **not** a standalone F2F clinical encounter and is **not selectable as the best F2F encounter**; use it as supporting evidence only.

| Code | Label |
|---|---|
| 15.1 | Home Health Referral / Intake Form |
| 15.2 | Physician Order Referring to Home Health (non-485) |
| 15.3 | Facility Discharge Referral to Home Health (hospital / SNF / IRF) |
| 15.4 | Skilled Nursing (SN) Referral Order |
| 15.5 | Therapy Referral Order (PT / OT / SLP) |
| 15.7 | Specialty / Consultation Referral Order |
| 15.8 | Referral Note or Letter (narrative) |
| 15.9 | Referral Acknowledgment / Receipt |
| 15.10 | Verbal / Telephone Referral |
| 15.11 | Aide / MSW / Ancillary Service Referral Order |
**Signals:** "Referral", "Referral Order", "Reason for Referral", "Referral Source", "Referring Physician", "Refer to Home Health Services", "Refer to PT/OT/SLP/SN", "Home Health Order", "Intake", "Referral Form" — document purpose is to **refer or initiate** services, not to narrate a clinical encounter.
> `15.6` is intentionally omitted — DME is captured as an **order** (`11.6`), not a referral. Referral precedence: standalone referral → category 15 over `physician_orders` (11); a referral embedded in a discharge summary stays `9.1`; a referral within the CMS-485 stays `poc_485` (2).

---

## Special Codes
| encounter_category | encounter_subcategory | Condition |
|---|---|---|
| `unplaced` | `UNPLACED` | Content does not fit any category or sub-type |
| `addendum` | `ADDENDUM` | Addition to a prior encounter; inherits parent type; requires `parent_encounter_index` |

---

## Classification Priority Rules

1. **F2F explicit first:** Document title or body explicitly states "Face-to-Face Encounter" as its primary purpose → `f2f_encounter`; **exception** — if telehealth indicators are also present, apply rule 2 instead.
2. **Telehealth flag:** Telehealth indicators present ("Video Visit", "Telemedicine", "audio/video") → `telehealth_encounter`; if ALSO explicit F2F → `telehealth_encounter / 3.5` (telehealth modality takes priority over F2F category).
3. **POC/485 over clinical:** "CMS-485", "Certification Period", or "Frequency/Duration of Visits" in header → `poc_485`.
4. **Discharge summary over progress note:** "Hospital Course" + "Discharge Diagnosis" both present → `discharge_and_transition / 9.1`, not `clinical_encounter_notes / 6.3`.
5. **Operative episode arc:** All pre-op, intraoperative, immediate post-op, and post-op follow-up notes → `operative_procedural_notes`; use `4.9` for pre-op assessment, `4.1`/`4.2` for intraoperative/PACU, `4.10` for follow-up clinic visit after surgery.
6. **Referral consolidation:** A document whose primary purpose is to refer or initiate services (referral order/letter, intake form, "Reason for Referral", "Refer to PT/OT/SLP/SN", "Refer to Home Health Services") → `referral_documents (15)`, taking precedence over `physician_orders (11)`. A referral **embedded in** a discharge summary stays `discharge_and_transition / 9.1`; a referral **within** the CMS-485 stays `poc_485 (2)`. Referral documents are supporting evidence, not standalone F2F encounters.
7. **Addendum:** Page explicitly labeled as addendum → `addendum / ADDENDUM`.
8. **UNPLACED only:** OCR-corrupted or fully uninterpretable content.
