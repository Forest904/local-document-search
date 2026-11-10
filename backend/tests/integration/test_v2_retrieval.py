"""Scenari V2-03 sui contratti pubblici e su entrambe le persistenze."""
from datetime import datetime, timezone

import pytest

from local_document_search.application.contracts import InvalidInput, SearchRequest, SuggestMode, SuggestRequest
from local_document_search.application.errors import SnapshotUnavailable
from local_document_search.application.search import ReadRuntime, SearchDocuments, SuggestTerms
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentId, DocumentMetadata, FileFingerprint, RelativePath,
)
from local_document_search.domain.queries import QueryEvaluator, QueryParser, SearchField
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository


def make_snapshot(root, key, items):
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    for number, (path, content) in enumerate(items):
        metadata = DocumentMetadata(RelativePath(path), path.rsplit("/", 1)[-1],
                                    DocumentFormat.TXT, FileFingerprint(len(content), 1))
        builder.add(DocumentId(number), CanonicalDocument(metadata, content))
    return draft.freeze(snapshot_id=key, root_directory=str(root),
                        created_at=datetime.now(timezone.utc), schema_version="1",
                        processing_version="1")


def publish(repo, snapshot):
    repo.save_candidate(snapshot)
    repo.validate_candidate(snapshot.snapshot_id)
    repo.activate(snapshot.snapshot_id)


@pytest.fixture(params=["memory", "sqlite"])
def repository(request, tmp_path):
    repo = (InMemorySnapshotRepository() if request.param == "memory" else
            SqliteSnapshotRepository(tmp_path / "storage"))
    yield repo, tmp_path
    if hasattr(repo, "close"):
        repo.close()


def test_prefix_fields_pagination_and_snapshot_versions(repository):
    repo, root = repository
    first = make_snapshot(root / "source", "first", [
        ("z/ReportFinal.txt", "reportage beta"),
        ("a.txt", "report beta"),
        ("b.txt", "alpha beta"),
        ("report.txt", "beta"),
    ])
    publish(repo, first)
    assert first.content_index.vocabulary == tuple(sorted(first.content_index.terms))
    assert first.filename_index.vocabulary == tuple(sorted(first.filename_index.terms))
    search = SearchDocuments(repo)
    request = SearchRequest("rep* beta", SearchField.BOTH, limit=1, allow_wildcards=True)
    page = search.execute(request)
    assert page.total_matches == 2
    assert page.results[0].relative_path.value == "a.txt"
    assert search.execute(SearchRequest("rep* beta", SearchField.BOTH, 1, 1, True)).results[0].relative_path.value == "z/ReportFinal.txt"
    assert search.execute(SearchRequest('rep* "beta"', SearchField.CONTENT, allow_wildcards=True)).total_matches == 2
    assert search.execute(SearchRequest("rep* absent", SearchField.BOTH, allow_wildcards=True)).total_matches == 0
    assert search.execute(SearchRequest("rep* be*", SearchField.BOTH, allow_wildcards=True)).total_matches == 2
    assert search.execute(SearchRequest("rep* rep*", SearchField.CONTENT, allow_wildcards=True)).total_matches == 2
    assert search.execute(SearchRequest("rep*", SearchField.FILENAME, allow_wildcards=True)).total_matches == 2
    assert search.execute(SearchRequest("rep*", SearchField.CONTENT, allow_wildcards=True)).total_matches == 2
    assert search.execute(SearchRequest("rep*", SearchField.CONTENT)).total_matches == 0
    for text, field, enabled in (("rep*", SearchField.BOTH, True),
                                 ("rep* be*", SearchField.BOTH, True),
                                 ("beta", SearchField.CONTENT, False)):
        expected = QueryEvaluator().evaluate(QueryParser().parse(text, field, enabled), first)
        for offset in (0, 1, len(expected), len(expected) + 1):
            response = search.execute(SearchRequest(text, field, 1, offset, enabled))
            assert response.total_matches == len(expected)
            assert [result.document_id for result in response.results] == [
                match.document_id for match in expected[offset:offset + 1]]
    suggest = SuggestTerms(repo)
    assert suggest.execute(SuggestRequest("rep", SearchField.BOTH)).terms == ("report", "reportage")
    assert suggest.execute(SuggestRequest("rep", SearchField.FILENAME)).terms == ("report",)
    assert suggest.execute(SuggestRequest("re", SearchField.CONTENT, limit=1)).terms == ("report",)
    assert suggest.execute(SuggestRequest("r", SearchField.CONTENT)).terms == ()
    assert suggest.execute(SuggestRequest("", SearchField.CONTENT)).snapshot_id == "first"
    second = make_snapshot(root / "source", "second", [("b.txt", "alpha beta")])
    publish(repo, second)
    assert suggest.execute(SuggestRequest("rep", snapshot_id="first")).terms == ("report", "reportage")
    assert suggest.execute(SuggestRequest("rep")).terms == ()
    if isinstance(repo, SqliteSnapshotRepository):
        repo.close()
        reopened = SqliteSnapshotRepository(root / "storage")
        try:
            assert reopened.load_active().content_index.vocabulary == ("alpha", "beta")
            assert SuggestTerms(reopened).execute(SuggestRequest("rep", snapshot_id="first")).terms == ("report", "reportage")
        finally:
            reopened.close()


