# Encounter Selection — Ranking Criteria
#
# How to weigh the six selection parameters to choose the best encounter. Read
# each upstream verdict as an ALIGNMENT signal, compute date alignment against the
# POC, score every encounter, then rank. Never re-derive a verdict — only compare
# each encounter's already-decided verdicts against the POC and across encounters
# (see cms-selection-rules.md).
#
# CORE PRINCIPLE (aligned with prebill F2F auditor + MAC-survival logic):
# a valid F2F must substantiate the CMS clinical pillars — the primary reason for
# home health, the need for skilled care, and homebound status (42 CFR
# §424.22(a)(1)(v); MBPM Ch.7 §30.5.1). So the best encounter is the one that,
# after passing the hard eligibility gates, ALIGNS on the primary diagnosis
# (a dominant threshold) and then covers the most clinical pillars. The certified
# date (i_certify / undersigned) identifies WHICH encounter the certification
# attests to — it is computed and reported for every encounter, is never an early
# exit, and constrains overrides (never a silent swap). A weighted 0–100 score is
# computed for transparency and used only as an advisory tie-breaker.

---

## Two stages: screen, then rank (never exit early on a date match)

<!-- cms_section_id: SEL_STAGE_MODEL -->

**Stage 1 — Eligibility screen (hard gates).** An encounter must be a claim-viable
F2F to compete at all. Gates:
- **Timing** — `encounter_date` inside the 120-day window `[SOC−90, SOC+30]`
  (inclusive). `OUT_OF_WINDOW` → `NOT_ELIGIBLE`. No date / no SOC → `UNKNOWN`
  (held as a risk, not a silent pass).
- **Allowed practitioner** (CY2026 definition) —
  `eligible_provider.conducting_provider.is_allowed = true`. Not allowed → gate
  fail → `NOT_ELIGIBLE`. Do NOT down-rank an encounter merely because a provider
  other than the certifier performed it (CY2026 decoupled performer from certifier
  — see cms-selection-rules.md `SEL_ALLOWED_PRACTITIONER`).
- **Substantiating signed note** — the encounter must be backed by an actual signed
  clinical note (signature *present*), not just a date referenced on the
  certification. A date-only encounter fails the gate (`DATE_ONLY_NO_NOTE`).
- **Relatedness** — a clear contradiction (`primary_hh_reason…alignment.status`
  contradicts the POC) → `NOT_ELIGIBLE`; `NOT_DOCUMENTED`/unclear weakens but does
  not alone disqualify.

Signature *strength* (verified vs handwritten) is **not** a gate — it is a scored
tie-breaker. An encounter failing a Stage-1 gate is `NOT_ELIGIBLE` and cannot be
the winner unless it is the *only* encounter (then → `NEEDS_HUMAN_REVIEW`).

**Stage 2 — Rank every eligible encounter (double-check, no early exit).** Compute
date alignment and the score for *every* encounter, then rank on the priority
order in `SEL_WATERFALL`. Even when a date-aligned encounter looks fully aligned,
still rank all encounters and confirm it is genuinely the best before selecting it.

---

## Date alignment against the POC (computed for every encounter)

<!-- cms_section_id: SEL_DATE_ALIGNMENT -->

A "date match" = an encounter whose `encounter_date` **exactly matches** a POC
anchor (`timely_encounter.poc_485.i_certify.encounter_date` or
`undersigned.encounter_date`). Exact match only — never fuzzy.

For each encounter set `date_aligned` (bool) and `matched_anchor`
(`i_certify` | `undersigned` | null). Emit a transaction-level key:

```
date_aligned_encounter: { present: bool, encounter_index: N | null,
                          matched_anchor: "i_certify" | "undersigned" | null }
```

Rules:
- Matching **either** anchor counts as date-aligned (both are certification-
  documented encounter dates).
- If `i_certify` and `undersigned` point to **different** encounters →
  `present = true`, record both in the report, and raise `ANCHOR_DATES_DISAGREE`
  → `NEEDS_HUMAN_REVIEW`.
- If **no POC anchor dates** exist → `present = false`, raise `NO_ANCHOR_DATE`, and
  rank purely on clinical relevance (`selection_method = clinical_only_no_anchor`).
- Date alignment is **reported and used in reconciliation and tie-breaking — it is
  never a gate and never an early exit.**

---

## Ranking waterfall (priority order)

