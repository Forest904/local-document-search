from dataclasses import replace

import pytest

from local_document_search.application.contracts import (
    DocumentDetails, InvalidInput, SearchRequest, SearchResponse, SearchResult,
)
from local_document_search.application.ports import Extracted, Excluded, ExtractionFailed
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentId, DocumentMetadata,
    FileFingerprint, RelativePath,
)
from local_document_search.domain.queries import SearchField


@pytest.mark.parametrize("kwargs", [{"query": ""}, {"limit": 0}, {"limit": True}, {"offset": -1}, {"offset": 0.5}, {"field": "invalid"}])
def test_invalid_request(kwargs):
    with pytest.raises(InvalidInput):
        SearchRequest(**({"query": "data"} | kwargs))


def test_request_defaults_and_parser_deferred():
    request = SearchRequest("data")
    assert (request.field, request.limit, request.offset) == (SearchField.BOTH, 50, 0)
    assert SearchRequest('"unclosed').query == '"unclosed'


def test_response_copies_collections_and_empty_page_keeps_total():
    fields = {SearchField.CONTENT}
    result = SearchResult(DocumentId(1), "a.txt", RelativePath("a.txt"), DocumentFormat.TXT, fields)
    results = [result]
    response = SearchResponse("s1", results, 1)
    fields.clear()
    results.clear()
    assert response.results[0].matched_fields == frozenset({SearchField.CONTENT})
    assert SearchResponse("s1", [], 12).total_matches == 12
    assert SearchResponse("s1", [], 0).snapshot_id == "s1"
    with pytest.raises(ValueError):
        replace(result, matched_fields={SearchField.BOTH})
    with pytest.raises(ValueError):
        replace(response, total_matches=0)


def test_reader_outcomes_preserve_success_exclusion_and_failure():
    metadata = DocumentMetadata(RelativePath("a.txt"), "a.txt", DocumentFormat.TXT, FileFingerprint(0, 0))
    document = CanonicalDocument(metadata, "")
    assert Extracted(document).document.content == ""
    assert type(Excluded("no text")) is not type(ExtractionFailed("bad encoding"))
    for outcome in (Excluded, ExtractionFailed):
        with pytest.raises(ValueError):
            outcome("")
    details = DocumentDetails("s1", DocumentId(1), metadata, "")
    assert details.extracted_text == ""
