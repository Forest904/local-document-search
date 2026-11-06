from dataclasses import FrozenInstanceError, replace

import pytest

from local_document_search.domain.analysis import Token
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentDescriptor, DocumentFormat, DocumentId,
    DocumentMetadata, FileFingerprint, IndexedDocument, RelativePath,
)
from local_document_search.domain.index import PositionalIndex, Posting
from local_document_search.domain.queries import PhraseClause, SearchField, SearchQuery, TermsClause


@pytest.mark.parametrize("value", [-1, True, 1.5])
def test_invalid_identity(value):
    with pytest.raises(ValueError):
        DocumentId(value)


@pytest.mark.parametrize("path", ["", "/a.txt", "../a", "a/../b", "a//b", "./a", "C:/a", "a\\b"])
def test_invalid_relative_path(path):
    with pytest.raises(ValueError):
        RelativePath(path)


def test_paths_preserve_case_unicode_and_distinct_directories():
    paths = ["A/Caffè.txt", "a/Caffè.txt", "A/Caffe\u0300.txt", "B/Caffè.txt"]
    values = [RelativePath(p) for p in paths]
    assert [p.value for p in values] == paths
    assert len(set(values)) == 4


@pytest.mark.parametrize("size,mtime", [(-1, 0), (True, 0), (0, 1.5)])
def test_invalid_fingerprint(size, mtime):
    with pytest.raises(ValueError):
        FileFingerprint(size, mtime)


def test_pre_epoch_timestamp_and_empty_document_are_valid():
    metadata = DocumentMetadata(RelativePath("empty.txt"), "empty.txt", DocumentFormat.TXT, FileFingerprint(0, -1))
    canonical = CanonicalDocument(metadata, "")
    assert canonical.content == ""
    assert not hasattr(canonical, "document_id")
    document = IndexedDocument(DocumentDescriptor(DocumentId(0), metadata), "", 0, 0)
    with pytest.raises(FrozenInstanceError):
        document.extracted_text = "changed"
    with pytest.raises(ValueError):
        replace(document, content_token_count=-1)
    with pytest.raises(ValueError):
        replace(metadata, filename="other.txt")


@pytest.mark.parametrize("term,position", [("", 0), (" ", 0), ("a", -1), ("a", True)])
def test_invalid_tokens(term, position):
    with pytest.raises(ValueError):
        Token(term, position)


@pytest.mark.parametrize("positions", [[], [-1], [1, 1], [2, 1], [True], [0.5]])
def test_invalid_postings(positions):
    with pytest.raises(ValueError):
        Posting(positions)


def test_index_copies_every_mutable_container():
    positions = [0, 2]
    posting = Posting(positions)
    postings = {DocumentId(1): posting}
    terms = {"data": postings}
    index = PositionalIndex(terms)
    positions.append(3)
    postings.clear()
    terms.clear()
    assert index.terms["data"][DocumentId(1)].positions == (0, 2)
    with pytest.raises(TypeError):
        index.terms["data"][DocumentId(2)] = posting
    with pytest.raises(TypeError):
        index.terms["new"] = {}


@pytest.mark.parametrize("terms", [{"": {DocumentId(1): Posting((0,))}}, {"word": {}}])
def test_empty_terms_or_posting_lists_rejected(terms):
    with pytest.raises(ValueError):
        PositionalIndex(terms)


def test_query_keeps_text_for_each_analyzer_and_copies_clauses():
    clauses = [TermsClause("HTTPServer"), PhraseClause("deep learning")]
    query = SearchQuery(clauses)
    clauses.clear()
    assert query.field is SearchField.BOTH
    assert query.clauses == (TermsClause("HTTPServer"), PhraseClause("deep learning"))


@pytest.mark.parametrize("factory", [lambda: SearchQuery([]), lambda: TermsClause(" "), lambda: PhraseClause(""), lambda: SearchQuery(["a"]), lambda: SearchQuery([TermsClause("a")], "bad")])
def test_invalid_structured_query(factory):
    with pytest.raises(ValueError):
        factory()
