"""Ricerca applicativa su una sola versione immutabile per richiesta."""
from concurrent.futures import ThreadPoolExecutor
from heapq import nsmallest
from threading import Condition

from .contracts import (DocumentDetails, InvalidInput, SearchOrder, SearchRequest, SearchResponse,
                        SearchResult, SearchSnippet, TextRange, SuggestRequest, SuggestResponse)
from .errors import ResourceFailure, SnapshotUnavailable
from .ports import SnapshotRepositoryPort
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.analysis import ContentAnalyzer, FilenameAnalyzer, prepare_filename
from local_document_search.domain.highlighting import matching_ranges, token_spans
from local_document_search.domain.queries import QueryEvaluator, QueryParser, SearchField


def _ranges(query, field, text):
    return tuple(TextRange(start, end) for start, end in
                 matching_ranges(query, field, token_spans(text, filename=field is SearchField.FILENAME)))


def _snippet(text: str, ranges: tuple[TextRange, ...]) -> SearchSnippet:
    first = ranges[0].start if ranges else 0
    start = min(max(0, first - 80), max(0, len(text) - 240))
    end = min(len(text), start + 240)
    highlights = tuple(TextRange(max(value.start, start) - start, min(value.end, end) - start)
                       for value in ranges if value.start < end and value.end > start)
    return SearchSnippet(text[start:end], start, start > 0, end < len(text), highlights)


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
            with self.snapshots.acquire(request.snapshot_id) as snapshot:
                try:
                    query = QueryParser().parse(request.query, request.field, request.allow_prefixes)
                    evaluator = QueryEvaluator()
                    if request.formats is None and request.folder is None and request.order is SearchOrder.PATH:
                        matches, total = evaluator.evaluate_page(query, snapshot, request.offset, request.limit)
                    else:
                        by_field = evaluator.matched_ids_by_field(query, snapshot)
                        matched = set().union(*by_field.values())
                        candidates = []
                        for document_id in snapshot.ordered_document_ids:
                            if document_id not in matched:
                                continue
                            metadata = snapshot.catalog.documents[document_id].descriptor.metadata
                            if request.formats is not None and metadata.format not in request.formats:
                                continue
                            if request.folder is not None and not metadata.relative_path.value.startswith(request.folder + "/"):
                                continue
                            candidates.append(document_id)
                        total = len(candidates)
                        if request.order is SearchOrder.RELEVANCE:
                            def key(document_id):
                                fields = frozenset(field for field, ids in by_field.items() if document_id in ids)
                                name, frequency = evaluator.score(query, snapshot, document_id, fields)
                                path = snapshot.catalog.documents[document_id].descriptor.metadata.relative_path.value
                                return (-name, -frequency, path)
                            selected = nsmallest(request.offset + request.limit, candidates, key=key)[request.offset:]
                        else:
                            selected = candidates[request.offset:request.offset + request.limit]
                        matches = tuple(evaluator._make_match(document_id, by_field) for document_id in selected)
                except ValueError as exc:
                    raise InvalidInput(str(exc)) from exc
                results = []
                for match in matches:
                    document = snapshot.catalog.documents[match.document_id]
                    metadata = document.descriptor.metadata
                    filename_ranges = _ranges(query, SearchField.FILENAME,
                                              prepare_filename(metadata.filename)) if SearchField.FILENAME in match.matched_fields else ()
                    content_ranges = _ranges(query, SearchField.CONTENT,
                                             document.extracted_text) if SearchField.CONTENT in match.matched_fields else ()
                    results.append(SearchResult(
                        match.document_id, metadata.filename, metadata.relative_path,
                        metadata.format, match.matched_fields,
                        _snippet(document.extracted_text, content_ranges), filename_ranges,
                    ))
                return SearchResponse(snapshot.snapshot_id, tuple(results), total)
        except MemoryError as exc:
            raise ResourceFailure("Memoria insufficiente durante la ricerca") from exc


