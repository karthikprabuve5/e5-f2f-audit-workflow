# Encounter Patterns — Exclusive Page Encounters

Use this file when all encounters start at page boundaries and no page is
shared between two or more encounters. All line fields are `null`.

---

## Pattern 1 — Single Encounter, Single Exclusive Page

**Raw input (every line as Python reads it):**
```
Line  1: ### Page 1
Line  2: 03/10/2026
Line  3:
Line  4: **FACE-TO-FACE ENCOUNTER NOTE**
Line  5: Provider: Dr. Jane Smith, MD
Line  6: Date of Service: 03/10/2026
Line  7:
Line  8: Homebound Status: Patient unable to leave home without considerable
Line  9: effort due to severe COPD requiring supplemental oxygen at all times.
Line 10:
Line 11: Primary Diagnosis: J44.1 — COPD with acute exacerbation
Line 12:
Line 13: Skilled Services Required: Skilled nursing for medication management.
Line 14:
Line 15: Physician Signature: <signature>Dr. Jane Smith, MD</signature>
Line 16: Date Signed: 03/10/2026
Line 17:
Line 18: <page_number>1/1</page_number>
```

Page 1 belongs exclusively to this encounter — no other encounter touches it.

**Output:**
```json
{
  "encounter_index": 1,
  "encounter_category": "certification_and_assessment",
  "encounter_subcategory": "face_to_face_note",
  "encounter_label": "Face-to-Face Encounter Note",
  "pages": [1],
  "page_start": 1,
  "page_end": 1,
  "line_start": null,
  "line_end": null,
  "split_anchor": null,
  "parent_encounter_index": null,
  "provider_name": "Dr. Jane Smith, MD",
  "encounter_date": "2026-03-10",
  "classification_confidence": 0.98,
  "classification_notes": "Explicit F2F title; homebound documented; skilled services; signed"
}
```

---

## Pattern 2 — Single Encounter, Multiple Exclusive Pages

**Raw input (abbreviated):**
```
Line  1: ### Page 1
Line  2: 02/20/2026
Line  3:
Line  4: **HISTORY AND PHYSICAL**
Line  5: Provider: Dr. Robert Lee, MD
Line  6: Date: 02/20/2026
Line  7:
Line  8: HPI: Patient presents with worsening dyspnea on exertion.
...
Line 38: <page_number>1/2</page_number>
Line 39:
Line 40: ### Page 2
Line 41: Assessment and Plan:
Line 42: 1. CHF — continue diuresis
...
Line 67: Electronically signed by: Dr. Robert Lee, MD
Line 68: Date: 02/20/2026
Line 69:
Line 70: <page_number>2/2</page_number>
```

Pages 1 and 2 both belong exclusively to this encounter.

**Output:**
```json
{
  "encounter_index": 1,
  "encounter_category": "history_and_physical",
  "encounter_subcategory": "comprehensive_h_and_p",
  "encounter_label": "Comprehensive History and Physical",
  "pages": [1, 2],
  "page_start": 1,
  "page_end": 2,
  "line_start": null,
  "line_end": null,
  "split_anchor": null,
  "parent_encounter_index": null,
  "provider_name": "Dr. Robert Lee, MD",
  "encounter_date": "2026-02-20",
  "classification_confidence": 0.97,
  "classification_notes": "Full H&P across two pages; no other encounter shares pages 1 or 2"
}
```

---

## Pattern 3 — Multiple Encounters All at Page Boundaries

**Scenario:** 5-page packet. Discharge summary (pages 1–2), post-op follow-up
(page 3), F2F note (pages 4–5). Every encounter starts at a `### Page N`
boundary. No page is shared.

| Index | Subcategory | pages | line_start | line_end | split_anchor |
|-------|-------------|-------|-----------|---------|-------------|
| 1 | `discharge_summary` | [1, 2] | null | null | null |
| 2 | `post_operative_follow_up` | [3] | null | null | null |
| 3 | `face_to_face_note` | [4, 5] | null | null | null |

All encounters start at page boundaries with no sharing — all line fields `null`.
