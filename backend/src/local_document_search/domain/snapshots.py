"""Aggregato immutabile e consistente; nessuna persistenza o attivazione."""
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from .analysis import ContentAnalyzer, FilenameAnalyzer, Token, prepare_filename
from .documents import (
    CanonicalDocument, DocumentDescriptor, DocumentId, DocumentMetadata,
    IndexedDocument, RelativePath,
)
from .index import PositionalIndex, Posting


class EntryOutcome(StrEnum):
    INDEXED = "indexed"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class FileEntry:
    metadata: DocumentMetadata
    outcome: EntryOutcome
    document_id: DocumentId | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.outcome is EntryOutcome.INDEXED:
            if self.document_id is None or self.reason is not None:
                raise ValueError("Entry indicizzata: ID richiesto, nessuna esclusione")
        elif self.outcome is EntryOutcome.EXCLUDED:
            if self.document_id is not None or not self.reason or not self.reason.strip():
                raise ValueError("Entry esclusa: motivazione richiesta, nessun ID")
        else:
            raise ValueError("Esito manifest non valido")


@dataclass(frozen=True)
class IndexManifest:
    entries: Mapping[RelativePath, FileEntry]

    def __post_init__(self) -> None:
        entries = dict(self.entries)
        if any(path != entry.metadata.relative_path for path, entry in entries.items()):
            raise ValueError("Chiave manifest non coerente")
        object.__setattr__(self, "entries", MappingProxyType(entries))


@dataclass(frozen=True)
class DocumentCatalog:
    documents: Mapping[DocumentId, IndexedDocument]

    def __post_init__(self) -> None:
        documents = dict(self.documents)
        if any(key != doc.descriptor.document_id for key, doc in documents.items()):
            raise ValueError("Chiave catalogo non coerente")
        object.__setattr__(self, "documents", MappingProxyType(documents))


