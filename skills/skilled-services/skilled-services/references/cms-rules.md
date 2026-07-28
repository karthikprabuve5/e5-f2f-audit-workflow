# Skilled Services — CMS Audit Rules
# Source: MBPM Pub. 100-02, Chapter 7
# §30.1, §30.1.1, §30.1.2, §30.2.1–30.2.4, §30.3, §30.4, §30.5.1.2

---

## Qualifying Services
<!-- cms_section_id: SS_QUALIFYING_SERVICES -->

**Qualifying services that establish HH eligibility (can initiate HH):**
- `SN` — Skilled Nursing (RN or LPN/LVN under RN supervision)
- `PT` — Physical Therapy
- `SLP` — Speech-Language Pathology

**Non-initiating services (cannot be the sole qualifying service):**
- `OT` — Occupational Therapy: can continue HH after SN/PT/SLP discharged; cannot initiate alone
- `MSS` — Medical Social Services: must accompany a qualifying skilled service
- `HHA` — Home Health Aide: NOT a skilled service; must accompany a qualifying skilled service

If OT, MSS, or HHA is the ONLY ordered service → set the corresponding standalone flag.

---

## Skilled Necessity
<!-- cms_section_id: SS_SKILLED_NECESSITY -->

The nature of the service — not who performs it or that a physician ordered it —
determines skilled status. If unskilled personnel can safely perform it, it is NOT skilled.

**SN `justification_type` values:**
- `observation_assessment` — nurse observes and assesses an unstable/unpredictable condition; see SS_OBSERVATION_ASSESSMENT
- `management_evaluation` — nurse manages a complex multi-condition care plan requiring clinical judgment to prevent adverse outcomes; same instability standard as O&A applies
- `teaching_training` — professional skill required to instruct; once patient/caregiver learns → non-skilled
- `wound_care` — complex sterile wound management; simple teachable wounds → non-skilled after training
- `medication_management` — IV/IM/SubQ: skilled; oral medications: generally NOT skilled
- `catheter_care` — initial insertion: skilled; routine ongoing care after training: NOT skilled
- `psychiatric_nursing` — requires documented psychiatric diagnosis and reason skilled oversight needed
- `other_direct_care` — tube feeding, ostomy instruction, tracheotomy aspiration, IV therapy

Custodial care (bathing, grooming, meal prep, housekeeping, companionship) — NEVER skilled.

---

## Observation and Assessment
<!-- cms_section_id: SS_OBSERVATION_ASSESSMENT -->

O&A-based SN requires that the patient's condition is **unstable, unpredictable, or at risk
of significant change** such that only a nurse can determine the appropriate treatment course.

**Not sufficient:**
- "Patient is complex," "Patient requires monitoring," "Needs observation"
- Stable patient with routine follow-up needs

**Sufficient:**
- Documented instability, acute change, complication risk
- New high-risk medication requiring skilled monitoring
- Unpredictable clinical course requiring clinical judgment

Stable, predictable condition without documented risk → O&A does NOT qualify → signal_strength WEAK.

---

## Intermittent Basis
<!-- cms_section_id: SS_INTERMITTENT_BASIS -->

SN must be **intermittent** — not continuous 24-hour care:
- Provided fewer than 7 days/week, OR
- Provided 7 days/week for fewer than 8 hours/day for a finite, predictable period

Documentation implying continuous around-the-clock nursing → `continuous_care_flag = true`.

**Venipuncture-only rule (§30.1.2):**
Venipuncture (blood draws) is covered ONLY when physician-ordered, part of the care plan,
AND not the sole SN service. If venipuncture is the ONLY SN justification → `venipuncture_only_flag = true`.

---

## Clinical Nexus
<!-- cms_section_id: SS_CLINICAL_NEXUS -->

Each service must be:
1. Clinically linked to a documented diagnosis or clinical finding in the F2F note
2. **Necessary** — not merely beneficial or helpful
   - WEAK: "would benefit from PT," "PT may help," "OT recommended"
   - STRONG: "requires skilled PT," "SN ordered for," "SLP necessary due to dysphagia"
3. For PT/OT/SLP: supported by a stated functional goal or expected outcome
4. For PT/OT/SLP: supported by rehabilitation potential OR a maintenance rationale

**Rehabilitation potential:**
- `documented` — note states expected functional improvement or need for skilled maintenance
- `not_documented` — no potential or maintenance rationale stated → signal_strength WEAK
- `not_applicable` — SN, MSS, HHA

**MSS-specific rules:**
- Social/emotional problem must DIRECTLY and adversely impact treatment or rate of recovery
- Short-term counseling only — chronic social situation unrelated to current illness → NOT covered
- "Patient has social needs" alone is insufficient

---

## Maintenance Therapy
<!-- cms_section_id: SS_MAINTENANCE_THERAPY -->

PT, OT, or SLP maintenance is covered ONLY when the therapist's skills are required to:
- Safely perform or oversee the exercise/therapeutic program, OR
- Detect a change in the patient's condition that non-skilled personnel would not recognize

**Required documentation:** The note must state explicitly that:
- Performance by non-skilled personnel would be unsafe or clinically ineffective
- The patient's condition necessitates ongoing therapist skill — not just caregiver assistance

Maintenance documented without this rationale → `maintenance_without_justification = true`

---

## Citation
MBPM Pub. 100-02, Chapter 7, §30.1–§30.4, §30.5.1.2 | 42 CFR §409.44
