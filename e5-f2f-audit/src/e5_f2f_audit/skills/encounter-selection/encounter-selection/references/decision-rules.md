# Encounter Selection — Decision Rules
#
# How to set `best_encounter_index`, `best_is_date_aligned`, `decision`,
# `selection_method`, and `final_statement` after the ranking (selection-criteria.md)
# and the risk assessment (risk-flags.md). The decision is the auditor's final
# call; it must be defensible and every edge case must resolve to exactly one state.

---

## Decision states

<!-- cms_section_id: SEL_DECISION_STATES -->

| `decision` | When | `best_encounter_index` |
|---|---|---|
| `SELECTED` | A single encounter passes all Stage-1 gates, is `ALIGNED` on primary dx **and** both clinical pillars (homebound + skilled), is the ranked winner, and either **is** the date-aligned encounter or **no** POC anchor exists — with no *critical* risk. A lower-priority `warning` (e.g. `WEAK_SIGNATURE`) is disclosed but does NOT block `SELECTED`. | the winner |
| `NEEDS_HUMAN_REVIEW` | A recommendation exists but confidence is not clean (see escalation triggers): residual clinical-pillar gap on the winner, the winner is not the date-aligned encounter, no primary-dx alignment anywhere, anchor dates disagree, SOC missing, or an unresolved tie. | the recommended winner (never null) |
| `NO_ELIGIBLE_ENCOUNTER` | No encounter passes the Stage-1 gates (all out-of-window, or none has an allowed provider + signed note). | `null` |

`status` (top-level envelope) mirrors `decision`.

`selection_method` records HOW the winner was chosen:
- `date_and_clinical_agree` — the ranked winner **is** the date-aligned encounter.
- `clinical_override_of_date_match` — the ranked winner is a *different* encounter
  than the date-aligned one (always pairs with `NEEDS_HUMAN_REVIEW`).
- `clinical_only_no_anchor` — no POC anchor date exists; ranked purely on clinical.
- `tie_break` — steps 1–3 of the waterfall tied; resolved by the tie-breaker chain.
- `sole_candidate` — only one eligible encounter.

---

## Core decision procedure

<!-- cms_section_id: SEL_DECISION_PROCEDURE -->

1. **Screen** every encounter (Stage-1 gates: window, allowed provider, signed
   note, no relatedness contradiction). If none pass → `NO_ELIGIBLE_ENCOUNTER`,
   `best_encounter_index = null`. Stop.
2. **Date alignment** — compute `date_aligned` per encounter and the transaction
   `date_aligned_encounter` key (`SEL_DATE_ALIGNMENT`). **No early exit.**
3. **Alignment + score** — resolve each parameter to `ALIGNED` / `NOT_ALIGNED` /
   `UNABLE_TO_DETERMINE` (`SEL_ALIGNMENT_MAP`) and compute the weighted `score`
   (`SEL_SCORE`) for every eligible encounter.
4. **Rank** (`SEL_WATERFALL`): primary-dx threshold → clinical-pillar coverage
   (homebound + skilled) → full criteria coverage → tie-breakers. Rank **all**
   eligible encounters even if a date-aligned one looks fully aligned.
5. **Reconcile** the ranked winner against the date-aligned encounter
   (`SEL_DATE_RECONCILIATION`); set `best_is_date_aligned`, `selection_method`,
   and `final_statement`.
6. **Set `decision`** using the escalation triggers below.
7. **Always** produce the full per-encounter report (alignment + score + summary),
   the date-aligned encounter summary, the best-encounter summary, and the
   comparison — regardless of the state.

---

## Escalation triggers → `NEEDS_HUMAN_REVIEW`

<!-- cms_section_id: SEL_ESCALATION -->

Set `NEEDS_HUMAN_REVIEW` (still naming the recommended `best_encounter_index`)
when any of these hold:

- **residual clinical-pillar gap on the winner** — the recommended encounter is
  `NOT_ALIGNED`/`UNABLE_TO_DETERMINE` on **primary dx, homebound, or skilled**
  (even though it out-ranked the alternatives). A valid F2F must substantiate all
  three clinical pillars, so a gap on the *selected* encounter must be reconciled
  by a human. Flag `DECISIVE_DATA_GAP`.
- **`DATE_MATCH_OVERRIDDEN_BY_CLINICAL`** — the ranked winner is NOT the
  date-aligned encounter (`best_is_date_aligned = false`). Recommend the winner;
  flag that the certification would need to document that encounter's date.
- **`PRIMARY_DX_UNALIGNED`** — no encounter is `ALIGNED` on primary dx. Recommend
  the least-weak encounter for the reviewer; there is no confident best.
- **`ANCHOR_DATES_DISAGREE`** — `i_certify` and `undersigned` point to different
  encounters.
- **`SOC_MISSING`** — no valid SOC; timeliness `UNKNOWN` for all; rank clinically
  but escalate.
- **unresolved tie** — steps 1–3 tied and the tie-breaker chain did not resolve
  cleanly (`THIN_MARGIN`), or a clinical trade-off is split across encounters
  (`SPLIT_STRENGTH`) and the margin is close.
- **critical risk on the winner** — any `risk-flags.md` *critical* flag on the
  recommended encounter (e.g. `DATE_ONLY_NO_NOTE`).
