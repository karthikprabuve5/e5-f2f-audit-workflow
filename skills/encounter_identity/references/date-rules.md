# Encounter Date — Extraction Rules
# Source: MBPM Pub. 100-02, Chapter 7, §30.5.1.2 | 42 CFR §424.22

---

## Date Type Priority
<!-- cms_section_id: ED_DATE_PRIORITY -->

Stop at the first match. Do NOT use multiple lower-priority sources if a
higher-priority source exists.

| Priority | Label Pattern | Confidence |
|---|---|---|
| 1 | "Date of Service" / "DOS" / "Date Seen" / "Date of Visit" / "Service Date" | high |
| 2 | "Visit Date" / "Encounter Date" / "Date of Encounter" | high |
| 3 | Unlabeled date in document header — only date on page 1, no competing dates | medium |
| 4 | Date in body text with explicit contextual signal (see below) | medium |
| 5 | Signature date only — no DOS field found anywhere | low |
| 6 | No date found anywhere in the encounter | null — set no_date_found = true |

**Valid body text signals (priority 4):**
"seen today on", "encounter on", "patient presented on", "visit on",
"patient was seen on", "I saw the patient on", "evaluated on"

**NEVER use:**
Dictation dates, transcription dates, print/fax dates, future appointment
dates, or reference dates in body text without a contextual signal above.

---

## Format Normalization
<!-- cms_section_id: ED_NORMALIZATION -->

Always output as ISO 8601: `YYYY-MM-DD`.

| Input Format | Normalized | Notes |
|---|---|---|
| 01/15/2025 | 2025-01-15 | |
| January 15, 2025 | 2025-01-15 | |
| Jan 15, 2025 | 2025-01-15 | |
| 01-15-2025 | 2025-01-15 | |
| 01/15/25 | 2025-01-15 | Two-digit year → 20XX |
| 01/15 | partial_date flag | Year from doc context if available |
| 2025-01-15 | 2025-01-15 | Unchanged |

**Ambiguous format:** Both values ≤ 12 (e.g., 02/03/25 — Feb 3 or Mar 2?)
→ Set `ambiguous_format = true`. Use label context if present; otherwise note the ambiguity.

---

## Date Flags
<!-- cms_section_id: ED_FLAGS -->

| Flag | Condition |
|---|---|
| `ambiguous_format` | Both day and month values ≤ 12; format indeterminate |
| `partial_date` | Day or year missing; cannot fully normalize |
| `multiple_dates_conflict` | Two labeled dates of same type with different values |
| `late_documentation` | Signature date − encounter date > 30 days |
| `no_date_found` | No date of any type found in the encounter |
| `reference_date_only` | Dates present only as past/future references in body text |

---

## Addendum Rule
<!-- cms_section_id: ED_ADDENDUM -->

If "Addendum", "Amendment", or "Correction" appears in the encounter:
- Extract the **original** encounter date as `value`
- Record addendum/amendment date separately as `addendum_date`
- Set `has_addendum = true`

The original encounter date controls all timing validations.

---

## Citation
MBPM Pub. 100-02, Chapter 7, §30.5.1.2 | 42 CFR §424.22(a)(1)(v)
