# Encounter Selection — CMS Rules
# Source: 42 CFR §424.22(a)(1)(v) | MBPM Pub. 100-02, Chapter 7, §30.5.1
# CY2026 HH PPS Final Rule (90 FR, Dec 2, 2025), effective Jan 1, 2026
# Program Integrity Manual (Pub. 100-08), Chapter 6, §6.2.1 / §6.2.3
#
# Selection does NOT re-apply the upstream CMS eligibility rules. Provider
# eligibility, primary-reason relatedness, the homebound two-prong test, and
# skilled necessity are already applied by the owning F2F skills and baked into
# the extracted verdicts in the merge_encounters input. The selection agent COMPARES
# those already-validated verdicts — it never re-judges them. The only CMS rule
# owned originally here is the 90/30-day timing window, because it needs the
# runtime start-of-care (SOC) date, which the upstream skills explicitly defer.
# All ranking logic lives in selection-criteria.md.

---

## Selection scope

Selection weighs exactly five parameters from the `merge_encounters` input:

1. `timely_encounter`
2. `eligible_practitioners`
3. `primary_hh_reason`
4. `skilled_services`
5. `homebound`

<!-- cms_section_id: SEL_OUT_OF_SCOPE -->
**Out of scope — never used for selection:** `telehealth`, `inpatient`, and
`surgical_note`. These are validated **downstream** when the final CMS audit
results are generated. Ignore them here even if present, and never let them
influence the chosen encounter or the inference summary.

---

## SEL_CLINICAL_PILLARS — What a valid F2F encounter must substantiate
<!-- cms_section_id: SEL_CLINICAL_PILLARS -->
<!-- element_type: CRITERIA -->

Authority: 42 CFR §424.22(a)(1)(v); MBPM Pub. 100-02, Chapter 7, §30.5.1.

The F2F encounter documentation must substantiate the clinical findings that
support home-health eligibility — specifically the three **clinical pillars**:

1. **Primary reason for home health** — the encounter is *related to the primary
   reason* the patient requires home health (the POC certifying condition).
2. **Need for skilled care** — the encounter supports the medical necessity of the
   skilled services ordered on the POC.
3. **Homebound status** — the encounter corroborates that the patient is confined
   to the home.

**Selection consequence (why the alignment waterfall is ordered this way):**
because all three pillars are required elements of a defensible F2F, the best
encounter is the one that *aligns* on the most of them, weighed in priority order
(primary reason → skilled → homebound; provider eligibility as the tie-breaking
fourth signal). An encounter that fails to substantiate a pillar is a weaker
claim anchor; if even the *selected* encounter leaves a pillar
`NOT_ALIGNED`/`UNABLE_TO_DETERMINE`, that gap must be reconciled by a human before
billing (see `selection-criteria.md` `SEL_WATERFALL` and `decision-rules.md`
`SEL_ESCALATION`). Selection never re-judges a pillar verdict — it only reads the
already-decided verdict and compares alignment across encounters.

---

## SEL_TIMING_WINDOW — 90/30-Day Timing Window (the only CMS rule owned here)
<!-- cms_section_id: SEL_TIMING_WINDOW -->
<!-- element_type: CRITERIA -->

Authority: 42 CFR §424.22(a)(1)(v); MBPM Pub. 100-02, Chapter 7, §30.5.1.
Upstream `encounter-identity` extracts the encounter date but "does not validate
the timing window" — this skill applies it, because it needs the SOC date (a
runtime input supplied in the system prompt).

The F2F encounter must occur within the window (a **120-day span**):
- **No more than 90 days BEFORE** the start of care, **through**
- **No more than 30 days AFTER** the start of care.

Compute: `window.start = soc_date − 90 days`, `window.end = soc_date + 30 days`
(boundaries inclusive). This is the hard timing **gate** — an out-of-window
encounter is `NOT_ELIGIBLE`.

Read `timely_encounter.f2f_encounters[i].encounter_date` and classify:
- date within `[window.start, window.end]` → **IN_WINDOW**
- date outside the window → **OUT_OF_WINDOW** (not claim-eligible on timing)
- no encounter date, or no `soc_date` supplied → **UNKNOWN** (a selection risk; never guess)

---

