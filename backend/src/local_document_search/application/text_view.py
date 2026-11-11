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
    source_version: tuple[int, int, int, int] | None = None  # size, mtime_ns, device, inode


@dataclass(frozen=True)
class SaveTextRequest:
    root_directory: str
    relative_path: RelativePath
    format: DocumentFormat
    text: str
    original_text: str
    bom: bool
    source_version: tuple[int, int, int, int]


@dataclass(frozen=True)
class SaveTextResult:
    source_version: tuple[int, int, int, int]
    source: str
    sync_requested: bool = False


class TextViewSavePort(Protocol):
    def save(self, request: SaveTextRequest) -> SaveTextResult: ...


class SaveTextDocument:
    def __init__(self, source: TextViewSavePort, lifecycle=None):
        self._source = source
        self._lifecycle = lifecycle

    def execute(self, request: SaveTextRequest) -> SaveTextResult:
        if request.format not in (DocumentFormat.TXT, DocumentFormat.MARKDOWN):
            raise ValueError("Editor disponibile solo per TXT/MD")
        if self._lifecycle is None:
            return self._source.save(request)
        jobs = self._lifecycle.jobs
        while True:
            with jobs.lock:
                jobs.ensure_open()
                if not jobs.active:
                    selected = self._lifecycle.settings.load().active_directory
                    if selected != request.root_directory:
                        raise ValueError("Directory attiva cambiata")
                    saved = self._source.save(request)
                    try:
                        self._lifecycle.request("manual")
                    except Exception:
                        return saved
                    return SaveTextResult(saved.source_version, saved.source, True)
                current = jobs.current()
            try:
                jobs.wait(current.job_id)
            except Exception:
                # A failed sync still releases the writer for an explicit save.
                pass


class TextViewSourcePort(Protocol):
    def prepare(self, request: TextViewRequest) -> TextViewDocument: ...


class PrepareTextView:
    def __init__(self, source: TextViewSourcePort):
        self._source = source

    def execute(self, request: TextViewRequest) -> TextViewDocument:
        if request.format not in (DocumentFormat.TXT, DocumentFormat.MARKDOWN):
            raise ValueError("Reader testuale disponibile solo per TXT/MD")
        return self._source.prepare(request)