@pytest.mark.parametrize("query", ["*", "re*p", "rep**", '"rep*"', '"*rep"', "a*",
                                          "DataBase*", "rep,*", "rep-*"])
def test_invalid_prefixes(repository, query):
    repo, root = repository
    publish(repo, make_snapshot(root / "source", "one", [("DataBase.txt", "report")]))
    with pytest.raises(InvalidInput):
        SearchDocuments(repo).execute(SearchRequest(query, allow_wildcards=True))


def test_expansion_limit_independent_of_other_clauses(repository):
    repo, root = repository
    publish(repo, make_snapshot(root / "source", "one", [("a.txt", " ".join(f"ab{i:03d}" for i in range(257)))]))
    search = SearchDocuments(repo)
    with pytest.raises(InvalidInput, match="256"):
        search.execute(SearchRequest("ab* absent", SearchField.CONTENT, allow_wildcards=True))
    assert search.execute(SearchRequest("ab255*", SearchField.CONTENT, allow_wildcards=True)).total_matches == 1
    assert SearchDocuments(repo).execute(SearchRequest("ab*", SearchField.FILENAME, allow_wildcards=True)).total_matches == 0


def test_exactly_256_expansions_are_accepted(repository):
    repo, root = repository
    publish(repo, make_snapshot(root / "source", "one", [
        ("a.txt", " ".join(f"ab{i:03d}" for i in range(256))),
    ]))
    assert SearchDocuments(repo).execute(SearchRequest("ab*", SearchField.CONTENT,
                                                       allow_wildcards=True)).total_matches == 1


def test_suffix_matches_ranking_highlights_and_suggestions(repository):
    repo, root = repository
    publish(repo, make_snapshot(root / "source", "one", [
        ("WalkingReport.txt", "walking testing"),
        ("b.txt", "testing walking walking"),
        ("c.txt", "cache"),
        ("Report.txt", "walking"),
    ]))
    with repo.acquire(None) as snapshot:
        for index in (snapshot.filename_index, snapshot.content_index):
            for suffix in ("ing", "ort", "missing"):
                assert set(index.terms_with_suffix(suffix)) == {
                    term for term in index.terms if term.endswith(suffix)}
    search = SearchDocuments(repo)
    response = search.execute(SearchRequest("*ing", SearchField.CONTENT, allow_wildcards=True))
    assert [r.relative_path.value for r in response.results] == ["Report.txt", "WalkingReport.txt", "b.txt"]
    assert response.results[0].snippet.highlights
    assert search.execute(SearchRequest("*ing", SearchField.FILENAME, allow_wildcards=True)).total_matches == 1
    assert search.execute(SearchRequest("*ing *ort", SearchField.BOTH, allow_wildcards=True)).total_matches == 1
    assert "Report.txt" not in [r.relative_path.value for r in search.execute(
        SearchRequest("*ing *ort", SearchField.BOTH, allow_wildcards=True)).results]
    assert search.execute(SearchRequest("walk* *ing", SearchField.CONTENT,
                                        allow_wildcards=True)).total_matches == 3
    assert search.execute(SearchRequest("*ing", SearchField.CONTENT)).total_matches == 0
    suggestions = SuggestTerms(repo).execute(SuggestRequest("ing", SearchField.BOTH, mode=SuggestMode.SUFFIX))
    assert suggestions.terms == ("testing", "walking")
    assert SuggestTerms(repo).execute(SuggestRequest("ing", limit=1, mode=SuggestMode.SUFFIX)).terms == ("testing",)
    assert SuggestTerms(repo).execute(SuggestRequest("i", mode=SuggestMode.SUFFIX)).terms == ()
    with pytest.raises(InvalidInput):
        SuggestRequest("ing", mode="suffix")


