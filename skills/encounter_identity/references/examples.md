# Encounter Identity — CMS Examples and Language Patterns
# Source: MBPM Pub. 100-02, Chapter 7, §30.5.1.2 | 42 CFR §424.22

---

## Encounter Date Examples

### Qualifying — Date Clearly Extracted

| Scenario | Raw Text | Extracted Value | Confidence |
|---|---|---|---|
| Labeled DOS in header | `Date of Service: 01/15/2025` | 2025-01-15 | high |
| Alternate label | `Visit Date: January 15, 2025` | 2025-01-15 | high |
| Telehealth note | `Date of Service: 01/15/2025 (Telehealth – Video)` | 2025-01-15 | high |
| Body text with signal | `Patient was seen on 01/15/2025 for follow-up` | 2025-01-15 | medium |
| Signature date fallback | No DOS field; signature reads `01/15/2025` | 2025-01-15 | low |

### Non-Qualifying — Do NOT Use These

| Scenario | Raw Text | Reason |
|---|---|---|
| Dictation date | `Dictated: 01/16/2025` | Not the encounter date |
| Transcription date | `Transcribed: 01/17/2025` | Administrative date |
| Future appointment | `Next visit: 02/01/2025` | Not this encounter |
| Ambiguous reference | `As of last month, patient was stable.` | No contextual signal |

---

## Signature Examples

### Qualifying

| Scenario | Evidence | Type | Confidence |
|---|---|---|---|
| EHR electronic block | `Electronically signed by: Sarah Jones, NP — 01/15/2025 10:04` | `electronic_verified` | High |
| Slash-s notation | `/s/ Michael Brown, MD 01/15/2025` | `electronic_verified` | High |
| Physical with name | `<signature>Dr. Amy Lee, DO</signature>` | `handwritten` | Medium |
| Signed status in header | `[Signed]` — no name, no tag | `absent` name; `signed = true` | Low |

### Non-Qualifying / Flagged

| Scenario | Flag Raised | Impact |
|---|---|---|
| `<signature>signed</signature>` | `illegible_signature = true` | Confidence drop |
| Signature date 45 days after DOS | `late_documentation = true` | Flag for review |
| Typed name "John Smith MD" no EHR prefix | `typed_unverified` | Low confidence |
| Rubber stamp impression | `stamp_signature = true` | MAC may reject |

---

## Eligible Provider + Multi-Signature Examples

### Disambiguation — Multiple Electronic Signatures

**Scenario A — Performed By match resolves it:**
- Performed By: Dr. Patel, MD
- Electronic signers: Dr. Patel, MD (10:00) | Dr. Nguyen, MD (Co-sign, 10:30)
- → Conductor: Dr. Patel, MD | method: `performed_by_match` | confidence: high

**Scenario B — Role label resolves it:**
- No Performed By field
- Electronic signers: Dr. Kim, MD (Attending) | Dr. Lee, Resident (Resident/PGY-2)
- → Conductor: Dr. Kim, MD | method: `role_label_attending`
- → Dr. Lee: `resident_conductor = true`; co-sign by Dr. Kim validated

**Scenario C — Ambiguous, MD/DO priority:**
- No Performed By; no role labels
- Electronic signers: Dr. Chen, MD | Dr. Ramos, MD (timestamps identical)
- → `conducting_provider_ambiguous = true` | method: `ambiguous`
- → Output: all signers listed; disambiguation reason stated in reasoning

**Scenario D — No Performed By, single NPP:**
- No Performed By field
- Single electronic signer: Sarah Jones, NP
- → Conductor: Sarah Jones, NP | method: `single_electronic` | confidence: medium

---

## Language Signal Map

| Language in Note | Interpretation |
|---|---|
| "Patient seen today on [date]" | Strong — contextual signal for priority 4 |
| "I evaluated the patient on [date]" | Strong — first-person contextual signal |
| "Per prior note dated [date]" | Reference date only — do NOT use |
| "Patient scheduled on [date]" | Future appointment — do NOT use |
| "Co-signed by:" | Co-signer, not conductor |
| "Attestation:" | Co-signer attestation, not conductor |
| "Ordering Provider:" | Conductor role label → `role_label_attending` |
