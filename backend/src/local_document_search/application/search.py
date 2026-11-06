"""Ricerca applicativa su una sola versione immutabile per richiesta."""
from .contracts import DocumentDetails, InvalidInput, SearchRequest, SearchResponse, SearchResult
from .errors import ResourceFailure, SnapshotUnavailable
from .ports import SnapshotRepositoryPort
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.queries import QueryEvaluator, QueryParser


class SearchDocuments:
    def __init__(self, snapshots: SnapshotRepositoryPort) -> None:
        self.snapshots = snapshots

    def execute(self, request: SearchRequest) -> SearchResponse:
        try:
            with self.snapshots.acquire() as snapshot:
                try:
                    query = QueryParser().parse(request.query, request.field)
                except ValueError as exc:
                    raise InvalidInput(str(exc)) from exc
                matches = QueryEvaluator().evaluate(query, snapshot)
                results = []
                for match in matches[request.offset:request.offset + request.limit]:
                    metadata = snapshot.catalog.documents[match.document_id].descriptor.metadata
                    results.append(SearchResult(
                        match.document_id, metadata.filename, metadata.relative_path,
                        metadata.format, match.matched_fields,
                    ))
                return SearchResponse(snapshot.snapshot_id, tuple(results), len(matches))
        except MemoryError as exc:
            raise ResourceFailure("Memoria insufficiente durante la ricerca") from exc


class GetDocument:
    def __init__(self, snapshots: SnapshotRepositoryPort) -> None:
        self.snapshots = snapshots

    def execute(self, document_id: DocumentId, snapshot_id: str) -> DocumentDetails:
        try:
            with self.snapshots.acquire(snapshot_id) as snapshot:
                document = snapshot.catalog.documents.get(document_id)
                if document is None:
                    raise SnapshotUnavailable("Documento non disponibile nella versione richiesta")
                return DocumentDetails(snapshot.snapshot_id, document_id,
                                       document.descriptor.metadata, document.extracted_text)
        except MemoryError as exc:
            raise ResourceFailure("Memoria insufficiente durante il recupero") from exc