def test_suffix_expansion_limit_and_order(repository):
    repo, root = repository
    words = [f"a{i:03d}ing" for i in range(257)]
    publish(repo, make_snapshot(root / "source", "one", [("a.txt", " ".join(words))]))
    search = SearchDocuments(repo)
    with pytest.raises(InvalidInput, match="256"):
        search.execute(SearchRequest("absent *ing", SearchField.CONTENT, allow_wildcards=True))
    assert SuggestTerms(repo).execute(SuggestRequest("ing", SearchField.CONTENT, 1,
                                                     mode=SuggestMode.SUFFIX)).terms == ("a000ing",)
    publish(repo, make_snapshot(root / "source", "two", [("a.txt", " ".join(words[:256]))]))
    assert search.execute(SearchRequest("*ing", SearchField.CONTENT, allow_wildcards=True)).total_matches == 1


def test_suffix_unicode_versions_and_relevance(repository):
    from local_document_search.application.contracts import SearchOrder
    from local_document_search.application.search import GetDocument

    repo, root = repository
    first = make_snapshot(root / "source", "first", [
        ("CaffèNote.txt", "Café CAFE\u0301"),
        ("z.txt", "café"),
    ])
    publish(repo, first)
    search = SearchDocuments(repo)
    response = search.execute(SearchRequest("*fé", SearchField.CONTENT,
                                            allow_wildcards=True, order=SearchOrder.RELEVANCE))
    assert [r.relative_path.value for r in response.results] == ["CaffèNote.txt", "z.txt"]
    assert len(response.results[0].snippet.highlights) == 2
    detail = GetDocument(repo).execute(response.results[0].document_id, "first", "*fé",
                                       SearchField.CONTENT, True)
    assert len(detail.content_highlights) == 2
    assert search.execute(SearchRequest("*fè", SearchField.FILENAME,
                                        allow_wildcards=True)).total_matches == 1
    second = make_snapshot(root / "source", "second", [("z.txt", "different")])
    publish(repo, second)
    assert search.execute(SearchRequest("*fé", SearchField.CONTENT,
                                        allow_wildcards=True)).total_matches == 0
    assert search.execute(SearchRequest("*fé", SearchField.CONTENT,
                                        allow_wildcards=True, snapshot_id="first")).total_matches == 2
    assert SuggestTerms(repo).execute(SuggestRequest("fé", snapshot_id="first",
                                                     mode=SuggestMode.SUFFIX)).terms == ("café",)


def test_suggestions_validation_async_and_unavailable(repository):
    repo, root = repository
    publish(repo, make_snapshot(root / "source", "one", [("a.txt", "caffè caffe")]))
    runtime = ReadRuntime()
    try:
        suggest = SuggestTerms(repo, runtime)
        assert suggest.submit(SuggestRequest("caff")).result().terms == ("caffe", "caffè")
        assert suggest.execute(SuggestRequest("caffe\u0300")).terms == ("caffè",)
        for text in ("a b", "DataBase", "ab*", '"ab"'):
            with pytest.raises(InvalidInput):
                suggest.execute(SuggestRequest(text))
        with pytest.raises(SnapshotUnavailable):
            suggest.execute(SuggestRequest("ca", snapshot_id="missing"))
        with pytest.raises(InvalidInput):
            SuggestRequest("ca", limit=51)
    finally:
        runtime.close()