@dataclass(frozen=True)
class IndexSnapshot:
    snapshot_id: str
    root_directory: str
    created_at: datetime
    schema_version: str
    processing_version: str
    manifest: IndexManifest
    catalog: DocumentCatalog
    filename_index: PositionalIndex
    content_index: PositionalIndex
    ordered_document_ids: tuple[DocumentId, ...] = field(init=False)

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (
            self.snapshot_id, self.root_directory, self.schema_version,
            self.processing_version,
        )):
            raise ValueError("Identità, radice e versioni richieste")
        documents = self.catalog.documents
        referenced = set()
        for entry in self.manifest.entries.values():
            if entry.outcome is EntryOutcome.INDEXED:
                doc = documents.get(entry.document_id)
                if doc is None or doc.descriptor.metadata != entry.metadata:
                    raise ValueError("Manifest e catalogo non coerenti")
                if entry.document_id in referenced:
                    raise ValueError("ID ripetuto nel manifest")
                referenced.add(entry.document_id)
        if referenced != set(documents):
            raise ValueError("Documenti senza entry indicizzata")
        object.__setattr__(self, "ordered_document_ids", tuple(sorted(
            documents, key=lambda key: documents[key].descriptor.metadata.relative_path.value,
        )))
        for index, count_attribute in (
            (self.filename_index, "filename_token_count"),
            (self.content_index, "content_token_count"),
        ):
            if index.vocabulary != tuple(sorted(index.terms)):
                raise ValueError("Vocabolario non coerente con i posting")
            seen: dict[DocumentId, bytearray] = {
                key: bytearray((getattr(doc, count_attribute) + 7) // 8)
                for key, doc in documents.items()
            }
            observed: dict[DocumentId, int] = dict.fromkeys(documents, 0)
            for postings in index.terms.values():
                for document_id, posting in postings.items():
                    if document_id not in documents:
                        raise ValueError("Posting riferita a ID sconosciuto")
                    count = getattr(documents[document_id], count_attribute)
                    bitset = seen[document_id]
                    for position in posting.positions:
                        if position >= count:
                            raise ValueError("Posizione fuori range o assegnata due volte")
                        byte = position >> 3
                        mask = 1 << (position & 7)
                        if bitset[byte] & mask:
                            raise ValueError("Posizione fuori range o assegnata due volte")
                        bitset[byte] |= mask
                    observed[document_id] += len(posting.positions)
            for document_id, count in observed.items():
                if count != getattr(documents[document_id], count_attribute):
                    raise ValueError("Posting incomplete rispetto al conteggio token")


@dataclass
class SnapshotDraft:
    """Stato di costruzione privato al writer, mai interrogato dall'evaluator."""

    entries: dict[RelativePath, FileEntry] = field(default_factory=dict)
    documents: dict[DocumentId, IndexedDocument] = field(default_factory=dict)
    filename_terms: dict[str, dict[DocumentId, Posting]] = field(default_factory=dict)
    content_terms: dict[str, dict[DocumentId, Posting]] = field(default_factory=dict)

    def freeze(
        self, *, snapshot_id: str, root_directory: str, created_at: datetime,
        schema_version: str, processing_version: str,
    ) -> IndexSnapshot:
        return IndexSnapshot(
            snapshot_id, root_directory, created_at, schema_version, processing_version,
            IndexManifest(self.entries), DocumentCatalog(self.documents),
            PositionalIndex(self.filename_terms), PositionalIndex(self.content_terms),
        )


class IndexBuilder:
    """Modifica un draft con ID assegnati dal chiamante; nessun I/O."""

    def __init__(self, draft: SnapshotDraft) -> None:
        self.draft = draft

    def add(self, document_id: DocumentId, document: CanonicalDocument) -> None:
        if document_id in self.draft.documents or document.metadata.relative_path in self.draft.entries:
            raise ValueError("ID o percorso già presente")
        self._write(document_id, document)

    def replace(self, document_id: DocumentId, document: CanonicalDocument) -> None:
        old = self.draft.documents.get(document_id)
        if old is None or old.descriptor.metadata.relative_path != document.metadata.relative_path:
            raise ValueError("Sostituzione richiesta sullo stesso ID e percorso")
        self._write(document_id, document)

    def _write(self, document_id: DocumentId, document: CanonicalDocument) -> None:
        filename = FilenameAnalyzer().analyze(prepare_filename(document.metadata.filename))
        content = ContentAnalyzer().analyze(document.content)
        indexed = IndexedDocument(
            DocumentDescriptor(document_id, document.metadata), document.content,
            len(filename), len(content),
        )
        entry = FileEntry(document.metadata, EntryOutcome.INDEXED, document_id)
        filename_postings = self._postings(filename)
        content_postings = self._postings(content)
        self.remove(document.metadata.relative_path)
        self.draft.documents[document_id] = indexed
        self.draft.entries[document.metadata.relative_path] = entry
        for terms, postings in (
            (self.draft.filename_terms, filename_postings),
            (self.draft.content_terms, content_postings),
        ):
            for term, posting in postings.items():
                terms.setdefault(term, {})[document_id] = posting

    @staticmethod
    def _postings(tokens: tuple[Token, ...]) -> dict[str, Posting]:
        positions: dict[str, list[int]] = {}
        for token in tokens:
            positions.setdefault(token.term, []).append(token.position)
        return {term: Posting(tuple(values)) for term, values in positions.items()}

    def remove(self, path: RelativePath) -> None:
        """Rimuove il percorso se presente, incluse tutte le occorrenze."""
        entry = self.draft.entries.pop(path, None)
        if entry is None or entry.document_id is None:
            return
        del self.draft.documents[entry.document_id]
        for terms in (self.draft.filename_terms, self.draft.content_terms):
            for term in list(terms):
                terms[term].pop(entry.document_id, None)
                if not terms[term]:
                    del terms[term]

    def exclude(self, metadata: DocumentMetadata, reason: str) -> None:
        entry = FileEntry(metadata, EntryOutcome.EXCLUDED, reason=reason)
        self.remove(metadata.relative_path)
        self.draft.entries[metadata.relative_path] = entry
