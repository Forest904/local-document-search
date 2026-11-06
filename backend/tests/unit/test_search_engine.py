"""Accettazione M2 con soli testi e metadati sintetici, senza filesystem."""
from datetime import datetime, timezone

import pytest

from local_document_search.domain.analysis import ContentAnalyzer, FilenameAnalyzer, prepare_filename
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentId, DocumentMetadata,
    FileFingerprint, RelativePath,
)
from local_document_search.domain.queries import (
    PhraseClause, QueryEvaluator, QueryParser, SearchField, SearchMatch, SearchQuery, TermsClause,
)
from local_document_search.domain.snapshots import EntryOutcome, IndexBuilder, SnapshotDraft


def document(path, text):
    return CanonicalDocument(
        DocumentMetadata(RelativePath(path), path.rsplit("/", 1)[-1], DocumentFormat.TXT, FileFingerprint(10, 1)),
        text,
    )


def freeze(draft, name="s1"):
    return draft.freeze(
        snapshot_id=name, root_directory="C:/synthetic", created_at=datetime(2026, 11, 6, tzinfo=timezone.utc),
        schema_version="1", processing_version="1",
    )


def snapshot_of(*documents):
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    for number, doc in enumerate(documents):
        builder.add(DocumentId(number), doc)
    return freeze(draft)


def search(snapshot, text, field=SearchField.BOTH):
    return QueryEvaluator().evaluate(QueryParser().parse(text, field), snapshot)


@pytest.mark.parametrize("text,expected", [
    ("l'acqua l’acqua", ["l", "acqua", "l", "acqua"]),
    ("caffè caffe CAFFE\u0300", ["caffè", "caffe", "caffè"]),
    ("Straße STRASSE", ["strasse", "strasse"]),
    ("uno_due-tre.quattro😀cinque", ["uno", "due", "tre", "quattro", "cinque"]),
    ("\u0301 😀 !", []),
    ("a\u0338 b", ["a\u0338", "b"]),
    ("", []),
    ("data data", ["data", "data"]),
    ("the e di", ["the", "e", "di"]),
    ("Report2026Finale HTTPServer", ["report2026finale", "httpserver"]),
    ("١٢ ² Ⅳ", ["١٢", "²", "ⅳ"]),
])
def test_content_analysis(text, expected):
    tokens = ContentAnalyzer().analyze(text)
    assert [token.term for token in tokens] == expected
    assert [token.position for token in tokens] == list(range(len(expected)))


@pytest.mark.parametrize("text,expected", [
    ("Report2026Finale", ["report", "2026", "finale"]),
    ("HTTPServer", ["http", "server"]),
    ("XMLHTTPParser", ["xmlhttp", "parser"]),
    ("caffèLatte", ["caffè", "latte"]),
    ("caffe\u0300Latte", ["caffè", "latte"]),
    ("a\u0338B", ["a\u0338", "b"]),
    ("42Roma١٢Tre", ["42", "roma", "١٢", "tre"]),
    ("Report.txt", ["report", "txt"]),
])
def test_filename_analysis(text, expected):
    tokens = FilenameAnalyzer().analyze(text)
    assert [token.term for token in tokens] == expected
    assert [token.position for token in tokens] == list(range(len(expected)))


@pytest.mark.parametrize("name,expected", [
    ("Report.TXT", "Report"), ("HTTPServer.md", "HTTPServer"),
    ("a.txt.pdf", "a.txt"), ("a.csv", "a.csv"), ("a", "a"), (".txt", ""),
])
def test_only_final_supported_source_suffix_removed(name, expected):
    assert prepare_filename(name) == expected


def test_parser_preserves_clause_text_and_field():
    query = QueryParser().parse('Machine "Deep Learning" OR NOT', SearchField.CONTENT)
    assert query == SearchQuery((TermsClause("Machine "), PhraseClause("Deep Learning"), TermsClause(" OR NOT")), SearchField.CONTENT)
    assert QueryParser().parse('a"b""c"').clauses == (TermsClause("a"), PhraseClause("b"), PhraseClause("c"))


@pytest.mark.parametrize("text", ["", "  ", '""', '"  "', '"abc', 'abc"', "!!!", 'abc "!!!"', '!!! "abc"'])
@pytest.mark.parametrize("field", list(SearchField))
def test_invalid_queries_rejected_even_on_empty_snapshot(text, field):
    with pytest.raises(ValueError):
        search(snapshot_of(), text, field)


def test_structured_query_cannot_bypass_validation():
    query = SearchQuery((TermsClause("missing"), PhraseClause("!!!")))
    with pytest.raises(ValueError, match="senza token"):
        QueryEvaluator().evaluate(query, snapshot_of())


@pytest.mark.parametrize("query,expected", [
    ("roma tre", [0, 1, 2]),
    ('"roma tre"', [0]),
    ('"tre roma"', [2]),
    ('"roma tre quattro cinque"', []),
    ('"data data"', [0, 2]),
    ('"data data data"', [2]),
    ("data data data", [0, 1, 2]),
    ('roma "data data"', [0, 2]),
    ("absent", []),
])
def test_and_phrase_and_repeated_terms(query, expected):
    snapshot = snapshot_of(
        document("a.txt", "Roma Tre data data"),
        document("b.txt", "Roma distante Tre data"),
        document("c.txt", "Tre Roma data data data"),
    )
    assert [match.document_id.value for match in search(snapshot, query, SearchField.CONTENT)] == expected


