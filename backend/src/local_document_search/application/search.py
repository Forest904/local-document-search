"""Ricerca applicativa su una sola versione immutabile per richiesta."""
from concurrent.futures import ThreadPoolExecutor
from threading import Condition

from .contracts import DocumentDetails, InvalidInput, SearchRequest, SearchResponse, SearchResult
from .errors import ResourceFailure, SnapshotUnavailable
from .ports import SnapshotRepositoryPort
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.queries import QueryEvaluator, QueryParser


class SearchDocuments:
    def __init__(self, snapshots: SnapshotRepositoryPort, runtime=None) -> None:
        self.snapshots = snapshots
        self.runtime = runtime

    def submit(self, request: SearchRequest):
        if self.runtime is None:
            raise InvalidInput("Runtime asincrono non configurato")
        return self.runtime.submit(self._execute, request)

    def execute(self, request: SearchRequest) -> SearchResponse:
        if self.runtime is not None:
            return self.runtime.run(self._execute, request)
        return self._execute(request)

    def _execute(self, request: SearchRequest) -> SearchResponse:
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
    def __init__(self, snapshots: SnapshotRepositoryPort, runtime=None) -> None:
        self.snapshots = snapshots
        self.runtime = runtime

    def submit(self, document_id: DocumentId, snapshot_id: str):
        if self.runtime is None:
            raise InvalidInput("Runtime asincrono non configurato")
        return self.runtime.submit(self._execute, document_id, snapshot_id)

    def execute(self, document_id: DocumentId, snapshot_id: str) -> DocumentDetails:
        if self.runtime is not None:
            return self.runtime.run(self._execute, document_id, snapshot_id)
        return self._execute(document_id, snapshot_id)

    def _execute(self, document_id: DocumentId, snapshot_id: str) -> DocumentDetails:
        try:
            with self.snapshots.acquire(snapshot_id) as snapshot:
                document = snapshot.catalog.documents.get(document_id)
                if document is None:
                    raise SnapshotUnavailable("Documento non disponibile nella versione richiesta")
                return DocumentDetails(snapshot.snapshot_id, document_id,
                                       document.descriptor.metadata, document.extracted_text)
        except MemoryError as exc:
            raise ResourceFailure("Memoria insufficiente durante il recupero") from exc


class ReadRuntime:
    """Ammette letture sync/async e attende tutte quelle accettate alla chiusura."""
    def __init__(self):
        self._condition = Condition()
        self._closed = False
        self._readers = 0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="index-read")

    def _admit(self):
        if self._closed:
            raise InvalidInput("Sessione in chiusura o chiusa")
        self._readers += 1

    def _release(self):
        with self._condition:
            self._readers -= 1
            self._condition.notify_all()

    def _run(self, operation, args):
        try:
            return operation(*args)
        finally:
            self._release()

    def run(self, operation, *args):
        with self._condition:
            self._admit()
        return self._run(operation, args)

    def submit(self, operation, *args):
        with self._condition:
            self._admit()
            try:
                future = self._executor.submit(self._run, operation, args)
            except BaseException:
                self._release()
                raise
            # Future.cancel può annullare una lettura non ancora iniziata.
            future.add_done_callback(lambda done: self._release() if done.cancelled() else None)
            return future

    def stop_accepting(self):
        with self._condition:
            self._closed = True

    def close(self):
        self.stop_accepting()
        self._executor.shutdown(wait=True)
        with self._condition:
            while self._readers:
                self._condition.wait()
