"""Merge-encounters engine: collate agent outputs into one per-transaction contract.

A pure, source-agnostic layer that reads the agents' processed outputs for one
transaction and rewrites them into the single ``merge_encounters`` contract (topics
with inline-resolved evidence). It makes no verdicts — the final audit layer does.

Public API::

    outputs = DiskMergeSource(outputs_dir).load(txn)                    # disk (batch)
    outputs = TransactionOutputs.from_mapping(payload)                  # agnostic / Temporal
    merged = MergeEncountersEngine().build(outputs, generated_at=now)   # same for both
"""

from .evidence_resolver import EvidenceResolver
from .key_builders import BUILDERS
from .merge_engine import PARAMETER_ID, MergeEncountersEngine
from .merge_source import DiskMergeSource, MergeSource
from .pipeline_payload import build_merge_encounters_payload
from .transaction_outputs import TransactionOutputs

__all__ = [
    "MergeEncountersEngine",
    "PARAMETER_ID",
    "MergeSource",
    "DiskMergeSource",
    "EvidenceResolver",
    "TransactionOutputs",
    "BUILDERS",
    "build_merge_encounters_payload",
]
