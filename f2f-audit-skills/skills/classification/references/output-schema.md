# Output Schema Reference

## JSON Structure

```json
{
  "total_encounters": 0,
  "encounters": [
    {
      "encounter_index": 1,
      "encounter_category": "",
      "encounter_subcategory": "",
      "encounter_label": "",
      "pages": [],
      "page_start": 1,
      "page_end": 1,
      "line_start": null,
      "line_end": null,
      "split_anchor": null,
      "parent_encounter_index": null,
      "provider_name": null,
      "encounter_date": null,
      "classification_confidence": 0.0,
      "classification_notes": ""
    }
  ]
}
```

## Field Reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `encounter_index` | integer | always | 1-based, sequential, never skip |
| `encounter_category` | string | always | Exact value from taxonomy |
| `encounter_subcategory` | string | always | Exact value from taxonomy |
| `encounter_label` | string | always | Human-readable display label |
| `pages` | integer[] | always | Every page number this encounter touches |
| `page_start` | integer | always | First `### Page N` number of this encounter |
| `page_end` | integer | always | Last `### Page N` number of this encounter |
| `line_start` | integer \| null | same-page only | Null for exclusive-page encounters |
| `line_end` | integer \| null | same-page only | Null for exclusive-page encounters |
| `split_anchor` | string \| null | same-page only | Null for exclusive-page encounters |
| `parent_encounter_index` | integer \| null | addenda only | Index of the encounter this addendum amends |
| `provider_name` | string \| null | always | Null if not found; never infer or hallucinate |
| `encounter_date` | string \| null | always | ISO 8601 `YYYY-MM-DD`; null if not found |
| `classification_confidence` | float | always | 0.0 – 1.0 |
| `classification_notes` | string | always | Brief reasoning; flag TELEHEALTH, ambiguity, low confidence |
