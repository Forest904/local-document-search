"""Ricerca applicativa su una sola versione immutabile per richiesta."""
from .contracts import InvalidInput, SearchRequest, SearchResponse, SearchResult
from .errors import ResourceFailure, SnapshotUnavailable
from .ports import SnapshotRepositoryPort
from local_document_search.domain.queries import QueryEvaluator, QueryParser


class SearchDocuments:
    def __init__(self, snapshots: SnapshotRepositoryPort) -> None:
        self.snapshots = snapshots

    def execute(self, request: SearchRequest) -> SearchResponse:
        try:
            snapshot = self.snapshots.load_active()
            if snapshot is None:
                raise SnapshotUnavailable("Nessuno snapshot attivo")
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
