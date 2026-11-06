"""Contratti M5, recovery su disco e fault injection con soli dati sintetici."""
from dataclasses import replace
from datetime import datetime, timezone
import sqlite3
import subprocess
import sys

import pytest

from local_document_search.application.contracts import SearchRequest
from local_document_search.application.errors import ResourceFailure, SnapshotUnavailable, StorageFailure
from local_document_search.application.search import GetDocument, SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.domain.documents import (
    CanonicalDocument, DocumentFormat, DocumentId, DocumentMetadata, FileFingerprint, RelativePath,
)
from local_document_search.domain.snapshots import IndexBuilder, SnapshotDraft
from local_document_search.domain.queries import SearchField
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository, storage_directory


def snapshot(root, key="one"):
    draft = SnapshotDraft()
    builder = IndexBuilder(draft)
    for i, (name, content, fmt) in enumerate([
        ("caffè.txt", "roma roma tre\r\n東京", DocumentFormat.TXT),
        ("sub/Café.md", "deep learning", DocumentFormat.MARKDOWN),
        ("machine.pdf", "deep learning", DocumentFormat.PDF),
        ("empty.txt", "", DocumentFormat.TXT),
    ]):
        metadata = DocumentMetadata(RelativePath(name), name.split("/")[-1], fmt, FileFingerprint(i, -123))
        builder.add(DocumentId(i), CanonicalDocument(metadata, content))
    builder.exclude(DocumentMetadata(RelativePath("image.pdf"), "image.pdf", DocumentFormat.PDF,
                                     FileFingerprint(100, 1234567890123456789)), "no text")
    return draft.freeze(snapshot_id=key, root_directory=str(root), created_at=datetime.now(timezone.utc),
                        schema_version="1", processing_version="1")


def publish(repo, value):
    repo.save_candidate(value)
    repo.validate_candidate(value.snapshot_id)
    repo.activate(value.snapshot_id)


@pytest.fixture(params=["memory", "sqlite"])
def repo(request, tmp_path):
    value = InMemorySnapshotRepository() if request.param == "memory" else SqliteSnapshotRepository(tmp_path / "storage")
    yield value
    if hasattr(value, "close"):
        value.close()


def test_contract_staging_rollback_and_retention(repo, tmp_path):
    first = snapshot(tmp_path / "source")
    repo.save_candidate(first)
    assert repo.load_active() is None
    with pytest.raises(SnapshotUnavailable):
        with repo.acquire(first.snapshot_id):
            pass
    with pytest.raises(StorageFailure):
        repo.activate(first.snapshot_id)
    with pytest.raises(StorageFailure):
        repo.save_candidate(first)
    with pytest.raises(StorageFailure):
        repo.validate_candidate("missing")
    repo.discard_candidate(first.snapshot_id)
    repo.discard_candidate(first.snapshot_id)
    publish(repo, first)
    with repo.acquire() as held:
        publish(repo, replace(first, snapshot_id="two"))
        publish(repo, replace(first, snapshot_id="three"))
        with repo.acquire("one") as old:
            assert old == held == first
        assert GetDocument(repo).execute(DocumentId(0), "one").extracted_text == "roma roma tre\r\n東京"
    with pytest.raises(SnapshotUnavailable):
        GetDocument(repo).execute(DocumentId(0), "one")
    with repo.acquire("two") as previous:
        assert previous.snapshot_id == "two"
    with pytest.raises(SnapshotUnavailable):
        GetDocument(repo).execute(DocumentId(999), "three")


def test_read_release_on_exception(repo, tmp_path):
    first = snapshot(tmp_path / "source")
    publish(repo, first)
    with pytest.raises(RuntimeError):
        with repo.acquire():
            publish(repo, replace(first, snapshot_id="two"))
            publish(repo, replace(first, snapshot_id="three"))
            raise RuntimeError
    with pytest.raises(SnapshotUnavailable):
        with repo.acquire("one"):
            pass


