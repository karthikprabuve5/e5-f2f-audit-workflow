"""Input document sourcing.

Pipelines consume document content as ``str`` and never read the filesystem
themselves. ``DocumentSource`` is the boundary: locally the entrypoints use
``LocalDirectoryDocumentSource`` to read ``ocr-markdown/<transaction_id>/*.md``;
in production an upstream layer can supply its own ``DocumentSource`` (or pass
the strings directly) with no pipeline changes.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

from .logging_setup import get_logger

logger = get_logger(__name__)


class DocumentKind(StrEnum):
    """The two input documents; values match the on-disk file stems."""

    POC = "POC"
    F2F = "F2F"


@runtime_checkable
class DocumentSource(Protocol):
    """Supplies raw document content for a transaction."""

    def load(self, transaction_id: str, kind: DocumentKind) -> str: ...


class LocalDirectoryDocumentSource:
    """Reads documents from ``<ocr_markdown_dir>/<transaction_id>/<KIND>.md``."""

    def __init__(self, ocr_markdown_dir: Path) -> None:
        self._ocr_markdown_dir = ocr_markdown_dir

    def load(self, transaction_id: str, kind: DocumentKind) -> str:
        document_path = self._ocr_markdown_dir / transaction_id / f"{kind}.md"
        try:
            content = document_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"{kind} document not found for transaction '{transaction_id}' at {document_path}."
            ) from exc

        logger.debug(
            "Loaded input document",
            extra={"transaction_id": transaction_id, "kind": str(kind), "chars": len(content)},
        )
        return content
