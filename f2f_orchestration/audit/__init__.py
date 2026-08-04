"""Audit engine: collate agent outputs into the audit-results contract.

A pure, source-agnostic layer that reads the agents' processed outputs for one
transaction and rewrites them into the single ``audit-results`` contract (topics
with inline-resolved evidence). It makes no audit verdicts.

Public API::

    outputs = DiskAuditSource(outputs_dir).load(txn)          # disk (batch)
    outputs = TransactionOutputs.from_mapping(payload)        # agnostic / Temporal
    audit = AuditEngine().build(outputs, generated_at=now)    # same for both
"""

from .audit_engine import PARAMETER_ID, AuditEngine
from .audit_source import AuditSource, DiskAuditSource
from .evidence_resolver import EvidenceResolver
from .key_builders import BUILDERS
from .transaction_outputs import TransactionOutputs

__all__ = [
    "AuditEngine",
    "PARAMETER_ID",
    "AuditSource",
    "DiskAuditSource",
    "EvidenceResolver",
    "TransactionOutputs",
    "BUILDERS",
]
