# Encounter Selection — Output Schema
#
# The exact JSON the selection agent must return. It reuses the shared envelope
# header (schema_version … reasoning) so it is scannable alongside every other
# agent output, but its `result` block is selection-specific. Return ONLY the
# JSON object; save it to
# /workspace/documents/outputs/encounter-selection/results.json.

---

## Rules

<!-- cms_section_id: SEL_SCHEMA_RULES -->

- **Top-level `status`** mirrors `result.decision`
  (`SELECTED` | `NEEDS_HUMAN_REVIEW` | `NO_ELIGIBLE_ENCOUNTER`).
- **Evidence is inline and location-only:** every cited claim uses
  `{ "verbiage": "...", "page": N }`, copied verbatim from the merge_encounters input. Do
  NOT use line numbers, and do NOT use the `evidence_id`/`evidence_refs` linkage
  system (that is an upstream extraction contract). Top-level `evidence` is `[]`.
- **Every roster encounter** appears in `result.encounters`, in `encounter_index`
  order — never drop one, even `NOT_ELIGIBLE` ones.
- `result.best_encounter_index` is an integer, or `null` **only** for
  `NO_ELIGIBLE_ENCOUNTER`.
- Populate `rules_applied.cms` with the `cms_section_id`s applied and
  `rules_applied.client` with every client directive evaluated.
- Factual reasoning only — no PII, no fabricated content, no re-derivation of
  upstream verdicts.
- **`reasoning.summary` is the CLINICAL narrative of the whole selection, in an
  AUDITOR's voice** (a MAC reviewer assessing whether the record substantiates the
  claim — clinical in substance, evaluative in stance) — see `inference-summary.md`.
  It never uses system/process vocabulary (gates, numeric score, "clinical-pillar",
  date-aligned/anchor, `selection_method`, or field names); those mechanics live in
  the structured fields and in `result.comparison[]` (the technical defense).

---

## `result` structure

<!-- cms_section_id: SEL_SCHEMA_RESULT -->

- `best_encounter_index` — the recommended encounter (integer | null).
- `best_encounter_score` — the winner's weighted score (0–100 | null).
- `best_is_date_aligned` — bool: is the recommended encounter the date-aligned one?
- `date_aligned_encounter` — `{ present: bool, encounter_index: N | null,
  matched_anchor: "i_certify" | "undersigned" | null }` (see `SEL_DATE_ALIGNMENT`).
- `decision` — `SELECTED` | `NEEDS_HUMAN_REVIEW` | `NO_ELIGIBLE_ENCOUNTER`.
- `selection_method` — `date_and_clinical_agree` | `clinical_override_of_date_match`
  | `clinical_only_no_anchor` | `tie_break` | `sole_candidate`.
- `soc_date` — the SOC used (echoed from the prompt).
- `encounter_window` — `{ start, end }` (SOC−90 / SOC+30), or nulls if `SOC_MISSING`.
- `final_statement` — one plain sentence: either "The date-aligned encounter (idx N)
  is the best encounter." or "Encounter idx X is the best encounter, stronger than
  the date-aligned encounter idx N." (or the no-anchor variant).
- `selected_rationale` — 1–3 sentences on why the winner is the most
  claim-defensible, citing evidence.
- `encounters[]` — the per-encounter detailed relevance report (below).
- `comparison[]` — for each *non-winning* encounter, why it lost to the winner
  (always include the date-aligned encounter when it is not the winner).
- `flags[]` — decision-driving flags `{ flag, severity, evidence }`.
- `data_quality` — `{ missing_parameters, unable_to_determine, notes }`.
- `excluded_encounters[]` — supporting-only encounters removed from candidacy
  **before** ranking (currently `referral_documents`). Each is
  `{ encounter_index, encounter_category, encounter_subcategory, reason }` with
  `reason = "referral_document_supporting_only"`. This list is populated
  deterministically by the orchestration filter, not inferred by the agent — the
  agent never sees these encounters, must not score or rank them, and must never
  return one as `best_encounter_index`. They may still be cited as supporting
  evidence for a real encounter's clinical pillars.
- `excluded_encounter_indices[]` — the flat list of excluded `encounter_index`
  values, for quick lookup.

### Per-encounter block (`result.encounters[i]`)

- `encounter_index`, `encounter_date`
- `in_window` (bool | null)
- `date_aligned` (bool) — exact match to `i_certify` or `undersigned`;
  `matched_anchor` — `"i_certify"` | `"undersigned"` | null
- `standing` — `PREFERRED` | `VIABLE` | `WEAK` | `NOT_ELIGIBLE`
- `screen` — `{ timing, provider, substantiating_note, relatedness }` gate results
- `alignment` — the six parameters as alignment status (drives ranking + score):
  `{ time_window, primary_diagnosis, homebound, skilled_services,
     provider_eligibility, signature }`, each
  `ALIGNED` | `NOT_ALIGNED` | `UNABLE_TO_DETERMINE`.
