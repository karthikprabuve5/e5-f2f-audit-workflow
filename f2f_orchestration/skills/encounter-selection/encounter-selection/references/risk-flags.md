# Encounter Selection — Risk Flags
#
# The denial-risk signals that make one encounter less claim-safe than another,
# and that drive escalation to NEEDS_HUMAN_REVIEW (see decision-rules.md). Flags
# are read-only interpretations of already-extracted verdicts — never re-derive.
# Each flag carries a severity: `critical` forces review; `warning` is disclosed
# but does not by itself change the decision.

---

## Flag catalog

<!-- cms_section_id: SEL_RISK_FLAGS -->

| Flag | Severity | Meaning / trigger |
|---|---|---|
| `DATE_ONLY_NO_NOTE` | critical | Encounter is a date referenced on the certification with no substantiating signed clinical note (MAC 5HC01 NOT MET). |
| `DECISIVE_DATA_GAP` | critical | A clinical pillar for the winner is missing or `UNABLE_TO_DETERMINE` (primary dx, homebound, or skilled). |
| `PRIMARY_DX_UNALIGNED` | critical | No encounter is `ALIGNED` on primary diagnosis with the POC anchor — F2F substantiation for the claim is not established. |
| `SOC_MISSING` | critical | No valid `soc_date` supplied → timeliness `UNKNOWN` for all encounters. |
| `DATE_MATCH_OVERRIDDEN_BY_CLINICAL` | critical | The ranked winner differs from the date-aligned encounter — certification would need re-documentation. |
| `NO_ANCHOR_DATE` | warning | No POC anchor date (`i_certify` / `undersigned`) exists → date alignment cannot be computed; ranked purely on clinical relevance. |
| `OUT_OF_WINDOW` | critical | Encounter date falls outside the 90/30 window → `NOT_ELIGIBLE`. |
| `PROVIDER_NOT_ALLOWED` | critical | `is_allowed = false` or signature absent → `NOT_ELIGIBLE`. |
| `THIN_MARGIN` | warning | Top two eligible encounters within one strength band on the deciding priority. |
| `SPLIT_STRENGTH` | warning | Highest-priority strengths split across encounters. |
| `ANCHOR_DATES_DISAGREE` | warning | `i_certify` and `undersigned` anchors point to different encounters. |
| `RELATEDNESS_UNCLEAR` | warning | `primary_hh_reason…alignment.status = NOT_DOCUMENTED`/unclear (weakens, not disqualifying). |
| `WEAK_SIGNATURE` | warning | Handwritten / uncredentialed / `single_electronic` / medium-low provider confidence. |
| `TIMELINESS_UNKNOWN` | warning | Encounter date missing for a specific encounter (but SOC present). |

---

## How flags interact with the decision

<!-- cms_section_id: SEL_RISK_DECISION -->

- Any `critical` flag on the **recommended** `best_encounter_index` →
  `NEEDS_HUMAN_REVIEW` (decision-rules.md `SEL_ESCALATION`).
- `critical` flags that make an encounter `NOT_ELIGIBLE` (`OUT_OF_WINDOW`,
  `PROVIDER_NOT_ALLOWED`, `DATE_ONLY_NO_NOTE` when date-only) remove it from
  ranking — unless it is the sole candidate.
- `warning` flags are disclosed in the encounter's `risk_flags` and in the
  inference summary, and are used to break or explain close calls, but do not by
  themselves change a clean `SELECTED`.
- Every flag placed on an encounter must cite the underlying evidence
  (`verbiage` + `page`) copied from the merge_encounters input.

---

## Placement in output

<!-- cms_section_id: SEL_RISK_PLACEMENT -->

- Per-encounter flags → `encounters[i].risk_flags` (list of `{ flag, severity,
  evidence }`).
- Flags that drive the final decision are also surfaced at the top level under
  `result.flags` so a reviewer sees them without scanning every encounter.
