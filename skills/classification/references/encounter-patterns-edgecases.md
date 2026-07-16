# Encounter Patterns — Edge Cases

Use this file when the document contains OCR noise, blank pages, embedded orders,
multi-provider same-page notes, face sheets, addenda, or illegible content.

---

## OCR Noise Between Encounters

Scanned documents may contain OCR artifacts (random characters, repeated hyphens,
garbled text) between encounters.

- Include artifact lines in the **preceding** encounter's `line_end` unless they
  form a natural separator
- If they form a natural separator, include them as the `line_start` of the next
  encounter and use them verbatim as `split_anchor`
- If the artifact lines share a page with another encounter, line field rules apply

---

## Embedded Orders at the Bottom of a Clinical Note

Physician orders sometimes appear at the bottom of a progress note or F2F note.

**No own title line** (order appears directly under Assessment/Plan):
→ It is part of the clinical note — do **not** split it as a separate encounter

**Has own title line** (e.g., `PHYSICIAN ORDER`, `HOME HEALTH ORDER`) or is on
a separate page:
→ Classify as a separate encounter using subcategory `home_health_order` or
`physician_order_set`
→ If it shares a page with the preceding note, line fields apply

---

## Multi-Provider Same-Page Notes

Two different providers' notes on the same page = two separate encounters.

Indicators: distinct provider names, different dates, or different note titles.

- Populate line fields for both encounters
- Use the second provider's note title or header line verbatim as `split_anchor`

---

## Patient Information Pages (Face Sheets)

A cover page or face sheet containing only demographics (no clinical narrative):
→ Classify as `administrative_and_legal / face_sheet`
→ Do not skip it — it must appear in the output
→ If it shares a page with another encounter, line fields apply; otherwise `null`

---

## Completely Blank Pages

A page containing only `### Page N` and blank lines:
→ Assign those lines to the **previous** encounter's `line_end` range
→ Do not create a standalone encounter for a blank page

---

## Addenda

An explicit addendum to an earlier encounter:
→ Classify as `addendum / ADDENDUM`
→ Set `parent_encounter_index` to the index of the encounter it amends
→ If the addendum shares a page with any other encounter, line fields are required

---

## Unknown or Illegible Content

Content that cannot be interpreted due to heavy OCR corruption:
→ Classify as `unknown / unknown`
→ Set `classification_confidence = 0.1`
→ Do not skip it — include it in the output
→ If it shares a page with another encounter, line fields apply
→ Add to `classification_notes`: `"Heavy OCR corruption — content unreadable"`