def test_roundtrip_search_without_sources(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    value = snapshot(source)
    queries = ["roma", '"roma roma"', 'roma "roma tre"', "machine deep", '"deep learning"', "empty"]
    requests = [SearchRequest(q, field) for q in queries for field in SearchField]
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        publish(repo, value)
        expected = [SearchDocuments(repo).execute(request) for request in requests]
    source.rmdir()
    from local_document_search.domain.analysis import ContentAnalyzer, FilenameAnalyzer
    def fail(*args):
        raise AssertionError("LoadActive non deve analizzare")
    with monkeypatch.context() as patch:
        patch.setattr(ContentAnalyzer, "analyze", fail)
        patch.setattr(FilenameAnalyzer, "analyze", fail)
        repo = SqliteSnapshotRepository(tmp_path / "storage")
        assert repo.load_active() == value
    with repo:
        assert [SearchDocuments(repo).execute(request) for request in requests] == expected
        assert GetDocument(repo).execute(DocumentId(0), "one").extracted_text == value.catalog.documents[DocumentId(0)].extracted_text
        assert repo._db.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert repo._db.execute("PRAGMA journal_mode").fetchone() == ("delete",)
        assert repo._db.execute("PRAGMA synchronous").fetchone() == (2,)


@pytest.mark.parametrize("stage", ["save", "validate", "commit", "full", "memory"])
def test_failure_preserves_active_and_retry(tmp_path, monkeypatch, stage):
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        first = snapshot(tmp_path / "source")
        publish(repo, first)
        candidate = replace(first, snapshot_id="two")
        with monkeypatch.context() as patch:
            if stage == "save":
                repo._db.execute("CREATE TRIGGER fail BEFORE INSERT ON documents BEGIN SELECT RAISE(ABORT, 'failure'); END")
            if stage in ("commit", "full", "memory"):
                def fail():
                    if stage == "memory":
                        raise MemoryError
                    error = sqlite3.OperationalError("synthetic failure")
                    error.sqlite_errorcode = sqlite3.SQLITE_FULL if stage == "full" else sqlite3.SQLITE_IOERR
                    raise error
                patch.setattr(repo, "_commit", fail)
            with pytest.raises(ResourceFailure if stage in ("full", "memory") else StorageFailure):
                repo.save_candidate(candidate)
                if stage == "validate":
                    repo._db.execute("DELETE FROM positions WHERE snapshot='two'")
                repo.validate_candidate("two")
                repo.activate("two")
            repo.discard_candidate("two")
        assert repo.load_active() == first
        if stage == "save":
            repo._db.execute("DROP TRIGGER fail")
        publish(repo, candidate)
    with SqliteSnapshotRepository(tmp_path / "storage") as reopened:
        assert reopened.load_active() == candidate


def test_retention_failure_is_diagnostic_and_retried_at_restart(tmp_path, monkeypatch):
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        first = snapshot(tmp_path / "source")
        publish(repo, first)
        with monkeypatch.context() as patch:
            def fail():
                raise sqlite3.OperationalError("synthetic cleanup failure")
            patch.setattr(repo, "_prune", fail)
            publish(repo, replace(first, snapshot_id="two"))
            publish(repo, replace(first, snapshot_id="three"))
            assert repo.load_active().snapshot_id == "three"
            assert repo.cleanup_diagnostic
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        assert repo.cleanup_diagnostic is None
        assert {row[0] for row in repo._db.execute("SELECT id FROM snapshots")} == {"two", "three"}


def test_clear_owns_only_rows_and_protects_readers(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    original = source / "keep.txt"
    original.write_text("preserved")
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        extra = repo.directory / "unrelated.txt"
        extra.write_text("preserved")
        publish(repo, snapshot(source))
        with repo.acquire():
            with pytest.raises(StorageFailure):
                repo.clear()
            with pytest.raises(StorageFailure):
                repo.close()
        repo.save_candidate(snapshot(source, "two"))
        with pytest.raises(StorageFailure):
            repo.clear()
        repo.discard_candidate("two")
        repo.clear()
        repo.clear()
        assert repo.load_active() is None
        assert extra.read_text() == original.read_text() == "preserved"
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        assert repo.load_active() is None


@pytest.mark.parametrize("kind", ["physical", "processing", "corruption", "missing_active"])
def test_incompatible_or_corrupt_storage_preserved(tmp_path, kind):
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        publish(repo, snapshot(tmp_path / "source"))
        if kind == "physical":
            repo._db.execute("PRAGMA user_version=99")
        elif kind == "processing":
            repo._db.execute("UPDATE snapshots SET processing_version='99'")
        elif kind == "missing_active":
            repo._db.execute("DELETE FROM active")
        else:
            repo._db.execute("DELETE FROM positions")
    path = tmp_path / "storage" / "snapshots.sqlite3"
    before = path.read_bytes()
    with pytest.raises(StorageFailure if kind in ("corruption", "missing_active") else SnapshotUnavailable):
        SqliteSnapshotRepository(path.parent)
    assert path.read_bytes() == before


def test_storage_boundaries(tmp_path):
    with pytest.raises(StorageFailure):
        storage_directory(tmp_path / "repo" / "data", repository_directory=tmp_path / "repo")
    with pytest.raises(StorageFailure):
        storage_directory(tmp_path / "source" / "data", source_directory=tmp_path / "source")
    with SqliteSnapshotRepository(tmp_path / "source" / "data") as repo:
        with pytest.raises(StorageFailure):
            publish(repo, snapshot(tmp_path / "source"))


@pytest.mark.parametrize("stage", ["before", "during", "after"])
def test_process_crash_and_recovery(tmp_path, stage):
    storage = tmp_path / "storage"
    with SqliteSnapshotRepository(storage) as repo:
        first = snapshot(tmp_path / "source")
        publish(repo, first)
    script = r"""
import os, sys
from dataclasses import replace
from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository
repo = SqliteSnapshotRepository(sys.argv[1])
candidate = replace(repo.load_active(), snapshot_id="two")
repo.save_candidate(candidate)
repo.validate_candidate("two")
if sys.argv[2] == "before":
    os._exit(73)
if sys.argv[2] == "during":
    # Il trace callback interrompe l'esecuzione dell'istruzione COMMIT nel processo.
    repo._db.set_trace_callback(lambda sql: os._exit(73) if sql == "COMMIT" else None)
else:
    original = repo._commit
    def stop_after_commit():
        original()
        os._exit(73)
    repo._commit = stop_after_commit
repo.activate("two")
"""
    result = subprocess.run([sys.executable, "-c", script, str(storage), stage], timeout=30)
    assert result.returncode == 73
    with SqliteSnapshotRepository(storage) as repo:
        active = repo.load_active()
        assert active == (replace(first, snapshot_id="two") if stage == "after" else first)
        assert repo._db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert repo._db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert SearchDocuments(repo).execute(SearchRequest('"roma roma"')).total_matches == 1


def test_real_sqlite_full_is_resource_failure_in_build(tmp_path):
    from local_document_search.infrastructure.filesystem import TextFileDiscovery
    from local_document_search.infrastructure.readers.text import TextReader
    source = tmp_path / "source"
    source.mkdir()
    (source / "first.txt").write_text("roma tre", encoding="utf-8")
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        build = BuildIndex(TextFileDiscovery(), TextReader(), repo)
        first = build.execute(str(source))
        pages = repo._db.execute("PRAGMA page_count").fetchone()[0]
        repo._db.execute(f"PRAGMA max_page_count={pages}")
        (source / "large.txt").write_text("large " * 10000, encoding="utf-8")
        with pytest.raises(ResourceFailure):
            build.execute(str(source))
        assert repo.load_active().snapshot_id == first.snapshot_id
        assert SearchDocuments(repo).execute(SearchRequest("large")).total_matches == 0
        repo._db.execute("PRAGMA max_page_count=100000")
        assert build.execute(str(source)).indexed == 2


def test_empty_snapshot_roundtrip(tmp_path):
    value = SnapshotDraft().freeze(snapshot_id="empty", root_directory=str(tmp_path / "source"),
        created_at=datetime.now(timezone.utc), schema_version="1", processing_version="1")
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        publish(repo, value)
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        assert repo.load_active() == value
        assert SearchDocuments(repo).execute(SearchRequest("anything")).total_matches == 0


def test_directory_retention_only_existing_reads_survive(repo, tmp_path):
    first = snapshot(tmp_path / "source")
    publish(repo, first)
    with repo.acquire() as held:
        publish(repo, replace(first, snapshot_id="other", root_directory=str(tmp_path / "other")))
        assert held == first
        with pytest.raises(SnapshotUnavailable):
            with repo.acquire("one"):
                pass
    with pytest.raises(SnapshotUnavailable):
        with repo.acquire("one"):
            pass


def test_duplicate_retained_id_rejected(repo, tmp_path):
    first = snapshot(tmp_path / "source")
    publish(repo, first)
    publish(repo, replace(first, snapshot_id="two"))
    with pytest.raises(StorageFailure):
        repo.save_candidate(first)
    assert repo.load_active().snapshot_id == "two"


@pytest.mark.parametrize("delay", [0, 0.005])
def test_external_termination_racing_commit(tmp_path, delay):
    import time
    from concurrent.futures import ThreadPoolExecutor
    storage = tmp_path / "storage"
    first = snapshot(tmp_path / "source")
    with SqliteSnapshotRepository(storage) as repo:
        publish(repo, first)
    script = r"""
import sys, time
from dataclasses import replace
from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository
repo = SqliteSnapshotRepository(sys.argv[1])
repo.save_candidate(replace(repo.load_active(), snapshot_id="two"))
repo.validate_candidate("two")
original = repo._commit
def commit():
    print("committing", flush=True)
    original()
repo._commit = commit
repo.activate("two")
time.sleep(30)
"""
    process = subprocess.Popen([sys.executable, "-c", script, str(storage)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        with ThreadPoolExecutor(max_workers=1) as reader:
            ready = reader.submit(process.stdout.readline)
            try:
                assert ready.result(timeout=10).strip() == "committing"
            except BaseException:
                process.kill()
                raise
        time.sleep(delay)
        process.kill()
        process.communicate(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
    with SqliteSnapshotRepository(storage) as repo:
        active = repo.load_active()
        assert active.snapshot_id in ("one", "two")
        assert active == replace(first, snapshot_id=active.snapshot_id)
        assert repo._db.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_candidate_and_reference_visible_only_after_commit(tmp_path):
    with SqliteSnapshotRepository(tmp_path / "storage") as repo:
        first = snapshot(tmp_path / "source")
        publish(repo, first)
        candidate = replace(first, snapshot_id="two")
        repo.save_candidate(candidate)
        repo.validate_candidate("two")
        observer = sqlite3.connect(repo.directory / "snapshots.sqlite3")
        try:
            assert observer.execute("SELECT id FROM snapshots").fetchall() == [("one",)]
            assert observer.execute("SELECT current FROM active").fetchone() == ("one",)
            assert repo.load_active() == first
            repo.activate("two")
            assert observer.execute("SELECT current FROM active").fetchone() == ("two",)
        finally:
            observer.close()


def test_incompatible_candidate_rejected(repo, tmp_path):
    value = snapshot(tmp_path / "source")
    publish(repo, value)
    with pytest.raises(SnapshotUnavailable):
        repo.save_candidate(replace(value, snapshot_id="two", processing_version="99"))
    assert repo.load_active() == value


def test_default_storage_is_per_user(tmp_path, monkeypatch):
    import os
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    if os.name == "nt":
        assert storage_directory() == tmp_path / "LocalDocumentSearch"
        monkeypatch.delenv("LOCALAPPDATA")
    with pytest.raises(StorageFailure):
        storage_directory()


def test_empty_requested_id_never_falls_back_to_active(repo, tmp_path):
    publish(repo, snapshot(tmp_path / "source"))
    with pytest.raises(SnapshotUnavailable):
        GetDocument(repo).execute(DocumentId(0), "")
