"""Repository volatile M3, con staging separato dal riferimento attivo."""
from local_document_search.application.errors import StorageFailure
from local_document_search.domain.snapshots import IndexSnapshot


class InMemorySnapshotRepository:
    def __init__(self) -> None:
        self._active: IndexSnapshot | None = None
        self._candidate: IndexSnapshot | None = None
        self._validated = False

    def load_active(self) -> IndexSnapshot | None:
        return self._active

    def save_candidate(self, snapshot: IndexSnapshot) -> None:
        if self._candidate is not None:
            raise StorageFailure("Un candidato è già in costruzione")
        if self._active is not None and snapshot.snapshot_id == self._active.snapshot_id:
            raise StorageFailure("Identificativo snapshot già attivo")
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
        self._active = candidate
        self._candidate = None
        self._validated = False

    def discard_candidate(self, snapshot_id: str) -> None:
        if self._candidate is not None and self._candidate.snapshot_id == snapshot_id:
            self._candidate = None
            self._validated = False
