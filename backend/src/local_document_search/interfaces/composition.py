"""Composizione esplicita M1 e cablaggio operativo della sessione multiformato M4."""
from dataclasses import dataclass, field
from threading import Lock
from local_document_search.application.lifecycle import (
    ApplicationLifecycle, InitializeApplication, SelectDirectory,
    RunSynchronization, GetIndexStatus, ClearLocalData,
)
from local_document_search.infrastructure.settings_storage import SqliteSettingsRepository
from local_document_search.infrastructure.persistent_storage import PersistentSnapshotRepository

from local_document_search.application.search import GetDocument, SearchDocuments, ReadRuntime
from local_document_search.application.jobs import RequestSynchronization, GetJobStatus
from local_document_search.infrastructure.storage_lock import StorageLock
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


@dataclass
class PersistentApplication:
    initialize: InitializeApplication
    select_directory: SelectDirectory
    synchronize: RunSynchronization
    status: GetIndexStatus
    clear_local_data: ClearLocalData
    search: SearchDocuments
    get_document: GetDocument
    snapshots: PersistentSnapshotRepository
    request_synchronization: RequestSynchronization
    job_status: GetJobStatus
    _lifecycle: ApplicationLifecycle
    _reads: ReadRuntime
    _storage_lock: StorageLock
    _close_lock: Lock = field(default_factory=Lock)
    _closed: bool = False

    def close(self):
        with self._close_lock:
            if self._closed:
                return
            self._lifecycle.jobs.stop_accepting()
            self._reads.stop_accepting()
            self._lifecycle.jobs.close()
            self._reads.close()
            self.snapshots.close()
            self._storage_lock.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def compose_persistent_application(storage=None):
    """Acquisisce lo storage prima di aprire database; initialize avvia il job."""
    lock = StorageLock(storage)
    settings = snapshots = lifecycle = reads = None
    try:
        settings = SqliteSettingsRepository(lock.directory)
        snapshots = PersistentSnapshotRepository(settings)
        reader = DocumentReader({DocumentFormat.TXT: TextReader(),
                                 DocumentFormat.MARKDOWN: MarkdownReader(),
                                 DocumentFormat.PDF: PdfReader()})
        lifecycle = ApplicationLifecycle(settings, snapshots,
                                        IndexSynchronizer(DocumentFileDiscovery(), reader, snapshots),
                                        resolve_directory)
        reads = ReadRuntime()
        return PersistentApplication(
            InitializeApplication(lifecycle), SelectDirectory(lifecycle),
            RunSynchronization(lifecycle), GetIndexStatus(lifecycle), ClearLocalData(lifecycle),
            SearchDocuments(snapshots, reads), GetDocument(snapshots, reads), snapshots,
            RequestSynchronization(lifecycle), GetJobStatus(lifecycle.jobs), lifecycle, reads, lock)
    except BaseException:
        try:
            if lifecycle is not None:
                lifecycle.jobs.close()
            if reads is not None:
                reads.close()
            if snapshots is not None:
                snapshots.close()
            elif settings is not None:
                settings.close()
        finally:
            lock.close()
        raise
