"""Repository volatile con staging e retention delle letture M5."""
from contextlib import contextmanager

from local_document_search.application.errors import StorageFailure, SnapshotUnavailable
from local_document_search.domain.snapshots import IndexSnapshot


class InMemorySnapshotRepository:
    def __init__(self) -> None:
        self._active: IndexSnapshot | None = None
        self._candidate: IndexSnapshot | None = None
        self._validated = False
        self._versions = {}
        self._readers = {}
        self._previous = None
        self.cleanup_diagnostic = None

    def load_active(self) -> IndexSnapshot | None:
        return self._active

    def save_candidate(self, snapshot: IndexSnapshot) -> None:
        if self._candidate is not None:
            raise StorageFailure("Un candidato è già in costruzione")
        if snapshot.snapshot_id in self._versions:
            raise StorageFailure("Identificativo snapshot già presente")
        if (snapshot.schema_version, snapshot.processing_version) != ("1", "1"):
            raise SnapshotUnavailable("Versione snapshot incompatibile")
        self._candidate = snapshot
        self._validated = False

    def _require_candidate(self, snapshot_id: str) -> IndexSnapshot:
        if self._candidate is None or self._candidate.snapshot_id != snapshot_id:
            raise StorageFailure("Candidato non disponibile")
        return self._candidate

    def validate_candidate(self, snapshot_id: str) -> None:
        candidate = self._require_candidate(snapshot_id)
        try:
            candidate.__post_init__()
        except ValueError as exc:
            raise StorageFailure(str(exc)) from exc
        self._validated = True

    def activate(self, snapshot_id: str) -> None:
        candidate = self._require_candidate(snapshot_id)
        if not self._validated:
            raise StorageFailure("Candidato non validato")
        self._previous = (self._active.snapshot_id if self._active is not None
                          and self._active.root_directory == candidate.root_directory else None)
        self._versions[candidate.snapshot_id] = candidate
        self._active = candidate
        self._candidate = None
        self._validated = False
        self._cleanup()

    def discard_candidate(self, snapshot_id: str) -> None:
        if self._candidate is not None and self._candidate.snapshot_id == snapshot_id:
            self._candidate = None
            self._validated = False

    def _prune(self):
        keep = {self._active.snapshot_id if self._active else None, self._previous}
        self._versions = {key: value for key, value in self._versions.items()
                          if key in keep or self._readers.get(key, 0)}

    @contextmanager
    def acquire(self, snapshot_id=None):
        key = snapshot_id if snapshot_id is not None else (self._active.snapshot_id if self._active else None)
        snapshot = self._versions.get(key)
        if snapshot is None or self._active is None or snapshot.root_directory != self._active.root_directory:
            raise SnapshotUnavailable("Snapshot non disponibile")
        self._readers[key] = self._readers.get(key, 0) + 1
        try:
            yield snapshot
        finally:
            self._readers[key] -= 1
            if not self._readers[key]:
                del self._readers[key]
            self._cleanup()

    def _cleanup(self):
        try:
            self._prune()
            self.cleanup_diagnostic = None
        except MemoryError:
            self.cleanup_diagnostic = "Pulizia snapshot da riprovare"