- `score` (0–100) and `score_breakdown` — per-parameter points (see `SEL_SCORE`).
- `criteria_satisfied_count` (0–6) — count of `ALIGNED` parameters.
- `clinical_relevance` —
  `{ primary_diagnosis_alignment, skilled_services_alignment, homebound_support,
     provider_eligibility_alignment, strength (STRONG|ADEQUATE|WEAK), summary }` —
  the full F2F audit perspective; each sub-field carries its `alignment` status
  plus `verbiage` + `page`. `strength` is descriptive only (never overrides the
  tier order).
- `strengths[]`, `weaknesses[]`
- `risk_flags[]` — `{ flag, severity, evidence }`

---

## Example (illustrative — clinical-pillar coverage decides → SELECTED)

Both encounters pass the gates, align on primary dx, and share the certified date
(both date-aligned). Encounter 1 covers **2/2** clinical pillars (homebound +
skilled) and scores 85; Encounter 2 covers only **1/2** (homebound
`UNABLE_TO_DETERMINE`, inpatient rehab note) and scores 80. Encounter 1 wins on
clinical-pillar coverage; the score corroborates. It is also the date-aligned
encounter, so `best_is_date_aligned = true`. Its handwritten signature is a
disclosed `WEAK_SIGNATURE` warning, which does not block `SELECTED`.

