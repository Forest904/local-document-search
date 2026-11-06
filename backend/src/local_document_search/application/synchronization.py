"""Build completo M3 e sincronizzazione incrementale bloccante M6."""
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from .contracts import BuildResult, SyncResult, JobPhase, JobReport, JobDiagnostic
from .errors import ExtractionFailure, ResourceFailure, StorageFailure
from .ports import DocumentReaderPort, Extracted, Excluded, FileDiscoveryPort, SnapshotRepositoryPort
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft


def _safe_exclusion(reason):
    return "PDF senza testo estraibile" if reason.startswith("PDF senza testo") else "Esclusione intenzionale"


class IndexSynchronizer:
    """Diff bloccante: gli invariati non attraversano reader o analyzer."""

    def __init__(self, discovery, reader, snapshots):
        self.discovery, self.reader, self.snapshots = discovery, reader, snapshots

    def execute(self, root_directory: str, progress=None) -> SyncResult:
        notify = progress if progress is not None else lambda **changes: None
        started = perf_counter()
        key = uuid4().hex
        try:
            old = self.snapshots.load_active()
            if old is not None and old.root_directory != root_directory:
                old = None
            notify(phase=JobPhase.SCANNING)
            candidates = self.discovery.discover(root_directory)
            before = old.manifest.entries if old else {}
            after = {c.metadata.relative_path: c for c in candidates}
            added = after.keys() - before.keys()
            removed = before.keys() - after.keys()
            modified = {p for p in after.keys() & before.keys()
                        if after[p].metadata.fingerprint != before[p].metadata.fingerprint}
            unchanged = (after.keys() & before.keys()) - modified
            work = added | modified
            notify(phase=JobPhase.BUILDING, files_total=len(work),
                   bytes_total=sum(after[p].metadata.fingerprint.size_bytes for p in work))
            if old is not None and not (added or removed or modified):
                report = JobReport(tuple(JobDiagnostic("excluded", JobPhase.BUILDING,
                                   p.value, _safe_exclusion(e.reason or ""))
                                   for p, e in before.items() if e.document_id is None),
                                   published_snapshot_id=old.snapshot_id,
                                   unchanged=len(unchanged),
                                   excluded=sum(e.document_id is None for e in before.values()))
                notify(report=report)
                return SyncResult(old.snapshot_id, False, 0, 0, 0, len(unchanged),
                                  sum(e.document_id is None for e in before.values()),
                                  0, perf_counter() - started, 0, report)
            draft = SnapshotDraft()
            if old:
                draft.entries.update(before)
                draft.documents.update(old.catalog.documents)
                draft.filename_terms.update({t: dict(p) for t, p in old.filename_index.terms.items()})
                draft.content_terms.update({t: dict(p) for t, p in old.content_index.terms.items()})
            new_id_paths = {p for p in work if p not in before or before[p].document_id is None}
            next_id = self.snapshots.reserve_document_ids(len(new_id_paths))
            builder = IndexBuilder(draft)
            observed_exclusions = []
            for path in removed:
                builder.remove(path)
            processed = 0
            for completed, path in enumerate(sorted(work, key=lambda p: p.value), start=1):
                candidate = after[path]
                notify(phase=JobPhase.EXTRACTING, current_file=path.value)
                try:
                    result = self.reader.read(candidate)
                except MemoryError:
                    raise
                except Exception as exc:
                    notify(report=JobReport(tuple(observed_exclusions) + (
                           JobDiagnostic("reader", JobPhase.EXTRACTING,
                           path.value, "Lettura o estrazione fallita"),), complete=False,
                           excluded=len(observed_exclusions)))
                    raise ExtractionFailure(f"{path.value}: estrazione fallita") from exc
                notify(phase=JobPhase.ANALYZING)
                if isinstance(result, Extracted):
                    identity = before[path].document_id if path in before else None
                    if identity is None:
                        identity = DocumentId(next_id)
                        next_id += 1
                    builder.remove(path)
                    builder.add(identity, result.document)
                elif isinstance(result, Excluded):
                    builder.exclude(candidate.metadata, result.reason)
                    observed_exclusions.append(JobDiagnostic("excluded", JobPhase.EXTRACTING,
                                               path.value, _safe_exclusion(result.reason)))
                else:
                    reason = "File non decodificabile" if "utf-8" in result.reason.lower() or "decode" in result.reason.lower() else (
                        "PDF protetto o illeggibile" if candidate.metadata.format.value == "pdf" else "Lettura o estrazione fallita")
                    notify(report=JobReport(tuple(observed_exclusions) + (
                           JobDiagnostic("reader", JobPhase.EXTRACTING,
                           path.value, reason),), complete=False,
                           excluded=len(observed_exclusions)))
                    raise ExtractionFailure(f"{path.value}: {reason}")
                processed += candidate.metadata.fingerprint.size_bytes
                notify(files_completed=completed, bytes_completed=processed)
            notify(phase=JobPhase.BUILDING, current_file=None)
            snapshot = draft.freeze(snapshot_id=key, root_directory=root_directory,
                                    created_at=datetime.now(timezone.utc),
                                    schema_version="1", processing_version="1")
            try:
                notify(phase=JobPhase.COMMITTING)
                report = JobReport(tuple(JobDiagnostic("excluded", JobPhase.BUILDING,
                                   p.value, _safe_exclusion(e.reason or ""))
                                   for p, e in draft.entries.items() if e.document_id is None),
                                   published_snapshot_id=key, added=len(added), modified=len(modified),
                                   removed=len(removed), unchanged=len(unchanged),
                                   excluded=sum(e.document_id is None for e in draft.entries.values()))
                self.snapshots.save_candidate(snapshot)
                self.snapshots.validate_candidate(key)
                self.snapshots.activate(key)
            except (MemoryError, ResourceFailure):
                raise
            except Exception as exc:
                notify(report=JobReport(tuple(observed_exclusions) + (
                       JobDiagnostic("storage", JobPhase.COMMITTING, None,
                       "Pubblicazione dello snapshot fallita"),), complete=False,
                       excluded=len(observed_exclusions)))
                raise StorageFailure("Pubblicazione dello snapshot fallita") from exc
            notify(report=report)
            return SyncResult(key, True, len(added), len(modified), len(removed), len(unchanged),
                              sum(e.document_id is None for e in draft.entries.values()),
                              0, perf_counter() - started, processed, report)
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

    def execute(self, root_directory: str) -> BuildResult:
        started = perf_counter()
        snapshot_id = uuid4().hex
        try:
            candidates = self.discovery.discover(root_directory)
            draft = SnapshotDraft()
            builder = IndexBuilder(draft)
            indexed = excluded = processed_bytes = 0
            exclusions = []
            next_id = self.snapshots.reserve_document_ids(len(candidates))
            for candidate in candidates:
                try:
                    result = self.reader.read(candidate)
                except MemoryError:
                    raise
                except Exception as exc:
                    raise ExtractionFailure(
                        f"{candidate.metadata.relative_path.value}: lettura o estrazione fallita"
                    ) from exc
                if isinstance(result, Extracted):
                    builder.add(DocumentId(next_id), result.document)
                    next_id += 1
                    indexed += 1
                elif isinstance(result, Excluded):
                    builder.exclude(candidate.metadata, result.reason)
                    excluded += 1
                    exclusions.append(JobDiagnostic("excluded", JobPhase.EXTRACTING,
                                      candidate.metadata.relative_path.value,
                                      _safe_exclusion(result.reason)))
                else:
                    raise ExtractionFailure(
                        f"{candidate.metadata.relative_path.value}: lettura o estrazione fallita")
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
                               processed_bytes, perf_counter() - started,
                               JobReport(tuple(exclusions), published_snapshot_id=snapshot_id,
                                         excluded=excluded))
        except BaseException as exc:
            # Anche l'interruzione da tastiera scarta lo staging.
            try:
                self.snapshots.discard_candidate(snapshot_id)
            except Exception as cleanup_error:
                exc.add_note(f"Scarto candidato fallito: {cleanup_error}")
            if isinstance(exc, MemoryError):
                raise ResourceFailure("Memoria insufficiente durante l'indicizzazione") from exc
            raise
