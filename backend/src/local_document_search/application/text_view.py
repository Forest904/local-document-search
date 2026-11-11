"""Preparazione di un documento testuale aperto dal desktop."""
from dataclasses import dataclass
from typing import Protocol

from local_document_search.domain.documents import DocumentFormat, RelativePath
from .contracts import TextNavigationTarget, TextRange


@dataclass(frozen=True)
class TextViewRequest:
    root_directory: str
    relative_path: RelativePath
    format: DocumentFormat
    snapshot_id: str
    target: TextNavigationTarget | None


@dataclass(frozen=True)
class TextViewDocument:
    source: str
    bom: bool
    line_endings: str
    source_ranges: tuple[TextRange, ...]
    destination_status: str  # ready, filename, changed, unavailable


class TextViewSourcePort(Protocol):
    def prepare(self, request: TextViewRequest) -> TextViewDocument: ...


class PrepareTextView:
    def __init__(self, source: TextViewSourcePort):
        self._source = source

    def execute(self, request: TextViewRequest) -> TextViewDocument:
        if request.format not in (DocumentFormat.TXT, DocumentFormat.MARKDOWN):
            raise ValueError("Reader testuale disponibile solo per TXT/MD")
        return self._source.prepare(request)
