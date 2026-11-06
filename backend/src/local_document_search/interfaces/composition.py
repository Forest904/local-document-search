"""Composizione esplicita M1 e cablaggio operativo della sessione multiformato M4."""
from dataclasses import dataclass

from local_document_search.application.search import SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery, resolve_directory
from local_document_search.infrastructure.readers.text import TextReader
from local_document_search.infrastructure.readers.markdown import MarkdownReader
from local_document_search.infrastructure.readers.pdf import PdfReader
from local_document_search.infrastructure.readers.registry import DocumentReader
from local_document_search.domain.documents import DocumentFormat
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository

from local_document_search.application.ports import (
    DocumentReaderPort, FileDiscoveryPort, SettingsRepositoryPort,
    SnapshotRepositoryPort,
)


@dataclass(frozen=True)
class ApplicationDependencies:
    discovery: FileDiscoveryPort
    reader: DocumentReaderPort
    snapshots: SnapshotRepositoryPort
    settings: SettingsRepositoryPort


def compose_application(
    *, discovery: FileDiscoveryPort, reader: DocumentReaderPort,
    snapshots: SnapshotRepositoryPort, settings: SettingsRepositoryPort,
) -> ApplicationDependencies:
    """Raccoglie le dipendenze; non costruisce ancora un'applicazione operativa."""
    return ApplicationDependencies(discovery, reader, snapshots, settings)


@dataclass(frozen=True)
class CliApplication:
    root_directory: str
    build: BuildIndex
    search: SearchDocuments


def compose_cli(directory: str) -> CliApplication:
    """Una sessione multiformato, un repository volatile e un writer bloccante."""
    root = resolve_directory(directory)
    snapshots = InMemorySnapshotRepository()
    reader = DocumentReader({DocumentFormat.TXT: TextReader(),
                             DocumentFormat.MARKDOWN: MarkdownReader(),
                             DocumentFormat.PDF: PdfReader()})
    return CliApplication(root, BuildIndex(DocumentFileDiscovery(), reader, snapshots),
                          SearchDocuments(snapshots))