def test_both_requires_whole_query_in_each_field_and_reports_fields():
    snapshot = snapshot_of(
        document("machine.txt", "deep learning"),
        document("machineDeepLearning.txt", "machine deep learning"),
        document("z.txt", "machine deep learning"),
    )
    matches = search(snapshot, 'machine "deep learning"')
    assert matches == (
        SearchMatch(DocumentId(1), frozenset({SearchField.FILENAME, SearchField.CONTENT})),
        SearchMatch(DocumentId(2), frozenset({SearchField.CONTENT})),
    )
    assert [match.document_id for match in search(snapshot, "machine learning", SearchField.FILENAME)] == [DocumentId(1)]


def test_field_specific_analysis_suffix_and_original_text():
    original = "Report2026Finale\nCAFFE\u0300"
    snapshot = snapshot_of(document("Report2026Finale.txt", original))
    assert search(snapshot, "Report2026Finale")[0].matched_fields == frozenset({SearchField.FILENAME, SearchField.CONTENT})
    assert search(snapshot, "report 2026 finale")[0].matched_fields == frozenset({SearchField.FILENAME})
    assert not search(snapshot, "txt")
    assert not search(snapshot, "Report2026Finale.txt", SearchField.FILENAME)
    assert search(snapshot, "caffè", SearchField.CONTENT)
    assert not search(snapshot, "caffe", SearchField.CONTENT)
    assert snapshot.catalog.documents[DocumentId(0)].extracted_text == original


def test_order_preserves_case_unicode_and_distinct_paths():
    paths = ["é/a.txt", "b/a.txt", "A/a.txt", "e\u0301/a.txt"]
    snapshot = snapshot_of(*(document(path, "common") for path in paths))
    matches = search(snapshot, "common")
    assert [paths[match.document_id.value] for match in matches] == sorted(paths)


def test_empty_documents_and_empty_snapshot():
    snapshot = snapshot_of(document("empty.txt", ""), document(".txt", ""))
    assert len(search(snapshot, "empty")) == 1
    assert not search(snapshot, "empty", SearchField.CONTENT)
    assert not search(snapshot_of(), "anything")
    assert snapshot.catalog.documents[DocumentId(1)].filename_token_count == 0


def test_builder_replacement_removal_exclusion_and_snapshot_isolation():
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    original = document("dataData.txt", "data data old")
    builder.add(DocumentId(7), original)
    builder.add(DocumentId(8), document("other.txt", "old"))
    first = freeze(draft)
    assert first.filename_index.terms["data"][DocumentId(7)].positions == (0, 1)
    assert first.content_index.terms["data"][DocumentId(7)].positions == (0, 1)
    builder.replace(DocumentId(7), document("dataData.txt", "new"))
    builder.remove(RelativePath("other.txt"))
    second = freeze(draft, "s2")
    assert not search(second, "old")
    assert search(second, "new")[0].document_id == DocumentId(7)
    assert "old" not in draft.content_terms
    builder.exclude(original.metadata, "synthetic exclusion")
    third = freeze(draft, "s3")
    assert third.manifest.entries[original.metadata.relative_path].outcome is EntryOutcome.EXCLUDED
    assert not third.catalog.documents and not third.filename_index.terms and not third.content_index.terms
    builder.remove(original.metadata.relative_path)
    builder.remove(original.metadata.relative_path)
    assert not freeze(draft).manifest.entries
    assert len(search(first, "old")) == 2
    assert search(second, "new")
    with pytest.raises(TypeError):
        first.filename_index.terms["data"][DocumentId(7)] = None


def test_builder_rejects_conflicts_without_changing_valid_draft():
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    source = document("a.txt", "original")
    builder.add(DocumentId(1), source)
    for action in (
        lambda: builder.add(DocumentId(1), document("b.txt", "bad")),
        lambda: builder.add(DocumentId(2), source),
        lambda: builder.replace(DocumentId(2), source),
        lambda: builder.replace(DocumentId(1), document("b.txt", "bad")),
        lambda: builder.exclude(source.metadata, ""),
    ):
        with pytest.raises(ValueError):
            action()
        assert search(freeze(draft), "original")[0].document_id == DocumentId(1)


def test_excluded_path_can_be_removed_then_indexed():
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    source = document("a.txt", "text")
    builder.exclude(source.metadata, "synthetic")
    with pytest.raises(ValueError):
        builder.add(DocumentId(1), source)
    builder.remove(source.metadata.relative_path)
    builder.add(DocumentId(1), source)
    assert search(freeze(draft), "text")


def test_draft_cannot_be_searched_and_match_fields_are_immutable():
    with pytest.raises(ValueError):
        QueryEvaluator().evaluate(QueryParser().parse("text"), SnapshotDraft())
    fields = {SearchField.CONTENT}
    match = SearchMatch(DocumentId(1), fields)
    fields.clear()
    assert match.matched_fields == frozenset({SearchField.CONTENT})
    with pytest.raises(ValueError):
        SearchMatch(DocumentId(1), {SearchField.BOTH})
