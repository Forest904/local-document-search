"""Composizione esplicita M1 e cablaggio operativo della sessione TXT M3."""
from dataclasses import dataclass

from local_document_search.application.search import SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.infrastructure.filesystem import TextFileDiscovery, resolve_directory
from local_document_search.infrastructure.readers.text import TextReader
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
    """Una sessione TXT, un repository volatile e un writer bloccante."""
    root = resolve_directory(directory)
    snapshots = InMemorySnapshotRepository()
    return CliApplication(root, BuildIndex(TextFileDiscovery(), TextReader(), snapshots),
                          SearchDocuments(snapshots))
