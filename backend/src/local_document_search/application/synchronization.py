"""Build completo M3 e sincronizzazione incrementale bloccante M6."""
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from .contracts import BuildResult, SyncResult
from .errors import ExtractionFailure, ResourceFailure, StorageFailure
from .ports import DocumentReaderPort, Extracted, Excluded, FileDiscoveryPort, SnapshotRepositoryPort
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft


class IndexSynchronizer:
    """Diff bloccante: gli invariati non attraversano reader o analyzer."""

    def __init__(self, discovery, reader, snapshots):
        self.discovery, self.reader, self.snapshots = discovery, reader, snapshots

    def execute(self, root_directory: str) -> SyncResult:
        started = perf_counter()
        key = uuid4().hex
        try:
            old = self.snapshots.load_active()
            if old is not None and old.root_directory != root_directory:
                old = None
            candidates = self.discovery.discover(root_directory)
            before = old.manifest.entries if old else {}
            after = {c.metadata.relative_path: c for c in candidates}
            added = after.keys() - before.keys()
            removed = before.keys() - after.keys()
            modified = {p for p in after.keys() & before.keys()
                        if after[p].metadata.fingerprint != before[p].metadata.fingerprint}
            unchanged = (after.keys() & before.keys()) - modified
            if old is not None and not (added or removed or modified):
                return SyncResult(old.snapshot_id, False, 0, 0, 0, len(unchanged),
                                  sum(e.document_id is None for e in before.values()),
                                  0, perf_counter() - started, 0)
            draft = SnapshotDraft()
            if old:
                draft.entries.update(before)
                draft.documents.update(old.catalog.documents)
                draft.filename_terms.update({t: dict(p) for t, p in old.filename_index.terms.items()})
                draft.content_terms.update({t: dict(p) for t, p in old.content_index.terms.items()})
            next_id = max((i.value for i in draft.documents), default=-1) + 1
            builder = IndexBuilder(draft)
            for path in removed:
                builder.remove(path)
            processed = 0
            for path in sorted(added | modified, key=lambda p: p.value):
                candidate = after[path]
                try:
                    result = self.reader.read(candidate)
                except MemoryError:
                    raise
                except Exception as exc:
                    raise ExtractionFailure(f"{path.value}: estrazione fallita") from exc
                if isinstance(result, Extracted):
                    identity = before[path].document_id if path in before else None
                    if identity is None:
                        identity = DocumentId(next_id)
                        next_id += 1
                    builder.remove(path)
                    builder.add(identity, result.document)
                elif isinstance(result, Excluded):
                    builder.exclude(candidate.metadata, result.reason)
                else:
                    raise ExtractionFailure(result.reason)
                processed += candidate.metadata.fingerprint.size_bytes
            snapshot = draft.freeze(snapshot_id=key, root_directory=root_directory,
                                    created_at=datetime.now(timezone.utc),
                                    schema_version="1", processing_version="1")
            try:
                self.snapshots.save_candidate(snapshot)
                self.snapshots.validate_candidate(key)
                self.snapshots.activate(key)
            except (MemoryError, ResourceFailure):
                raise
            except Exception as exc:
                raise StorageFailure("Pubblicazione dello snapshot fallita") from exc
            return SyncResult(key, True, len(added), len(modified), len(removed), len(unchanged),
                              sum(e.document_id is None for e in draft.entries.values()),
                              0, perf_counter() - started, processed)
        except BaseException as exc:
            try:
                self.snapshots.discard_candidate(key)
            except Exception as cleanup:
                exc.add_note(f"Scarto candidato fallito: {cleanup}")
            if isinstance(exc, MemoryError):
                raise ResourceFailure("Memoria insufficiente durante sync") from exc
            raise


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
            except (MemoryError, ResourceFailure):
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
