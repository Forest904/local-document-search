"""Build completo bloccante M3; diff e lifecycle restano in M6."""
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from .contracts import BuildResult
from .errors import ExtractionFailure, ResourceFailure, StorageFailure
from .ports import DocumentReaderPort, Extracted, Excluded, FileDiscoveryPort, SnapshotRepositoryPort
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft


class BuildIndex:
    """Un writer sincrono per sessione, con radice assoluta validata dall'adapter."""

    def __init__(self, discovery: FileDiscoveryPort, reader: DocumentReaderPort,
                 snapshots: SnapshotRepositoryPort) -> None:
        self.discovery = discovery
        self.reader = reader
        self.snapshots = snapshots
        self._next_id = 0

    def execute(self, root_directory: str) -> BuildResult:
        started = perf_counter()
        snapshot_id = uuid4().hex
        try:
            candidates = self.discovery.discover(root_directory)
            draft = SnapshotDraft()
            builder = IndexBuilder(draft)
            indexed = excluded = processed_bytes = 0
            for candidate in candidates:
                try:
                    result = self.reader.read(candidate)
                except MemoryError:
                    raise
                except Exception as exc:
                    raise ExtractionFailure(
                        f"{candidate.metadata.relative_path.value}: {exc}"
                    ) from exc
                if isinstance(result, Extracted):
                    builder.add(DocumentId(self._next_id), result.document)
                    self._next_id += 1
                    indexed += 1
                elif isinstance(result, Excluded):
                    builder.exclude(candidate.metadata, result.reason)
                    excluded += 1
                else:
                    raise ExtractionFailure(result.reason)
                processed_bytes += candidate.metadata.fingerprint.size_bytes
            snapshot = draft.freeze(
                snapshot_id=snapshot_id, root_directory=root_directory,
                created_at=datetime.now(timezone.utc), schema_version="1", processing_version="1",
            )
            try:
                self.snapshots.save_candidate(snapshot)
                self.snapshots.validate_candidate(snapshot_id)
                self.snapshots.activate(snapshot_id)
            except MemoryError:
                raise
            except Exception as exc:
                raise StorageFailure(f"Pubblicazione fallita: {exc}") from exc
            return BuildResult(snapshot_id, len(candidates), indexed, excluded,
                               processed_bytes, perf_counter() - started)
        except BaseException as exc:
            # Anche l'interruzione da tastiera scarta lo staging.
            try:
                self.snapshots.discard_candidate(snapshot_id)
            except Exception as cleanup_error:
                exc.add_note(f"Scarto candidato fallito: {cleanup_error}")
            if isinstance(exc, MemoryError):
                raise ResourceFailure("Memoria insufficiente durante l'indicizzazione") from exc
            raise
