# Line Counting Rules

## How to Count Lines

Count every line in the document sequentially from line 1, exactly as
Python `readlines()` would. The counter never resets at a new page.

**Every line counts — no exceptions:**

| Line type | Counted? |
|-----------|---------|
| `### Page N` header line | ✅ yes |
| Blank / empty line | ✅ yes |
| HTML tag lines (`<table>`, `<tr>`, `<td>`, `</table>` etc.) | ✅ yes |
| `<watermark>`, `<page_number>`, `<signature>`, `<img>` tag lines | ✅ yes |
| Separator lines (`---`, `────────`) | ✅ yes |
| Repeated header/footer lines (patient name, MRN, URL, printed-at) | ✅ yes |

## When Line Fields Are Required

| Condition | line_start / line_end / split_anchor |
|-----------|--------------------------------------|
| A `### Page N` number appears in more than one encounter's `pages` array | **Required** — populate for every encounter touching that shared page |
| All of an encounter's pages are exclusive to it | `null` for all three |

**Propagation rule:** If *any* page in an encounter's `pages` array is shared
with another encounter, that encounter requires line fields — even if its other
pages are exclusive.

## line_start and line_end

- `line_start`: document-level line number of the first line of the encounter (inclusive)
- `line_end`: document-level line number of the last line of the encounter (inclusive)
- These are **always document-level** — they naturally span across page boundaries
  when an encounter crosses pages. No special handling is needed.
- Lines must not overlap: if encounter N ends at line X, encounter N+1 starts at X+1

## Boundary Ownership

| Content | Belongs to |
|---------|-----------|
| Blank line after a signature, before a separator | Preceding encounter (`line_end`) |
| Separator line (`---`, `────────`) between two encounters | Following encounter (`line_start` and `split_anchor`) |
| `<page_number>` tag line at bottom of page | Current encounter (`line_end`) |
| `<watermark>` tag line | Current encounter |
| Blank line immediately before `### Page N` | Preceding encounter (`line_end`) |
| `### Page N` header line itself | The encounter that starts on that page (`line_start`) |
| Repeated footer lines (MRN, URL, printed-at) | Current encounter — do not trigger a new one |

## split_anchor

- First encounter on a shared page → verbatim `### Page N` header string
- Subsequent encounters on the same shared page → verbatim first non-blank
  distinguishing line of that encounter (separator, title heading, or note header)
- Encounter on an exclusive page → `null`
