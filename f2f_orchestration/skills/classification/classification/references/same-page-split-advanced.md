# Same-Page Split Cases — Advanced Scenarios

Use this file for cross-page spanning encounters and complex same-page splits
involving three or more encounters. Read `references/line-counting-rules.md`
and `references/same-page-split-cases.md` before applying cases here.

---

## Case 3 — Encounter A Ends Mid-Page, Encounter B Starts Mid-Same-Page and Spills Forward

**Raw input (every line as Python reads it):**
```
Line  1: ### Page 1
Line  2: 02/20/2026
Line  3:
Line  4: **HISTORY AND PHYSICAL**
Line  5: Provider: Dr. Lee, MD
Line  6: Date: 02/20/2026
Line  7:
Line  8: HPI: Patient presents with worsening dyspnea on exertion.
Line  9: PMH: CHF, COPD, Hypertension.
Line 10:
Line 11: <page_number>1/4</page_number>
Line 12:
Line 13: ### Page 2
Line 14: Assessment and Plan:
Line 15: 1. CHF — continue diuresis
Line 16: 2. COPD — continue inhalers
Line 17:
Line 18: Electronically signed by: Dr. Lee, MD
Line 19: Date: 02/20/2026
Line 20:
Line 21: <page_number>2/4</page_number>
Line 22:
Line 23: **DISCHARGE SUMMARY**
Line 24: Provider: Dr. Lee, MD
Line 25: Date of Service: 02/20/2026
Line 26:
Line 27: Hospital Course: Patient admitted 02/15/2026 for acute CHF exacerbation.
Line 28:
Line 29: ### Page 3
Line 30: Condition at Discharge: Stable
Line 31: Discharge Disposition: Home with Home Health
Line 32:
Line 33: Discharge Diagnosis: I50.20 — Unspecified systolic heart failure
Line 34:
Line 35: Electronically signed by: Dr. Lee, MD
Line 36: Date: 02/20/2026
Line 37:
Line 38: <page_number>3/4</page_number>
```

Page 2 is shared by encounters A and B — line fields required for both.
- Encounter A: `line_start` on page 1, `line_end` on page 2 — spans pages naturally
- Encounter B: `line_start` on page 2, `line_end` on page 3 — spans pages naturally
- Page 1 is exclusive to A, but A still requires line fields (page 2 is shared)
- Page 3 is exclusive to B, but B still requires line fields (page 2 is shared)

```json
[
  {
    "encounter_index": 1,
    "pages": [1, 2], "page_start": 1, "page_end": 2,
    "line_start": 1, "line_end": 22,
    "split_anchor": "### Page 1"
  },
  {
    "encounter_index": 2,
    "pages": [2, 3], "page_start": 2, "page_end": 3,
    "line_start": 23, "line_end": 38,
    "split_anchor": "**DISCHARGE SUMMARY**"
  }
]
```

---

## Case 4 — Three Encounters on the Same Single Page

Page N is shared by all three encounters — line fields required for all three.

- Encounter 1: starts at the `### Page N` header line
- Encounter 2: starts at the separator or title that begins it
- Encounter 3: starts at its own separator or title

| Index | pages | line_start | line_end | split_anchor |
|-------|-------|-----------|---------|-------------|
| 1 | [N] | first line of page N | last line before separator | `"### Page N"` |
| 2 | [N] | separator line | last line before next title | verbatim separator |
| 3 | [N] | title line of encounter 3 | last line of page N content | verbatim title |

**Key rule:** Each encounter's `line_end` is the last line before the next
encounter's separator or title. The separator or title belongs to the following
encounter — it is that encounter's `line_start` and `split_anchor`.

---

## Case 5 — Encounter A Ends on Page N, Encounter B Entirely on Page N, Encounter C Starts on Page N and Spills Forward

Page N is shared by A, B, and C — line fields required for all three.

- Encounter A: `pages` includes pages before N; `line_end` lands on page N
- Encounter B: `pages: [N]`; entirely within page N
- Encounter C: `pages` includes N and pages after; `line_start` is on page N,
  `line_end` is on a later page — spans across the page boundary naturally

| Index | pages | line_start | line_end | Notes |
|-------|-------|-----------|---------|-------|
| A | [..., N] | on earlier page | on page N | ends mid-page N |
| B | [N] | on page N | on page N | entirely on page N |
| C | [N, ...] | on page N | on later page | starts mid-page N, spills forward |

**Propagation applies to A and C:** Even though A's earlier pages and C's later
pages are exclusive, both still require line fields because page N is shared.

---

## Case 6 — Encounter Straddles Three or More Pages, Sharing First and Last with Others

Encounter B spans pages 1–3. Page 1 is shared with encounter A (which ends mid-page 1).
Page 3 is shared with encounter C (which starts mid-page 3). Page 2 is exclusive to B.

- B requires line fields because pages 1 and 3 are shared (propagation rule)
- B's `line_start` is on page 1 and `line_end` is on page 3 — spans naturally
- Page 2 being exclusive to B does not exempt B from line fields

| Index | pages | line_start | line_end | split_anchor |
|-------|-------|-----------|---------|-------------|
| A | [1] | line 1 | on page 1 | `"### Page 1"` |
| B | [1, 2, 3] | on page 1 | on page 3 | verbatim title/separator on page 1 |
| C | [3] | on page 3 | on page 3 | verbatim title/separator on page 3 |

**Note for encounter C:** If C does not spill beyond page 3, its `pages: [3]`.
If C spills to page 4 and page 4 is exclusive to C, `pages: [3, 4]` but line
fields are still required because page 3 is shared (propagation rule).
