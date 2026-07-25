# Client Rules — TEMPLATE
# skill: encounter_identity
# Copy this file to clients/<CLIENT_NAME>/client-rules.md and fill in.

# ── Anchors ──────────────────────────────────────────────────────────────────
# These values override whatever is passed in the system prompt for this client.
# Leave commented out to inherit from the system prompt anchor.

# client_name: CLIENT_A
# poc_certifying_provider: "<provider name from 485>"

# ── Directives ───────────────────────────────────────────────────────────────
# Each directive has the format:
#   VERB  SECTION_ID  "description / replacement text"
#
# ELEVATE  — increase signal_strength for an evidence pattern to STRONG
# EXTEND   — add an additional acceptable pattern or label not in the CMS default
# EXCLUDE  — exclude a normally accepted pattern or provider type for this client
# REPLACE  — replace a CMS-default rule entirely with client-defined logic

# Examples:

# EXTEND  ED_DATE_PRIORITY
#   Accept "Service Rendered On:" as a priority-1 labeled date label.

# ELEVATE  EP_SIGNATURE_TYPES
#   Treat typed_unverified signatures as electronic_verified for CLIENT_A EHR
#   because CLIENT_A's system auto-authenticates all typed names at sign-off.

# EXCLUDE  EP_ELIGIBLE_PROVIDER
#   CNM not accepted for CLIENT_A — state law does not authorize CNM for HH F2F.

# REPLACE  EP_COSIGN
#   For HHA-authored notes, CLIENT_A requires co-sign within 24 hours of DOS.
#   co_sign_deadline_hours: 24

# ── client_notes ─────────────────────────────────────────────────────────────
# Free-text notes for auditors reviewing this client's output.
# client_notes: |
#   CLIENT_A uses Meditech EHR. Electronic signature block always appears as
#   "AUTH: <Name>, <Cred> <timestamp>" — treat AUTH prefix as electronic_verified.
