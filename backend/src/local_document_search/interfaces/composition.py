"""Composizione esplicita M1 e cablaggio operativo della sessione multiformato M4."""
from dataclasses import dataclass, field
import os
from pathlib import Path
from threading import Lock
from local_document_search.application.lifecycle import (
    ApplicationLifecycle, InitializeApplication, SelectDirectory,
    RunSynchronization, GetIndexStatus, ClearLocalData,
    RebuildIndex, RecoverPreviousSnapshot,
)
from local_document_search.infrastructure.settings_storage import SqliteSettingsRepository
from local_document_search.infrastructure.persistent_storage import PersistentSnapshotRepository

from local_document_search.application.search import GetDocument, SearchDocuments, SuggestTerms, SuggestSpellingCorrections, ReadRuntime
from local_document_search.application.jobs import RequestSynchronization, GetJobStatus, CancelSynchronization
from local_document_search.infrastructure.storage_lock import StorageLock
from local_document_search.application.synchronization import BuildIndex, IndexSynchronizer
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery, resolve_directory
from local_document_search.infrastructure.readers.text import TextReader
from local_document_search.infrastructure.readers.markdown import MarkdownReader
from local_document_search.infrastructure.readers.pdf import PdfReader
from local_document_search.infrastructure.readers.registry import DocumentReader
from local_document_search.domain.documents import DocumentFormat
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.application.errors import StorageFailure
from local_document_search.application.preferences import GetDesktopPreferences, SaveDesktopPreferences
from local_document_search.infrastructure.sqlite_snapshot_storage import storage_directory

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


def _create_reader():
    return DocumentReader({DocumentFormat.TXT: TextReader(),
                           DocumentFormat.MARKDOWN: MarkdownReader(),
                           DocumentFormat.PDF: PdfReader()})


@dataclass
class PersistentApplication:
    initialize: InitializeApplication
    select_directory: SelectDirectory
    synchronize: RunSynchronization
    status: GetIndexStatus
    clear_local_data: ClearLocalData
    rebuild: RebuildIndex
    recover_previous: RecoverPreviousSnapshot
    search: SearchDocuments
    suggest: SuggestTerms
    get_document: GetDocument
    snapshots: PersistentSnapshotRepository
    request_synchronization: RequestSynchronization
    job_status: GetJobStatus
    cancel_synchronization: CancelSynchronization
    _lifecycle: ApplicationLifecycle
    _reads: ReadRuntime
    _storage_lock: StorageLock
    get_preferences: GetDesktopPreferences | None = None
    save_preferences: SaveDesktopPreferences | None = None
    suggest_spelling: SuggestSpellingCorrections | None = None
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


def desktop_storage_directory():
    """Percorso pubblico stabile, separato dagli storage storici."""
    if os.name != "nt" or not os.environ.get("LOCALAPPDATA"):
        raise StorageFailure("Directory applicativa esplicita richiesta")
    directory = Path(os.environ["LOCALAPPDATA"]) / "LocalDocumentSearch" / "Data"
    if any(node.is_symlink() or node.is_junction() for node in (directory, *directory.parents)):
        raise StorageFailure("Collegamenti non consentiti nel percorso dei dati locali")
    return directory


def compose_persistent_application(storage=None, *, v2=False, read_workers=None):
    """Acquisisce lo storage prima di aprire database; initialize avvia il job."""
    if v2:
        if storage is None:
            storage = desktop_storage_directory()
        storage = storage_directory(storage)
        if ((storage / "control.sqlite3").exists() or (storage / "snapshots.sqlite3").exists()
                or ((storage / "document-ids.sqlite3").exists()
                    and not (storage / "control-v2.sqlite3").exists())):
            raise StorageFailure("Storage v1: scegliere una directory v2 distinta")
    lock = StorageLock(storage)
    settings = snapshots = lifecycle = reads = None
    try:
        settings = SqliteSettingsRepository(lock.directory,
            database_name="control-v2.sqlite3" if v2 else "control.sqlite3",
            legacy_detection=not v2)
        snapshots = (PersistentSnapshotRepository(settings, v2=True) if v2
                     else PersistentSnapshotRepository(settings))
        reader = _create_reader()
        lifecycle = ApplicationLifecycle(settings, snapshots,
                                        IndexSynchronizer(DocumentFileDiscovery(), reader, snapshots,
                                                          schema_version="2" if v2 else "1",
                                                          read_workers=(read_workers if read_workers is not None
                                                                        else (2 if v2 else 1)),
                                                          worker_reader_factory=_create_reader if v2 else None),
                                        resolve_directory)
        reads = ReadRuntime()
        return PersistentApplication(
            InitializeApplication(lifecycle), SelectDirectory(lifecycle),
            RunSynchronization(lifecycle), GetIndexStatus(lifecycle), ClearLocalData(lifecycle),
            RebuildIndex(lifecycle), RecoverPreviousSnapshot(lifecycle),
            SearchDocuments(snapshots, reads), SuggestTerms(snapshots, reads),
            GetDocument(snapshots, reads), snapshots,
            RequestSynchronization(lifecycle), GetJobStatus(lifecycle.jobs),
            CancelSynchronization(lifecycle.jobs), lifecycle, reads, lock,
            GetDesktopPreferences(settings) if v2 else None,
            SaveDesktopPreferences(settings) if v2 else None,
            suggest_spelling=SuggestSpellingCorrections(snapshots, reads) if v2 else None)
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


def compose_v2_application(storage=None, *, read_workers=2):
    """Sessione desktop v2, isolata dal formato persistente v1."""
    return compose_persistent_application(storage, v2=True, read_workers=read_workers)
