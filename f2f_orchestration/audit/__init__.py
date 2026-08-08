"""Final audit layer: merged encounters + selection headline fields (lossless).

A pure, source-agnostic transform that consumes the consolidated
``merge_encounters`` contract plus the ``encounter-selection`` output and returns
the identical merge_encounters format with every encounter retained, surfacing the
selection headline fields at the top of ``results`` so downstream consumers can
derive any view (best-only, drop referrals, show-all) from a single document.

Public API::

    audit = FinalAuditEngine().build(merged, selection, generated_at=now)
"""

from .audit_engine import FinalAuditEngine

__all__ = ["FinalAuditEngine"]