```json
{
  "schema_version": "1.0",
  "parameter_id": "encounter_selection",
  "client_id": "DEFAULT",
  "evaluated_at": "2026-08-06T00:00:00Z",
  "status": "SELECTED",
  "confidence": 0.82,
  "result": {
    "best_encounter_index": 1,
    "best_encounter_score": 85,
    "best_is_date_aligned": true,
    "date_aligned_encounter": { "present": true, "encounter_index": 1, "matched_anchor": "undersigned" },
    "decision": "SELECTED",
    "selection_method": "date_and_clinical_agree",
    "soc_date": "2026-07-24",
    "encounter_window": { "start": "2026-04-25", "end": "2026-08-23" },
    "final_statement": "The date-aligned encounter (idx 1) is the best encounter.",
    "selected_rationale": "Encounter 1 is selected: it aligns on primary diagnosis (hip fracture, POC anchor S72.141D) and covers both clinical pillars — skilled services (PT justified) and homebound (both prongs MET). Encounter 2 ties on primary dx and skilled but does NOT substantiate homebound (inpatient rehab note), so Encounter 1 wins on clinical-pillar coverage (2/2 vs 1/2) and score (85 vs 80).",
    "encounters": [
      {
        "encounter_index": 1,
        "encounter_date": "2026-07-21",
        "in_window": true,
        "date_aligned": true,
        "matched_anchor": "undersigned",
        "standing": "PREFERRED",
        "screen": { "timing": "IN_WINDOW", "provider": "ALLOWED", "substantiating_note": "PRESENT", "relatedness": "ALIGNED" },
        "alignment": {
          "time_window": "ALIGNED",
          "primary_diagnosis": "ALIGNED",
          "homebound": "ALIGNED",
          "skilled_services": "ALIGNED",
          "provider_eligibility": "ALIGNED",
          "signature": "ALIGNED"
        },
        "score": 85,
        "score_breakdown": { "primary_diagnosis": 30, "homebound": 20, "skilled_services": 10, "time_window": 10, "provider_eligibility": 10, "signature": 5 },
        "criteria_satisfied_count": 6,
        "clinical_relevance": {
          "primary_diagnosis_alignment": { "alignment": "ALIGNED", "strength": "STRONG", "verbiage": "Right hip Intertrochanteric Fracture", "page": 1 },
          "skilled_services_alignment": { "alignment": "ALIGNED", "strength": "ADEQUATE", "verbiage": "PT [SELECTED] Eval & Treat 3 X Week", "page": 1 },
          "homebound_support": { "alignment": "ALIGNED", "strength": "STRONG", "verbiage": "Requires Maximum assistance /tiring effort to leave home", "page": 1 },
          "provider_eligibility_alignment": { "alignment": "ALIGNED", "strength": "WEAK", "verbiage": "Signature of physician: <signature>Mupledi</signature> 7-21", "page": 1 },
          "strength": "ADEQUATE",
          "summary": "Aligned on primary dx and both clinical pillars (skilled PT, homebound both prongs). Provider allowed but signature handwritten without explicit credentials."
        },
        "strengths": ["Aligned on primary dx + both clinical pillars", "Homebound MET (both prongs)", "Date-aligned to the certification"],
        "weaknesses": ["Skilled PARTIAL (SN weak)", "Handwritten signature, no explicit credentials"],
        "risk_flags": [
          { "flag": "WEAK_SIGNATURE", "severity": "warning", "evidence": { "verbiage": "Signature of physician: <signature>Mupledi</signature> 7-21", "page": 1 } }
        ]
      },
      {
        "encounter_index": 2,
        "encounter_date": "2026-07-21",
        "in_window": true,
        "date_aligned": true,
        "matched_anchor": "undersigned",
        "standing": "VIABLE",
        "screen": { "timing": "IN_WINDOW", "provider": "ALLOWED", "substantiating_note": "PRESENT", "relatedness": "ALIGNED" },
        "alignment": {
          "time_window": "ALIGNED",
          "primary_diagnosis": "ALIGNED",
          "homebound": "UNABLE_TO_DETERMINE",
          "skilled_services": "ALIGNED",
          "provider_eligibility": "ALIGNED",
          "signature": "ALIGNED"
        },
        "score": 80,
        "score_breakdown": { "primary_diagnosis": 30, "homebound": 0, "skilled_services": 20, "time_window": 10, "provider_eligibility": 10, "signature": 10 },
        "criteria_satisfied_count": 5,
        "clinical_relevance": {
          "primary_diagnosis_alignment": { "alignment": "ALIGNED", "strength": "STRONG", "verbiage": "Right intertrochanteric hip fracture status post surgical fixation", "page": 2 },
          "skilled_services_alignment": { "alignment": "ALIGNED", "strength": "STRONG", "verbiage": "PT: Gait 70 feet with RW and CGA", "page": 9 },
          "homebound_support": { "alignment": "UNABLE_TO_DETERMINE", "strength": "ABSENT", "verbiage": "No explicit homebound status statement", "page": null },
          "provider_eligibility_alignment": { "alignment": "ALIGNED", "strength": "STRONG", "verbiage": "electronic verified signature, MD, PM&R", "page": 9 },
          "strength": "ADEQUATE",
          "summary": "Ties on primary dx and skilled (STRONG PT), stronger provider, but homebound is UNABLE_TO_DETERMINE — the inpatient rehab note does not assess homebound. Loses on clinical-pillar coverage (1/2)."
        },
        "strengths": ["Skilled MET (STRONG PT)", "High-confidence verified signature with credentials"],
        "weaknesses": ["Homebound UNABLE_TO_DETERMINE (inpatient rehab note)"],
        "risk_flags": [
          { "flag": "SPLIT_STRENGTH", "severity": "warning", "evidence": { "verbiage": "Gait 70 feet with RW and CGA", "page": 9 } }
        ]
      }
    ],
    "comparison": [
      {
        "encounter_index": 2,
        "why_not_selected": "Ties Encounter 1 on primary diagnosis and skilled, and is stronger on skilled and provider confidence, but does NOT substantiate homebound (inpatient rehab note, UNABLE_TO_DETERMINE). Clinical-pillar coverage decides: Encounter 1 covers 2/2, Encounter 2 covers 1/2, so Encounter 1 is the more complete F2F anchor (score 85 vs 80).",
        "evidence": { "verbiage": "No explicit homebound status statement", "page": null }
      }
    ],
    "flags": [
      { "flag": "WEAK_SIGNATURE", "severity": "warning", "evidence": { "verbiage": "Signature of physician: <signature>Mupledi</signature> 7-21", "page": 1 } }
    ],
    "data_quality": {
      "missing_parameters": [],
      "unable_to_determine": ["homebound.f2f_encounters[2].status"],
      "notes": "Both encounters share the certified date (2026-07-21); the date does not differentiate. Encounter 1 selected on clinical-pillar coverage. Encounter 2's homebound is not assessable in its inpatient rehab note; this does not affect the pick because Encounter 1 substantiates homebound directly."
    },
    "excluded_encounters": [],
    "excluded_encounter_indices": []
  },
  "evidence": [],
  "rules_applied": {
    "cms": ["SEL_TIMING_WINDOW", "SEL_ALLOWED_PRACTITIONER", "SEL_SUBSTANTIATING_NOTE", "SEL_CLINICAL_PILLARS", "SEL_DATE_ALIGNMENT", "SEL_WATERFALL", "SEL_SCORE", "SEL_DATE_RECONCILIATION", "SEL_TIEBREAKERS"],
    "client": []
  },
  "reasoning": {
    "status": "SELECTED",
    "summary": "The plan of care certifies home health for a hip fracture (S72.141D). Encounter 1 is a face-to-face visit whose documentation substantiates this certified diagnosis, establishes home confinement (patient unable to leave home without assistance and a two-person transfer), and orders a qualifying skilled service — physical therapy for gait training and strengthening (p.3). Encounter 2 addresses the same fracture and skilled therapy, but as an inpatient rehabilitation note it does not document home confinement, so it does not substantiate the homebound requirement. Encounter 1 therefore provides the most complete and defensible support for the claim. Its signature is handwritten without printed credentials, which the reviewer should confirm, though it does not undermine the clinical support in the record.",
    "evidence_refs": [],
    "missing": null,
    "agency_warnings": []
  }
}
```