class SuggestTerms:
    def __init__(self, snapshots: SnapshotRepositoryPort, runtime=None) -> None:
        self.snapshots = snapshots
        self.runtime = runtime

    def submit(self, request: SuggestRequest):
        if self.runtime is None:
            raise InvalidInput("Runtime asincrono non configurato")
        return self.runtime.submit(self._execute, request)

    def execute(self, request: SuggestRequest) -> SuggestResponse:
        if self.runtime is not None:
            return self.runtime.run(self._execute, request)
        return self._execute(request)

    def _execute(self, request: SuggestRequest) -> SuggestResponse:
        try:
            with self.snapshots.acquire(request.snapshot_id) as snapshot:
                if not request.text.strip():
                    return SuggestResponse(snapshot.snapshot_id, ())
                if any(char in request.text for char in '*"'):
                    raise InvalidInput("Sintassi non valida per suggerimenti")
                fields = ((SearchField.FILENAME, FilenameAnalyzer(), snapshot.filename_index),
                          (SearchField.CONTENT, ContentAnalyzer(), snapshot.content_index))
                found = set()
                for field, analyzer, index in fields:
                    if request.field not in (field, SearchField.BOTH):
                        continue
                    tokens = analyzer.analyze(request.text)
                    if len(tokens) != 1:
                        raise InvalidInput("Richiesto un solo token per campo")
                    prefix = tokens[0].term
                    if len(prefix) >= 2:
                        found.update(index.terms_with_prefix(prefix, request.limit))
                return SuggestResponse(snapshot.snapshot_id, tuple(sorted(found)[:request.limit]))
        except MemoryError as exc:
            raise ResourceFailure("Memoria insufficiente durante i suggerimenti") from exc


class GetDocument:
    def __init__(self, snapshots: SnapshotRepositoryPort, runtime=None) -> None:
        self.snapshots = snapshots
        self.runtime = runtime

    def submit(self, document_id: DocumentId, snapshot_id: str, query: str | None = None,
               field: SearchField = SearchField.BOTH, allow_prefixes: bool = False):
        if self.runtime is None:
            raise InvalidInput("Runtime asincrono non configurato")
        return self.runtime.submit(self._execute, document_id, snapshot_id, query, field, allow_prefixes)

    def execute(self, document_id: DocumentId, snapshot_id: str, query: str | None = None,
                field: SearchField = SearchField.BOTH, allow_prefixes: bool = False) -> DocumentDetails:
        if self.runtime is not None:
            return self.runtime.run(self._execute, document_id, snapshot_id, query, field, allow_prefixes)
        return self._execute(document_id, snapshot_id, query, field, allow_prefixes)

    def _execute(self, document_id: DocumentId, snapshot_id: str, query: str | None,
                 field: SearchField, allow_prefixes: bool) -> DocumentDetails:
        try:
            with self.snapshots.acquire(snapshot_id) as snapshot:
                document = snapshot.catalog.documents.get(document_id)
                if document is None:
                    raise SnapshotUnavailable("Documento non disponibile nella versione richiesta")
                filename_ranges = content_ranges = ()
                if query is not None:
                    try:
                        parsed = QueryParser().parse(query, field, allow_prefixes)
                        by_field = QueryEvaluator().matched_ids_by_field(parsed, snapshot)
                        metadata = document.descriptor.metadata
                        if document_id in by_field.get(SearchField.FILENAME, ()):
                            filename_ranges = _ranges(parsed, SearchField.FILENAME,
                                                      prepare_filename(metadata.filename))
                        if document_id in by_field.get(SearchField.CONTENT, ()):
                            content_ranges = _ranges(parsed, SearchField.CONTENT, document.extracted_text)
                    except ValueError as exc:
                        raise InvalidInput(str(exc)) from exc
                return DocumentDetails(snapshot.snapshot_id, document_id,
                                       document.descriptor.metadata, document.extracted_text,
                                       filename_ranges, content_ranges)
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
