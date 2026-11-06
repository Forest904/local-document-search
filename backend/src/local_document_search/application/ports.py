"""Confini infrastrutturali, senza adapter o orchestrazione anticipati."""
from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from local_document_search.domain.documents import CanonicalDocument, DocumentMetadata
from local_document_search.domain.snapshots import IndexSnapshot


@dataclass(frozen=True)
class FileCandidate:
    root_directory: str
    metadata: DocumentMetadata


@dataclass(frozen=True)
class Extracted:
    document: CanonicalDocument


@dataclass(frozen=True)
class Excluded:
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("Motivazione richiesta")


@dataclass(frozen=True)
class ExtractionFailed:
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("Diagnostica richiesta")


type ReaderResult = Extracted | Excluded | ExtractionFailed


class FileDiscoveryPort(Protocol):
    def discover(self, root_directory: str) -> Sequence[FileCandidate]:
        """Restituisce candidati ordinati; errori di scansione non sono esclusioni."""
        ...


class DocumentReaderPort(Protocol):
    def read(self, candidate: FileCandidate) -> ReaderResult:
        """Estrae senza assegnare ID o costruire posting."""
        ...


class SnapshotRepositoryPort(Protocol):
    def load_active(self) -> IndexSnapshot | None: ...

    def acquire(self, snapshot_id: str | None = None) -> AbstractContextManager[IndexSnapshot]:
        """Protegge la versione richiesta (o attiva) fino al rilascio."""
        ...

    def save_candidate(self, snapshot: IndexSnapshot) -> None:
        """Avvia lo staging; nessun commit intermedio fino ad activate."""
        ...

    def validate_candidate(self, snapshot_id: str) -> None: ...

    def activate(self, snapshot_id: str) -> None:
        """Commit atomico del candidato validato; pubblicazione RAM dopo commit."""
        ...

    def discard_candidate(self, snapshot_id: str) -> None: ...


class SyncOutcome(StrEnum):
    UPDATED = "updated"
    NO_CHANGES = "no_changes"
    FAILED = "failed"


@dataclass(frozen=True)
class LastCheck:
    checked_at: datetime
    outcome: SyncOutcome
    diagnostic: str | None = None


@dataclass(frozen=True)
class Settings:
    active_directory: str | None = None
    last_check: LastCheck | None = None


class SettingsRepositoryPort(Protocol):
    def load(self) -> Settings: ...

    def save(self, settings: Settings) -> None: ...

    def clear(self) -> None: ...


class DirectoryResolverPort(Protocol):
    def __call__(self, directory: str) -> str:
        """Valida e restituisce la radice assoluta senza attraversare link."""
        ...


class LifecycleSnapshotRepositoryPort(SnapshotRepositoryPort, Protocol):
    incompatible: bool

    def select_directory(self, root: str) -> None:
        """Invalida le nuove acquisizioni della precedente directory."""
        ...

    def clear(self) -> None:
        """Blocca nuove letture, attende le esistenti e pulisce i dati posseduti."""
        ...

    def close(self) -> None: ...
