"""T06/T07: ranking, filtri e testo della versione acquisita."""
import pytest

from local_document_search.application.contracts import InvalidInput, SearchOrder, SearchRequest
from local_document_search.application.errors import SnapshotUnavailable
from local_document_search.application.search import GetDocument, SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.domain.documents import DocumentFormat
from local_document_search.domain.queries import SearchField
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery
from local_document_search.infrastructure.readers.text import TextReader
from local_document_search.infrastructure.readers.markdown import MarkdownReader
from local_document_search.infrastructure.readers.pdf import PdfReader
from local_document_search.infrastructure.readers.registry import DocumentReader
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository


def build(repo, root):
    reader = DocumentReader({DocumentFormat.TXT: TextReader(),
                             DocumentFormat.MARKDOWN: MarkdownReader(),
                             DocumentFormat.PDF: PdfReader()})
    BuildIndex(DocumentFileDiscovery(), reader, repo).execute(str(root))


def test_rank_filters_pages_and_snapshot(tmp_path):
    files = {
        "a/alpha.txt": "alpha",
        "a/sub/b.txt": "alpha alpha alpha",
        "a/sub/c.md": "alpha alpha",
        "a-old/d.txt": "alpha alpha alpha alpha",
        "z.txt": "alpha",
    }
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    repo = InMemorySnapshotRepository()
    build(repo, tmp_path)
    search = SearchDocuments(repo)
    request = SearchRequest("alpha", order=SearchOrder.RELEVANCE,
                            formats={DocumentFormat.TXT, DocumentFormat.MARKDOWN}, folder="a")
    page = search.execute(request)
    assert page.total_matches == 3
    assert [result.relative_path.value for result in page.results] == [
        "a/alpha.txt", "a/sub/b.txt", "a/sub/c.md",
    ]
    second = search.execute(SearchRequest("alpha", order=SearchOrder.RELEVANCE,
                                          folder="a", offset=1, limit=1,
                                          snapshot_id=page.snapshot_id))
    assert second.total_matches == 3
    assert second.results[0].relative_path.value == "a/sub/b.txt"
    assert [r.relative_path.value for r in search.execute(SearchRequest("alpha")).results] == sorted(files)
    with pytest.raises(SnapshotUnavailable):
        search.execute(SearchRequest("alpha", snapshot_id="missing"))


@pytest.mark.parametrize("folder", ["/a", "a/../b", "a//b", "C:/a", "a\\b", "a/"])
def test_invalid_folder(folder):
    with pytest.raises(InvalidInput):
        SearchRequest("alpha", folder=folder)


def test_unicode_phrase_and_persisted_preview(tmp_path):
    path = tmp_path / "other.txt"
    text = "x" * 100 + " Straße 😀 café cafe\u0301 Straße 😀 café " + "y" * 200
    path.write_text(text, encoding="utf-8")
    repo = InMemorySnapshotRepository()
    build(repo, tmp_path)
    search = SearchDocuments(repo)
    response = search.execute(SearchRequest('"straße café"', SearchField.BOTH))
    result = response.results[0]
    assert result.matched_fields == {SearchField.CONTENT}
    assert result.snippet.truncated_before and result.snippet.truncated_after
    assert len(result.snippet.text) == 240
    assert [result.snippet.text[r.start:r.end] for r in result.snippet.highlights] == [
        "Straße 😀 café", "Straße 😀 café",
    ]
    path.unlink()
    details = GetDocument(repo).execute(result.document_id, response.snapshot_id,
                                        '"straße café"', SearchField.BOTH)
    assert details.extracted_text == text
    assert [text[r.start:r.end] for r in details.content_highlights] == ["Straße 😀 café", "Straße 😀 café"]
    assert details.filename_highlights == ()


def test_prefix_and_name_highlight(tmp_path):
    path = tmp_path / "AlphaBeta.txt"
    path.write_text("", encoding="utf-8")
    repo = InMemorySnapshotRepository()
    build(repo, tmp_path)
    result = SearchDocuments(repo).execute(SearchRequest("alp*", allow_wildcards=True)).results[0]
    assert result.filename[result.filename_highlights[0].start:result.filename_highlights[0].end] == "Alpha"
    assert result.snippet.text == ""


def test_suffix_filters_ranking_and_page(tmp_path):
    for name, content in {
        "a/walking.txt": "walking",
        "a/talking.md": "talking talking",
        "b/walking.txt": "walking walking walking",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    repo = InMemorySnapshotRepository()
    build(repo, tmp_path)
    request = SearchRequest("*ing", SearchField.BOTH, allow_wildcards=True,
                            order=SearchOrder.RELEVANCE, folder="a",
                            formats={DocumentFormat.TXT, DocumentFormat.MARKDOWN}, limit=1, offset=1)
    response = SearchDocuments(repo).execute(request)
    assert response.total_matches == 2
    assert [r.relative_path.value for r in response.results] == ["a/walking.txt"]
    result = response.results[0]
    assert result.filename[result.filename_highlights[0].start:result.filename_highlights[0].end] == "walking"


def test_both_scores_only_complete_fields_and_stable_ties(tmp_path):
    for name, content in {
        "a/alpha-beta.txt": "alpha alpha alpha",
        "b/alpha-beta.txt": "alpha",
        "c/other.txt": "alpha beta alpha beta",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    repo = InMemorySnapshotRepository()
    build(repo, tmp_path)
    results = SearchDocuments(repo).execute(SearchRequest("alpha beta", order=SearchOrder.RELEVANCE)).results
    assert [result.relative_path.value for result in results] == [
        "a/alpha-beta.txt", "b/alpha-beta.txt", "c/other.txt",
    ]
    assert results[0].matched_fields == {SearchField.FILENAME}
    assert results[2].matched_fields == {SearchField.CONTENT}