## SEL_ALLOWED_PRACTITIONER — Who may perform the F2F (CY2026 definition)
<!-- cms_section_id: SEL_ALLOWED_PRACTITIONER -->
<!-- element_type: CRITERIA -->

Provider eligibility is decided upstream (`eligible_practitioners`); selection
only reads that verdict. Interpret it under the **CY2026** rule so the read is
correct:

The CY2026 HH PPS Final Rule revised §424.22(a)(1)(v)(A) and **removed**
§424.22(a)(1)(v)(C). The F2F encounter may now be performed by **any** physician,
nurse practitioner (NP), clinical nurse specialist (CNS), physician assistant
(PA), or certified nurse-midwife (CNM) as defined at §484.2 — the performer **no
longer needs to be the certifying practitioner** or an acute/post-acute physician
with privileges. The financial-relationship-with-HHA exclusion still applies.

**Selection consequence:** because CMS decoupled the F2F *performer* from the
*certifier*, an encounter performed by a provider other than the certifier is
fully eligible. Selecting the most clinically defensible encounter is therefore
CMS-aligned — do not down-rank an encounter merely because a different allowed
provider performed it.

An encounter whose upstream verdict is `is_allowed = false` (or whose signature
is absent) fails this gate → `NOT_ELIGIBLE`.

---

## SEL_SUBSTANTIATING_NOTE — A signed clinical note must exist
<!-- cms_section_id: SEL_SUBSTANTIATING_NOTE -->
<!-- element_type: CRITERIA -->

MACs require the **actual clinical note** for the F2F encounter visit — a date
referenced on the certification with **no substantiating, signed clinical note**
is a classic NOT MET (CGS denial reason 5HC01; PIM Pub. 100-08 §6.2.1/§6.2.3).

For selection, read this from the already-extracted verdicts (do not re-derive):
an encounter must have a documented, signed encounter note behind it —
`eligible_practitioners…signature` present and the encounter substantiated in
`primary_hh_reason` / `skilled_services` evidence. An encounter that is only a
**date with no substantiating note** is a selection risk (see `risk-flags.md`)
and cannot be `PREFERRED`; if it is the only candidate → `NEEDS_HUMAN_REVIEW`.

---

## SEL_CERTIFIED_ENCOUNTER_IDENTITY — Date match = which encounter was certified
<!-- cms_section_id: SEL_CERTIFIED_ENCOUNTER_IDENTITY -->
<!-- element_type: CRITERIA -->

The certifying practitioner "must document the date of the encounter as part of
the certification" (§424.22(a)(1)(v)). The POC anchor dates
(`timely_encounter.poc_485.i_certify.encounter_date` /
`undersigned.encounter_date`), when present, therefore **identify the encounter
the certification actually attests to** — not mere corroboration.

**Selection consequence:** an F2F encounter whose date **exactly matches** a POC
anchor is the *certified encounter of record*. Date alignment is **computed for
every encounter and reported** (the `date_aligned_encounter` key) — it is never a
gate and never an early exit. Clinical relevance still leads the ranking (see
`selection-criteria.md`), but the selection agent must **never silently swap** to
a clinically stronger encounter that carries a *different* date than the one on
the certification — doing so would create a certification-linkage gap a MAC would
flag. When the ranked winner points away from the date-aligned encounter, that is
a documentation action → `NEEDS_HUMAN_REVIEW` (see `decision-rules.md`), not an
auto-override.

---

## Everything else is already validated upstream

<!-- cms_section_id: SEL_UPSTREAM_VALIDATED -->

Provider eligibility, primary-reason relatedness, homebound, and skilled
necessity are already decided by the owning F2F skills and carried as verdicts +
evidence in the merge_encounters input. The selection agent reads those verdicts and
compares **relative strength and POC alignment** across encounters per
`selection-criteria.md`. It does not restate or re-run any of those CMS rules. A
missing or `UNABLE_TO_DETERMINE` verdict is a gap to weigh (see `risk-flags.md`)
— never something to fill or re-derive.

## Citation
42 CFR §424.22(a)(1)(v) | CY2026 HH PPS Final Rule (90 FR, eff. Jan 1, 2026)
MBPM Pub. 100-02, Chapter 7, §30.5.1 | PIM Pub. 100-08, Chapter 6, §6.2.1/§6.2.3