- **sole eligible but weak** — only one encounter passes the gates and it has a
  clinical-pillar gap or a critical risk.

If none of the above — the ranked winner passes the gates, is aligned on primary
dx + both clinical pillars, and is the date-aligned encounter (or no anchor
exists) → `SELECTED`. A lower-priority `warning` (e.g. `WEAK_SIGNATURE`, or
`NO_ANCHOR_DATE` when the best is otherwise fully aligned) is disclosed in
`flags[]` but does not block `SELECTED`.

---

## Edge cases (each resolves to exactly one state)

<!-- cms_section_id: SEL_EDGE_CASES -->

1. **No eligible encounters** (all out-of-window / not-allowed / date-only) →
   `NO_ELIGIBLE_ENCOUNTER`, index `null`.
2. **Single eligible encounter, aligned on primary dx + both pillars** →
   `SELECTED`, `sole_candidate`.
3. **Single eligible encounter with a clinical-pillar gap or critical risk** →
   `NEEDS_HUMAN_REVIEW`, `sole_candidate`.
4. **Ranked winner is the date-aligned encounter and aligned on primary dx + both
   pillars** → `SELECTED`, `date_and_clinical_agree`, `best_is_date_aligned = true`.
   (The `bates_donna` case: both aligned on primary dx and skilled and share the
   certified date; Enc 1 also aligns on homebound → 2/2 pillar coverage vs Enc 2's
   1/2 → Enc 1 `SELECTED`; a `WEAK_SIGNATURE` is a disclosed warning.)
5. **Ranked winner out-ranks the date-aligned encounter** → `NEEDS_HUMAN_REVIEW`,
   `clinical_override_of_date_match`, `best_is_date_aligned = false`, flag
   `DATE_MATCH_OVERRIDDEN_BY_CLINICAL`; report both summaries + comparison.
6. **Date-aligned encounter is only *equal*** to the best alternative (not strictly
   out-ranked) → date-aligned wins (tie-breaker), `SELECTED`,
   `date_and_clinical_agree`.
7. **Winner wins the ranking but still has a clinical-pillar gap** (e.g. best
   coverage available is only 1/2 pillars) → `NEEDS_HUMAN_REVIEW`,
   `DECISIVE_DATA_GAP`.
8. **No primary-dx alignment on any encounter** → `PRIMARY_DX_UNALIGNED` →
   `NEEDS_HUMAN_REVIEW` (recommend least-weak; no confident best).
9. **No POC anchor date at all** → `date_aligned_encounter.present = false`,
   `clinical_only_no_anchor`, flag `NO_ANCHOR_DATE`; `SELECTED` if the clinical
   winner is fully pillar-aligned, else `NEEDS_HUMAN_REVIEW`.
10. **Two anchors point to different encounters** (`i_certify` → A, `undersigned`
    → B) → both date-aligned; rank both; flag `ANCHOR_DATES_DISAGREE` →
    `NEEDS_HUMAN_REVIEW`.
11. **Same date on multiple encounters** → the date does not differentiate; the
    ranking picks the winner (no override flag). If the ranking also ties → the
    tie-breaker chain; if still tied → `NEEDS_HUMAN_REVIEW`.
12. **A parameter is `UNABLE_TO_DETERMINE` for every encounter** (e.g. none
    document homebound) → it does not differentiate; the winner carries that gap →
    `NEEDS_HUMAN_REVIEW`, `DECISIVE_DATA_GAP`. Never fill or re-derive it.
13. **Coverage tie, different pillars** (A homebound-only, B skilled-only, each
    1/2) → `SPLIT_STRENGTH`; resolve by full coverage → tie-breakers (score first);
    escalate if close.
14. **High score but primary-dx NOT aligned** → cannot be best; a primary-dx-aligned
    (even lower-scoring) encounter outranks it. If it is the *only* aligned option
    absent, see case 8.
15. **SOC missing/invalid** → `SOC_MISSING`, timeliness `UNKNOWN` all, rank
    clinically but `NEEDS_HUMAN_REVIEW`.
16. **Roster encounter with no verdicts at all** → `NOT_ELIGIBLE` (insufficient
    data); still reported.

---

## Client directives

<!-- cms_section_id: SEL_CLIENT_DIRECTIVES -->

If `clients/<client_name>/client-rules.md` is loaded, a directive may change the
outcome (per the guard in `SKILL.md`). When a client `ELEVATE`/`EXTEND` directive
that *Affects Outcome* changes the winner or forces review, record it in
`reasoning.missing` and `rules_applied.client`, and reflect it in `decision`.
CMS gates are never lowered by a client directive.

---

## Invariants (never violate)

<!-- cms_section_id: SEL_INVARIANTS -->

- Every roster encounter appears in the output, in index order — never dropped.
- `date_aligned_encounter`, `best_is_date_aligned`, and a `score` per encounter are
  **always** emitted.
- `best_encounter_index` is `null` **only** for `NO_ELIGIBLE_ENCOUNTER`.
- `NEEDS_HUMAN_REVIEW` always still names a recommended `best_encounter_index`.
- A primary-dx-unaligned or gate-failing encounter can **never** be the best, no
  matter its score.
- The selection agent never re-validates or re-derives an upstream verdict.
- Never silently override the date-aligned encounter — any override → review.
