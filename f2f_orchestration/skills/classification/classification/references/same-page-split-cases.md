# Same-Page Split Cases

Use this file when any `### Page N` number appears in more than one encounter's
`pages` array. Read `references/line-counting-rules.md` before applying any case here.

---

## Case 1 — Both Encounters Entirely on the Same Single Page

**Raw input (every line as Python reads it):**
```
Line  1: ### Page 1
Line  2: 01/15/2026
Line  3:
Line  4: **PROGRESS NOTE**
Line  5: Provider: Dr. Kim, MD
Line  6: Date of Service: 01/15/2026
Line  7:
Line  8: Subjective: Patient reports increased shortness of breath.
Line  9: Objective: HR 88, BP 140/90, SpO2 94% on 2L O2
Line 10: Assessment: CHF exacerbation, COPD stable
Line 11: Plan: Increase diuretic dose; follow up in 2 weeks
Line 12:
Line 13: Signed: Dr. Kim, MD    01/15/2026
Line 14:
Line 15: ─────────────────────────────────────────────
Line 16:
Line 17: **FACE-TO-FACE ENCOUNTER NOTE**
Line 18: Provider: Dr. Kim, MD
Line 19: Date of Service: 01/15/2026
Line 20:
Line 21: Homebound Status: Patient cannot leave without significant assistance
Line 22: due to severe CHF and activity intolerance.
Line 23:
Line 24: Primary Diagnosis: I50.20 — Unspecified systolic heart failure
Line 25: Skilled Services: SN for assessment and medication management
Line 26:
Line 27: Physician Signature: <signature>Dr. Kim, MD</signature>
Line 28: Date: 01/15/2026
Line 29:
Line 30: ### Page 2
```

Page 1 shared by encounters 1 and 2 — line fields required for both.
- Encounter 1: `line_end` = 14 (blank line after signature, before separator)
- Encounter 2: `line_start` = 15 (separator belongs to encounter 2)
- Encounter 2: `line_end` = 29 (blank line after date, before `### Page 2`)

```json
[
  {
    "encounter_index": 1,
    "pages": [1], "page_start": 1, "page_end": 1,
    "line_start": 1, "line_end": 14,
    "split_anchor": "### Page 1"
  },
  {
    "encounter_index": 2,
    "pages": [1], "page_start": 1, "page_end": 1,
    "line_start": 15, "line_end": 29,
    "split_anchor": "─────────────────────────────────────────────"
  }
]
```

---

## Case 2 — Encounter A Ends Mid-Page, Encounter B Starts Mid-Same-Page and Spills to Next Page

**Raw input (every line as Python reads it):**
```
Line  1: ### Page 3
Line  2: 03/10/2026
Line  3:
Line  4: **PHYSICIAN ORDER**
Line  5: Patient: John Doe
Line  6: Date: 03/10/2026
Line  7:
Line  8: Order: Resume home medications as prescribed.
Line  9: Continue PT three times weekly.
Line 10:
Line 11: Physician Signature: <signature>Dr. Adams, MD</signature>
Line 12: Date Signed: 03/10/2026
Line 13:
Line 14: <page_number>2/4</page_number>
Line 15:
Line 16: **FACE-TO-FACE ENCOUNTER NOTE**
Line 17: Provider: Dr. Adams, MD
Line 18: Date of Service: 03/10/2026
Line 19:
Line 20: Homebound Status: Patient unable to ambulate without maximum assistance
Line 21: due to recent right hip replacement surgery.
Line 22:
Line 23: Primary Diagnosis: M16.11 — Primary osteoarthritis, right hip
Line 24:
Line 25: ### Page 4
Line 26: Skilled Services Required: PT for therapeutic exercise and gait training.
Line 27: Nursing for wound assessment and medication management.
Line 28:
Line 29: Physician Signature: <signature>Dr. Adams, MD</signature>
Line 30: Date Signed: 03/10/2026
Line 31:
Line 32: <page_number>3/4</page_number>
```

Page 3 is shared by encounters A and B — line fields required for both.
Page 4 is exclusive to B, but B still requires line fields (propagation rule).
Encounter B's `line_start` is on page 3 and `line_end` is on page 4 —
`line_start` and `line_end` span across the page boundary naturally.

```json
[
  {
    "encounter_index": 1,
    "pages": [3], "page_start": 3, "page_end": 3,
    "line_start": 1, "line_end": 15,
    "split_anchor": "### Page 3"
  },
  {
    "encounter_index": 2,
    "pages": [3, 4], "page_start": 3, "page_end": 4,
    "line_start": 16, "line_end": 32,
    "split_anchor": "**FACE-TO-FACE ENCOUNTER NOTE**"
  }
]
```

