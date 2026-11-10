"""T24: proposte dalla versione acquisita, senza espandere la ricerca."""
from datetime import datetime, timezone

import pytest

from local_document_search.application.contracts import InvalidInput, SpellingRequest
from local_document_search.application.errors import SnapshotUnavailable
from local_document_search.application.search import SearchDocuments, SuggestSpellingCorrections
from local_document_search.application.contracts import SearchRequest
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentId, DocumentMetadata, FileFingerprint, RelativePath,
)
from local_document_search.domain.queries import SearchField
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository


def publish(repo, name, items):
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    for number, (path, content) in enumerate(items):
        metadata = DocumentMetadata(RelativePath(path), path.rsplit("/", 1)[-1],
                                    DocumentFormat.TXT, FileFingerprint(len(content), 1))
        builder.add(DocumentId(number), CanonicalDocument(metadata, content))
    snapshot = draft.freeze(snapshot_id=name, root_directory="C:/source",
                            created_at=datetime.now(timezone.utc), schema_version="1",
                            processing_version="1")
    repo.save_candidate(snapshot)
    repo.validate_candidate(name)
    repo.activate(name)


def test_query_correction_preserves_original_search_and_spans():
    repo = InMemorySnapshotRepository()
    publish(repo, "N", [("Famous.txt", "famous entrepreneurs café"),
                        ("Form.txt", "form Heathrow")])
    spelling = SuggestSpellingCorrections(repo)
    original = "famos, entrepreneurrs café"
    result = spelling.execute(SpellingRequest(original, SearchField.CONTENT))
    assert result.snapshot_id == "N"
    assert result.proposed_query == "famous, entrepreneurs café"
    assert [(original[r.start:r.end], r.replacement) for r in result.replacements] == [
        ("famos", "famous"), ("entrepreneurrs", "entrepreneurs")]
    assert SearchDocuments(repo).execute(SearchRequest(original, SearchField.CONTENT)).total_matches == 0
    assert SearchDocuments(repo).execute(SearchRequest(result.proposed_query, SearchField.CONTENT)).total_matches == 1
    assert spelling.execute(SpellingRequest("form Heathrow", SearchField.CONTENT)).proposed_query is None
    assert spelling.execute(SpellingRequest("famos *preneurs", SearchField.CONTENT)).proposed_query is None
    assert spelling.execute(SpellingRequest('"famos"', SearchField.CONTENT)).proposed_query is None
    assert spelling.execute(SpellingRequest("famos X123", SearchField.CONTENT)).proposed_query == "famous X123"


@pytest.mark.parametrize("persistent", [False, True])
def test_field_versions_and_input(tmp_path, persistent):
    repo = SqliteSnapshotRepository(tmp_path / "index") if persistent else InMemorySnapshotRepository()
    publish(repo, "N", [("famous.txt", "something")])
    spelling = SuggestSpellingCorrections(repo)
    assert spelling.execute(SpellingRequest("famos", SearchField.FILENAME)).proposed_query == "famous"
    assert spelling.execute(SpellingRequest("famos", SearchField.CONTENT)).proposed_query is None
    assert spelling.execute(SpellingRequest("Famous", SearchField.BOTH)).proposed_query is None
    assert spelling.execute(SpellingRequest("FamousReport", SearchField.BOTH)).proposed_query is None
    publish(repo, "N2", [("other.txt", "something")])
    assert spelling.execute(SpellingRequest("famos", SearchField.FILENAME)).proposed_query is None
    with pytest.raises(SnapshotUnavailable):
        spelling.execute(SpellingRequest("famos", snapshot_id="missing"))
    with pytest.raises(InvalidInput):
        spelling.execute(SpellingRequest('"famos', SearchField.BOTH))
    if persistent:
        repo.close()
        reopened = SqliteSnapshotRepository(tmp_path / "index")
        assert SuggestSpellingCorrections(reopened).execute(
            SpellingRequest("someting", SearchField.CONTENT)).proposed_query == "something"
        reopened.close()


@pytest.mark.parametrize(("query", "expected"), [
    ("ricerca", None),
    ("ricerca documenti", None),
    ("ricerac documenti", "ricerca documenti"),
    ("ricerca documeti", "ricerca documenti"),
    ("famos entrepreneurs", "famous entrepreneurs"),
    ("from Heathrow", None),
    ("form Heathrow", None),
])
def test_synthetic_it_en_ground_truth(query, expected):
    repo = InMemorySnapshotRepository()
    publish(repo, "N", [("notes.txt", "ricerca documenti famous entrepreneurs form Heathrow")])
    assert SuggestSpellingCorrections(repo).execute(
        SpellingRequest(query, SearchField.CONTENT)).proposed_query == expected