<!-- cms_section_id: SEL_WATERFALL -->

Among eligible encounters, rank in this strict order. Earlier steps dominate;
later steps only break ties left by earlier ones.

### 1. Primary-diagnosis alignment — DOMINANT THRESHOLD  (`primary_hh_reason`)
Resolve each encounter to `ALIGNED` / `NOT_ALIGNED` / `UNABLE_TO_DETERMINE`
(`SEL_ALIGNMENT_MAP`).
- An encounter **not `ALIGNED`** on primary dx **cannot be the best encounter**,
  regardless of score or any other parameter. Primary-dx-aligned encounters rank
  above all non-aligned ones.
- If **some** align → only they compete for `best`.
- If **no** encounter aligns → `PRIMARY_DX_UNALIGNED` → `NEEDS_HUMAN_REVIEW`
  (recommend the least-weak encounter for the reviewer; do not present a confident
  best).

### 2. Clinical-pillar coverage  (`homebound` + `skilled_services`)
Among primary-dx-aligned encounters, prefer the one aligning on **more of the two
clinical pillars** {Homebound, Skilled}: 2 aligned > 1 > 0. This is where an
encounter that substantiates homebound beats one that does not, all else equal.

### 3. Full criteria coverage (of 6)
If pillar coverage ties, prefer the encounter satisfying the **higher number** of
all six parameters (Time, Primary Dx, Homebound, Skilled, Provider, Signature).

### 4. Tie-breakers
See `SEL_TIEBREAKERS` — weighted score (advisory) → certified-date match →
signature strength → closest-to-SOC → documentation defensibility.

The result per encounter: an `alignment` profile (per-parameter status), a
`score` (0–100), a `standing`, and a `clinical_relevance` band.

---

## Weighted encounter score (advisory, 0–100)

<!-- cms_section_id: SEL_SCORE -->

Compute a transparency score for **every** encounter. It is **advisory** — it is
used only as the first tie-breaker in `SEL_TIEBREAKERS` and is surfaced in the
output; it **never** overrides the hard gates or the primary-dx threshold. A
high-scoring encounter that is not `ALIGNED` on primary dx still cannot be best.

| Parameter | Weight | Credit rule |
|---|---|---|
| Primary Diagnosis | 30 | `ALIGNED` = 30; `NOT_ALIGNED`/`UNABLE_TO_DETERMINE` = 0 |
| Homebound | 20 | `MET` = 20; `UNABLE_TO_DETERMINE`/`NOT_MET` = 0 |
| Skilled Services | 20 | `MET` = 20; `PARTIAL` (≥1 justified POC discipline) = 10; none = 0 |
| Time Window | 10 | in-window = 10; else 0 |
| Provider Eligibility | 10 | `is_allowed = true` = 10; else 0 |
| Signature | 10 | verified + explicit credentials = 10; handwritten/weak/`single_electronic` = 5; absent = 0 |

Emit `score` and `score_breakdown` (per-parameter points) per encounter, and the
winner's `best_encounter_score` at the top of `result`.

---

## Certified-date reconciliation & the final statement

<!-- cms_section_id: SEL_DATE_RECONCILIATION -->

After the full ranking picks a top encounter, reconcile it against the
date-aligned encounter and set `best_is_date_aligned` + `final_statement`:

1. **Top-ranked IS the date-aligned encounter** → `best_is_date_aligned = true`,
   `selection_method = date_and_clinical_agree`. Statement: *"The date-aligned
   encounter (idx N) is the best encounter."* Highest confidence.
2. **A different encounter out-ranks the date-aligned one** (aligns on a higher
   priority the date-aligned one lacks, or clearly higher coverage) →
   `best_is_date_aligned = false`,
   `selection_method = clinical_override_of_date_match`, flag
   `DATE_MATCH_OVERRIDDEN_BY_CLINICAL` → `NEEDS_HUMAN_REVIEW`. **Never silently
   swap** — the certification would need to document the chosen encounter's date.
   Report **both** encounters' alignment summaries and compare them.
3. **Date-aligned encounter is only *equal*** to the best alternative (not strictly
   out-ranked) → the date-aligned encounter wins (certification tie-breaker),
   `best_is_date_aligned = true`.
4. **No date-aligned encounter** → the clinical leader is `best_encounter_index`,
   `selection_method = clinical_only_no_anchor`, flag `NO_ANCHOR_DATE`.

