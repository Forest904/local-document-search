"""DTO pubblici di ricerca e build completo M3."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from local_document_search.domain.documents import (
    DocumentId, DocumentMetadata, DocumentFormat, RelativePath, require_nonnegative,
)
from local_document_search.domain.queries import SearchField


class InvalidInput(ValueError):
    """Parametri della richiesta non validi."""


@dataclass(frozen=True)
class SearchRequest:
    query: str
    field: SearchField = SearchField.BOTH
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if not self.query.strip() or not isinstance(self.field, SearchField):
            raise InvalidInput("Query vuota o campo non valido")
        if type(self.limit) is not int or self.limit <= 0:
            raise InvalidInput("limit deve essere un intero positivo")
        if type(self.offset) is not int or self.offset < 0:
            raise InvalidInput("offset deve essere un intero non negativo")
        # SearchDocuments traduce gli errori del parser/analyzer in InvalidInput.


@dataclass(frozen=True)
class SearchResult:
    document_id: DocumentId
    filename: str
    relative_path: RelativePath
    format: DocumentFormat
    matched_fields: frozenset[SearchField]

    def __post_init__(self) -> None:
        object.__setattr__(self, "matched_fields", frozenset(self.matched_fields))
        if not self.matched_fields or any(
            field is not SearchField.FILENAME and field is not SearchField.CONTENT
            for field in self.matched_fields
        ):
            raise ValueError("matched_fields richiede campi concreti")


@dataclass(frozen=True)
class SearchResponse:
    snapshot_id: str
    results: tuple[SearchResult, ...]
    total_matches: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", tuple(self.results))
        require_nonnegative(self.total_matches, "total_matches")
        if not self.snapshot_id.strip() or len(self.results) > self.total_matches:
            raise ValueError("Risposta non coerente")


@dataclass(frozen=True)
class DocumentDetails:
    snapshot_id: str
    document_id: DocumentId
    metadata: DocumentMetadata
    extracted_text: str


@dataclass(frozen=True)
class BuildResult:
    """Esito del build iniziale completo; fallimenti esposti come errori."""
    snapshot_id: str
    discovered: int
    indexed: int
    excluded: int
    processed_bytes: int
    elapsed: float
    report: "JobReport | None" = None


@dataclass(frozen=True)
class SyncResult:
    snapshot_id: str
    changed: bool
    added: int
    modified: int
    removed: int
    unchanged: int
    excluded: int
    failed: int
    elapsed: float
    processed_bytes: int
    report: "JobReport | None" = None


@dataclass(frozen=True)
class JobDiagnostic:
    category: str
    phase: "JobPhase"
    relative_path: str | None
    reason: str


@dataclass(frozen=True)
class JobReport:
    diagnostics: tuple[JobDiagnostic, ...] = ()
    complete: bool = True
    published_snapshot_id: str | None = None
    added: int = 0
    modified: int = 0
    removed: int = 0
    unchanged: int = 0
    excluded: int = 0


@dataclass(frozen=True)
class ApplicationState:
    active_directory: str | None
    active_snapshot_id: str | None
    search_available: bool
    warning: str | None = None
    last_sync_outcome: str | None = None
    job: "JobRef | None" = None


class JobState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobPhase(str, Enum):
    SCANNING = "SCANNING"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    BUILDING = "BUILDING"
    COMMITTING = "COMMITTING"


@dataclass(frozen=True)
class JobRef:
    job_id: str
    status: JobState
    reused: bool = False


@dataclass(frozen=True)
class JobStatus:
    job_id: str
    state: JobState
    phase: JobPhase
    started_at: datetime
    files_total: int | None = None
    files_completed: int = 0
    bytes_total: int | None = None
    bytes_completed: int = 0
    current_file: str | None = None
    finished_at: datetime | None = None
    error: str | None = None
    report: JobReport | None = None

    @property
    def progress(self) -> float | None:
        """I byte misurano il lavoro, il completamento richiede il successo."""
        if self.state == JobState.COMPLETED:
            return 1.0
        if not self.bytes_total:
            return None
        return min(self.bytes_completed / self.bytes_total, 0.99)
