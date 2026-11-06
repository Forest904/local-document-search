"""Pipeline M2 in memoria: documenti canonici, build, freeze e ricerca."""
from datetime import datetime, timezone

from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentId, DocumentMetadata,
    FileFingerprint, RelativePath,
)
from local_document_search.domain.queries import QueryEvaluator, QueryParser, SearchField
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft


def test_canonical_documents_to_searchable_snapshot():
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    for number, (path, text) in enumerate((
        ("notes/Report2026Finale.txt", "machine deep\nlearning"),
        ("machine.txt", "deep learning"),
        ("empty.txt", ""),
    )):
        metadata = DocumentMetadata(
            RelativePath(path), path.rsplit("/", 1)[-1], DocumentFormat.TXT,
            FileFingerprint(len(text.encode("utf-8")), 123),
        )
        builder.add(DocumentId(number), CanonicalDocument(metadata, text))
    snapshot = draft.freeze(
        snapshot_id="synthetic", root_directory="C:/synthetic",
        created_at=datetime(2026, 11, 6, tzinfo=timezone.utc),
        schema_version="1", processing_version="1",
    )
    parser, evaluator = QueryParser(), QueryEvaluator()
    matches = evaluator.evaluate(parser.parse('machine "deep learning"'), snapshot)
    assert len(matches) == 1
    assert matches[0].document_id == DocumentId(0)
    assert matches[0].matched_fields == frozenset({SearchField.CONTENT})
    assert evaluator.evaluate(parser.parse('"report 2026 finale"', SearchField.FILENAME), snapshot)[0].document_id == DocumentId(0)
    builder.remove(RelativePath("notes/Report2026Finale.txt"))
    assert evaluator.evaluate(parser.parse('machine "deep learning"'), snapshot) == matches
