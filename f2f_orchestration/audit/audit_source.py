"""Load a transaction's outputs into :class:`TransactionOutputs` from disk.

``AuditSource`` is the interface the standalone entrypoint depends on;
:class:`DiskAuditSource` is the concrete backend that reads the processed
``outputs/<txn>/`` JSON files. An external orchestrator (Temporal, etc.) skips
this module entirely and calls :meth:`TransactionOutputs.from_mapping` directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from .transaction_outputs import TransactionOutputs


@runtime_checkable
class AuditSource(Protocol):
    """Loads one transaction's outputs as a normalized :class:`TransactionOutputs`."""

    def load(self, transaction_id: str) -> TransactionOutputs: ...


class DiskAuditSource:
    """Loads from ``outputs/<transaction_id>/`` processed JSON files."""

    def __init__(self, outputs_dir: Path) -> None:
        self._outputs_dir = outputs_dir

    def load(self, transaction_id: str) -> TransactionOutputs:
        return TransactionOutputs.from_disk(self._outputs_dir, transaction_id)

    def available_transactions(self) -> list[str]:
        """Return every transaction directory under ``outputs_dir`` (sorted)."""
        if not self._outputs_dir.is_dir():
            return []
        return sorted(entry.name for entry in self._outputs_dir.iterdir() if entry.is_dir())
