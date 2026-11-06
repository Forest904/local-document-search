"""Aggregato immutabile e consistente; nessuna persistenza o attivazione."""
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from .documents import DocumentId, DocumentMetadata, IndexedDocument, RelativePath
from .index import PositionalIndex


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
        for index, count_attribute in (
            (self.filename_index, "filename_token_count"),
            (self.content_index, "content_token_count"),
        ):
            seen: dict[DocumentId, set[int]] = {key: set() for key in documents}
            for postings in index.terms.values():
                for document_id, posting in postings.items():
                    if document_id not in documents:
                        raise ValueError("Posting riferita a ID sconosciuto")
                    count = getattr(documents[document_id], count_attribute)
                    for position in posting.positions:
                        if position >= count or position in seen[document_id]:
                            raise ValueError("Posizione fuori range o assegnata due volte")
                        seen[document_id].add(position)
            for document_id, positions in seen.items():
                if len(positions) != getattr(documents[document_id], count_attribute):
                    raise ValueError("Posting incomplete rispetto al conteggio token")
