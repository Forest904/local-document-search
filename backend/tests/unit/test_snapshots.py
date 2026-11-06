from dataclasses import replace
from datetime import datetime, timezone

import pytest

from local_document_search.domain.documents import (
    DocumentDescriptor, DocumentFormat, DocumentId, DocumentMetadata,
    FileFingerprint, IndexedDocument, RelativePath,
)
from local_document_search.domain.index import PositionalIndex, Posting
from local_document_search.domain.snapshots import (
    DocumentCatalog, EntryOutcome, FileEntry, IndexManifest, IndexSnapshot,
)


@pytest.fixture
def snapshot():
    metadata = DocumentMetadata(RelativePath("report.txt"), "report.txt", DocumentFormat.TXT, FileFingerprint(9, 10))
    document_id = DocumentId(1)
    document = IndexedDocument(DocumentDescriptor(document_id, metadata), "data data", 1, 2)
    return IndexSnapshot(
        "s1", "C:/synthetic", datetime(2026, 11, 6, tzinfo=timezone.utc), "1", "1",
        IndexManifest({metadata.relative_path: FileEntry(metadata, EntryOutcome.INDEXED, document_id)}),
        DocumentCatalog({document_id: document}),
        PositionalIndex({"report": {document_id: Posting((0,))}}),
        PositionalIndex({"data": {document_id: Posting((0, 1))}}),
    )


def test_snapshot_has_independent_field_positions(snapshot):
    assert snapshot.filename_index.terms["report"][DocumentId(1)].positions == (0,)
    assert snapshot.content_index.terms["data"][DocumentId(1)].positions == (0, 1)


def test_catalog_and_manifest_copy_input(snapshot):
    entries = dict(snapshot.manifest.entries)
    documents = dict(snapshot.catalog.documents)
    copied = replace(snapshot, manifest=IndexManifest(entries), catalog=DocumentCatalog(documents))
    entries.clear()
    documents.clear()
    assert len(copied.manifest.entries) == len(copied.catalog.documents) == 1
    with pytest.raises(TypeError):
        copied.catalog.documents[DocumentId(2)] = next(iter(copied.catalog.documents.values()))
    with pytest.raises(TypeError):
        copied.manifest.entries[RelativePath("new.txt")] = next(iter(copied.manifest.entries.values()))


@pytest.mark.parametrize("terms", [
    {"data": {DocumentId(2): Posting((0, 1))}},
    {"data": {DocumentId(1): Posting((0, 2))}},
    {"data": {DocumentId(1): Posting((0,))}},
    {"data": {DocumentId(1): Posting((0, 1))}, "other": {DocumentId(1): Posting((1,))}},
])
def test_inconsistent_postings_rejected(snapshot, terms):
    with pytest.raises(ValueError):
        replace(snapshot, content_index=PositionalIndex(terms))


def test_missing_manifest_or_catalog_rejected(snapshot):
    with pytest.raises(ValueError):
        replace(snapshot, manifest=IndexManifest({}))
    with pytest.raises(ValueError):
        replace(snapshot, catalog=DocumentCatalog({}))


def test_changed_metadata_rejected(snapshot):
    doc = snapshot.catalog.documents[DocumentId(1)]
    metadata = replace(doc.descriptor.metadata, fingerprint=FileFingerprint(10, 11))
    changed = replace(doc, descriptor=replace(doc.descriptor, metadata=metadata))
    with pytest.raises(ValueError):
        replace(snapshot, catalog=DocumentCatalog({DocumentId(1): changed}))


def test_mapping_keys_must_match_values(snapshot):
    with pytest.raises(ValueError):
        DocumentCatalog({DocumentId(2): snapshot.catalog.documents[DocumentId(1)]})
    with pytest.raises(ValueError):
        IndexManifest({RelativePath("wrong.txt"): next(iter(snapshot.manifest.entries.values()))})


def test_excluded_entry_has_reason_and_no_document(snapshot):
    metadata = DocumentMetadata(RelativePath("image.pdf"), "image.pdf", DocumentFormat.PDF, FileFingerprint(100, 1))
    excluded = FileEntry(metadata, EntryOutcome.EXCLUDED, reason="no text")
    entries = dict(snapshot.manifest.entries)
    entries[metadata.relative_path] = excluded
    valid = replace(snapshot, manifest=IndexManifest(entries))
    assert len(valid.catalog.documents) == 1
    with pytest.raises(ValueError):
        replace(excluded, document_id=DocumentId(2))
    with pytest.raises(ValueError):
        replace(excluded, reason=None)
    with pytest.raises(ValueError):
        replace(excluded, outcome="failed")
    with pytest.raises(ValueError):
        FileEntry(metadata, EntryOutcome.INDEXED)


def test_empty_snapshot_valid_and_versions_required(snapshot):
    empty = replace(snapshot, manifest=IndexManifest({}), catalog=DocumentCatalog({}), filename_index=PositionalIndex({}), content_index=PositionalIndex({}))
    assert not empty.catalog.documents
    with pytest.raises(ValueError):
        replace(empty, processing_version="")