Always output the date-aligned encounter's summary AND the best encounter's
summary; when they differ, output the comparison of both.

---

## Tie-breakers (only when steps 1–3 of the waterfall are tied)

<!-- cms_section_id: SEL_TIEBREAKERS -->

Reach these only when primary-dx alignment, clinical-pillar coverage, and full
criteria coverage are all equal. Apply in order; stop at the first that resolves:
1. **Weighted score (advisory)** — higher `score` (see `SEL_SCORE`) wins.
2. **Certified-date match** — the date-aligned encounter wins (strongest legal
   link to the certification).
3. **Signature / provider strength** — `electronic_verified` + explicit
   credentials + `performed_by_match` + `overall_confidence = high` > handwritten /
   uncredentialed / `single_electronic` / medium-low confidence.
4. **Closest to SOC** — the encounter nearest the start-of-care date is the
   tightest clinical tie to the episode. (CMS notes a *new* F2F is required if the
   patient's condition changed — so "closest to SOC / most representative of the
   current condition" is the defensible reason to prefer one date, not "newest
   wins" as a blanket rule.)
5. **Documentation defensibility** — fewest gaps: `reasoning.missing` empty, no
   `UNABLE_TO_DETERMINE` among the six parameters, every cited claim carries
   `verbiage` + `page`. Prefer the encounter an ADR reviewer could least easily
   challenge.

If still tied after all five → `NEEDS_HUMAN_REVIEW` (`THIN_MARGIN`).

---

## Reading a verdict into an alignment status

<!-- cms_section_id: SEL_ALIGNMENT_MAP -->

Resolve each parameter to an alignment (this drives the ranking and the score):

| Parameter | `ALIGNED` | `NOT_ALIGNED` | `UNABLE_TO_DETERMINE` |
|---|---|---|---|
| Time Window | `encounter_date` ∈ `[SOC−90, SOC+30]` | outside the window | no date / no SOC |
| Primary dx | `alignment.status = ALIGNED` (same condition as POC anchor) | contradicts / different condition | `NOT_DOCUMENTED` / absent |
| Skilled | `status = MET`, or `PARTIAL` with ≥1 justified POC-ordered discipline | no POC discipline justified / no match | verdict missing |
| Homebound | `status = MET` | `status = NOT_MET` | `UNABLE_TO_DETERMINE` / absent |
| Provider | `is_allowed = true` + signature present | `is_allowed = false` / no signature | confidence undeterminable |
| Signature | signed note present (any) | no signature | undeterminable |

## Reading a verdict into a strength signal (tie-breaker / descriptive only)

<!-- cms_section_id: SEL_STRENGTH_MAP -->

Strength fills the descriptive `clinical_relevance` band and feeds the score's
partial-credit rules; it never skips the primary-dx threshold or coverage steps.

| Signal | Means |
|---|---|
| `STRONG` | qualifying verdict + strong upstream evidence (`signal_strength: STRONG`, both prongs, ALIGNED same-condition primary dx, verified signature) |
| `ADEQUATE` | qualifying verdict but with medium evidence or a minor gap |
| `WEAK` | borderline / `PARTIAL` / low confidence / weak evidence / date-only note |
| `ABSENT` | `UNABLE_TO_DETERMINE`, `NOT_MET`, missing, or `OUT_OF_WINDOW` |

Roll the parameter alignments into a `standing`:
- `PREFERRED` — passes the gates, aligned on primary dx, and is the ranked winner
  (top clinical-pillar coverage / score).
- `VIABLE` — passes the gates and aligned on primary dx; competitive but not the winner.
- `WEAK` — passes the gates only marginally (multiple `NOT_ALIGNED`/`ABSENT`).
- `NOT_ELIGIBLE` — fails a Stage-1 gate.

---

## Split-coverage awareness

<!-- cms_section_id: SEL_SPLIT -->

If the clinical pillars are **split across encounters** (e.g. one aligns on
homebound, another on skilled — each 1/2) the coverage step ties; fall to full
criteria coverage, then the tie-breakers (weighted score first). Flag
`SPLIT_STRENGTH` so the reviewer sees the trade-off, and disclose it in the
inference summary. Never average two encounters into a false single winner; name
the ranked leader and report both. A higher-priority step is never overridden by a
lower one (an encounter cannot win on score alone if it loses the primary-dx
threshold or clinical-pillar coverage).
