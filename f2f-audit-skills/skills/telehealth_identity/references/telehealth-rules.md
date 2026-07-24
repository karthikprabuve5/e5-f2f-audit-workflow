# Telehealth F2F — CMS Rules Reference
# skill: telehealth_identity
# Source: CMS Chapter 7 §30.5 | CMS-1828-F (CY 2026 HH Final Rule)
#         Consolidated Appropriations Act 2023 (telehealth extension)

---

## TH_MODALITY — Modality Requirements
<!-- cms_section_id: TH_MODALITY -->

CMS requires synchronous (real-time) two-way communication for F2F telehealth.
Store-and-forward (asynchronous) is NOT permitted for F2F encounters.

| Modality | CMS Status | Notes |
|---|---|---|
| Audio + Video | Allowed | Standard telehealth F2F modality |
| Audio-only | Conditionally allowed | See TH_AUDIO_ONLY |
| Video-only | Not recognized | Not a defined CMS telehealth F2F modality |
| Asynchronous | NOT allowed | Does not satisfy F2F requirement |

Flag `synchronous_not_confirmed = true` if no real-time interaction language found.

---

## TH_AUDIO_ONLY — Audio-Only Restrictions
<!-- cms_section_id: TH_AUDIO_ONLY -->
<!-- element_type: CRITERIA -->

Audio-only telehealth for F2F encounters is conditionally permitted under:
- Consolidated Appropriations Act extensions and subsequent legislation (through CY 2026)
- 42 CFR §410.78 (Medicare telehealth services) — audio-only allowed when:
  1. Patient is in a rural area or Health Professional Shortage Area (HPSA), OR
  2. Patient has documented inability or lack of technology to participate via video

Note: The rural/HPSA and technology-barrier conditions originate from the
Physician Fee Schedule telehealth rules. Their application to HH F2F is governed
by the same telehealth extension legislation. Extraction captures the modality as
documented — downstream audit engine determines if audio-only is justified.

Always flag `audio_only_flagged = true` when modality is audio-only.

---

## TH_LOCATION — Location Requirements
<!-- cms_section_id: TH_LOCATION -->

| Party | CMS Term | Requirement |
|---|---|---|
| Patient | Originating site | Home allowed under post-PHE extensions through CY 2026 |
| Provider | Distant site | Any location with appropriate licensure |

Flag `no_patient_location = true` if patient location absent from document.
Flag `no_provider_location = true` if provider location absent from document.
Eligibility determination (originating site compliance) is downstream.

---

## TH_CONSENT — Consent Documentation
<!-- cms_section_id: TH_CONSENT -->

CMS does not explicitly mandate telehealth consent within the F2F note itself,
but Medicare Conditions of Participation and many state laws require it.
Capture whether consent is documented — do not determine compliance.
Flag `no_consent = true` if consent language is absent.

---

## TH_SYNCHRONOUS — Synchronous Confirmation Signals
<!-- cms_section_id: TH_SYNCHRONOUS -->
<!-- element_type: EXAMPLE -->

Keywords confirming real-time communication:
"real-time", "live video", "interactive", "two-way", "synchronous",
"patient seen via telehealth", "video call conducted", "visit conducted via",
"audio and video connection", "real-time audio/video"

Absence of all these signals → `synchronous_not_confirmed = true`.

---

## TH_FLAGS — Flag Summary
<!-- cms_section_id: TH_FLAGS -->

| Flag | Set When |
|---|---|
| `audio_only_flagged` | Modality is `audio_only` |
| `no_modality_documented` | Telehealth confirmed but modality not explicitly stated (`unknown`) |
| `no_patient_location` | Patient location field absent from document |
| `no_provider_location` | Provider location field absent from document |
| `no_consent` | Consent language absent or declined |
| `synchronous_not_confirmed` | No real-time interaction language found anywhere in document |
