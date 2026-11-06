"""Composizione esplicita M1 e cablaggio operativo della sessione multiformato M4."""
from dataclasses import dataclass
from local_document_search.application.lifecycle import (
    ApplicationLifecycle, InitializeApplication, SelectDirectory,
    RunSynchronization, GetIndexStatus, ClearLocalData,
)
from local_document_search.infrastructure.settings_storage import SqliteSettingsRepository
from local_document_search.infrastructure.persistent_storage import PersistentSnapshotRepository

from local_document_search.application.search import GetDocument, SearchDocuments
from local_document_search.application.synchronization import BuildIndex, IndexSynchronizer
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


@dataclass(frozen=True)
class PersistentApplication:
    initialize: InitializeApplication
    select_directory: SelectDirectory
    synchronize: RunSynchronization
    status: GetIndexStatus
    clear_local_data: ClearLocalData
    search: SearchDocuments
    get_document: GetDocument
    snapshots: PersistentSnapshotRepository

    def close(self):
        self.snapshots.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def compose_persistent_application(storage=None):
    """Sessione persistente bloccante; chiamare initialize dopo la composizione."""
    settings = SqliteSettingsRepository(storage)
    try:
        snapshots = PersistentSnapshotRepository(settings)
    except BaseException:
        settings.close()
        raise
    reader = DocumentReader({DocumentFormat.TXT: TextReader(),
                             DocumentFormat.MARKDOWN: MarkdownReader(),
                             DocumentFormat.PDF: PdfReader()})
    lifecycle = ApplicationLifecycle(settings, snapshots,
                                    IndexSynchronizer(DocumentFileDiscovery(), reader, snapshots),
                                    resolve_directory)
    return PersistentApplication(InitializeApplication(lifecycle), SelectDirectory(lifecycle),
                                 RunSynchronization(lifecycle), GetIndexStatus(lifecycle),
                                 ClearLocalData(lifecycle), SearchDocuments(snapshots),
                                 GetDocument(snapshots), snapshots)
