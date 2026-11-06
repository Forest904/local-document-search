"""DTO pubblici di ricerca; i casi d'uso saranno introdotti successivamente."""
from dataclasses import dataclass

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
        # Parser/analyzer M2 validano sintassi e token; collegamento al caso d'uso in M3.


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
