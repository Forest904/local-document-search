"""Contratti persistenti v2 su un corpus sintetico minimo."""
import sqlite3
import subprocess
import sys
from threading import Event

import pytest
from pypdf import PdfWriter

from local_document_search.application.contracts import (
    CancelOutcome, CancelledResult, JobState, SearchRequest, SuggestRequest,
)
from local_document_search.application.errors import StorageFailure
from local_document_search.interfaces.composition import compose_v2_application as _compose_v2_application


def compose_v2_application(storage):
    return _compose_v2_application(storage, read_workers=1)


def test_v2_reopen_sync_and_versioned_results(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    file = source / "note.txt"
    file.write_text("alfa beta", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(app.job_status.manager.current().job_id)
        first = app.search.execute(SearchRequest("alfa"))
        assert first.total_matches == 1
        file.write_text("gamma beta", encoding="utf-8")
        app.synchronize.execute()
        assert app.search.execute(SearchRequest("gamma")).total_matches == 1
        with app.snapshots.acquire(first.snapshot_id) as previous:
            assert previous.snapshot_id == first.snapshot_id
    with compose_v2_application(storage) as app:
        state = app.initialize.execute()
        assert state.search_available
        assert app.search.execute(SearchRequest("gamma")).total_matches == 1
        assert app.search.execute(SearchRequest("gam*", allow_prefixes=True)).total_matches == 1
        assert app.suggest.execute(SuggestRequest("gam")).terms == ("gamma",)
        app._lifecycle.jobs.wait(state.job.job_id)


def test_v2_refuses_explicit_v1_storage_without_modification(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    marker = storage / "snapshots.sqlite3"
    marker.write_bytes(b"v1 storage")
    with pytest.raises(StorageFailure):
        compose_v2_application(storage)
    assert marker.read_bytes() == b"v1 storage"
    assert not (storage / "control-v2.sqlite3").exists()


def test_cancel_unknown_and_completed_job(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        from local_document_search.application.contracts import InvalidInput
        with pytest.raises(InvalidInput):
            app.cancel_synchronization.execute("missing")
        state = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(state.job.job_id)
        assert app.cancel_synchronization.execute(state.job.job_id) is CancelOutcome.FINISHED
        assert app.job_status.execute(state.job.job_id).state is JobState.COMPLETED


def test_cancel_during_reader_preserves_previous(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        previous = app.status.execute().active_snapshot_id
        (source / "second.txt").write_text("beta", encoding="utf-8")
        entered, release = Event(), Event()
        reader = app._lifecycle.synchronizer.reader
        original = reader.read

        def blocked(candidate):
            entered.set()
            assert release.wait(5)
            return original(candidate)

        monkeypatch.setattr(reader, "read", blocked)
        try:
            job = app.request_synchronization.execute()
            assert entered.wait(5)
            assert app.cancel_synchronization.execute(job.job_id) is CancelOutcome.ACCEPTED
        finally:
            release.set()
        result = app._lifecycle.jobs.wait(job.job_id)
        assert result == CancelledResult(job.job_id)
        assert app.job_status.execute(job.job_id).state is JobState.CANCELLED
        assert app.status.execute().active_snapshot_id == previous
        assert app.search.execute(SearchRequest("beta")).total_matches == 0


def test_recovery_requires_explicit_action(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        original = app.status.execute().active_snapshot_id
        note.write_text("beta", encoding="utf-8")
        app.synchronize.execute()
        name = app.snapshots.settings.selected()
    with sqlite3.connect(storage / name) as db:
        db.execute("UPDATE snapshots SET processing_version='broken' WHERE id=(SELECT current FROM active)")
    with compose_v2_application(storage) as app:
        assert not app.initialize.execute().search_available
        assert app.recover_previous.execute() == original
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1


def test_changed_metadata_fails_without_publication(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        original_id = app.status.execute().active_snapshot_id
        note.write_text("beta", encoding="utf-8")
        reader = app._lifecycle.synchronizer.reader
        read = reader.read

        def mutate(candidate):
            result = read(candidate)
            note.write_text("gamma delta", encoding="utf-8")
            return result

        monkeypatch.setattr(reader, "read", mutate)
        from local_document_search.application.errors import SourceUnavailable
        with pytest.raises(SourceUnavailable):
            app.synchronize.execute()
        assert app.status.execute().active_snapshot_id == original_id


def test_v2_reuses_unchanged_versions_and_rebuilds_explicitly(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    first_file = source / "first.txt"
    first_file.write_text("alfa", encoding="utf-8")
    second_file = source / "second.txt"
    second_file.write_text("beta", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        job = app.select_directory.execute(str(source)).job
        app._lifecycle.jobs.wait(job.job_id)
        first_snapshot = app.status.execute().active_snapshot_id
        second_file.write_text("gamma longer", encoding="utf-8")
        app.synchronize.execute()
        name = app.snapshots.settings.selected()
        rebuild = app.rebuild.execute()
        app._lifecycle.jobs.wait(rebuild.job_id)
        assert app.status.execute().active_snapshot_id != first_snapshot
    with sqlite3.connect(storage / name) as db:
        rows = db.execute("SELECT snapshot,path,version FROM manifest ORDER BY snapshot,path").fetchall()
        by_path = {}
        for _, path, version in rows:
            by_path.setdefault(path, set()).add(version)
        assert len(by_path["first.txt"]) == 1
        assert len(by_path["second.txt"]) == 1


def test_v2_physical_incompatibility_requires_rebuild(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("alfa", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        job = app.select_directory.execute(str(source)).job
        app._lifecycle.jobs.wait(job.job_id)
        name = app.snapshots.settings.selected()
    with sqlite3.connect(storage / name) as db:
        db.execute("PRAGMA user_version=99")
    with compose_v2_application(storage) as app:
        assert not app.initialize.execute().search_available
        assert app.snapshots.settings.selected() == name
        job = app.rebuild.execute()
        app._lifecycle.jobs.wait(job.job_id)
        assert app.status.execute().search_available
        assert app.snapshots.settings.selected() != name


def test_cancel_rejected_once_commit_begins(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        note.write_text("beta longer", encoding="utf-8")
        entered, release = Event(), Event()
        repo = app.snapshots._repo
        commit = repo._commit

        def blocked_commit():
            entered.set()
            assert release.wait(5)
            return commit()

        monkeypatch.setattr(repo, "_commit", blocked_commit)
        try:
            job = app.request_synchronization.execute()
            assert entered.wait(5)
            assert app.cancel_synchronization.execute(job.job_id) is CancelOutcome.COMMIT_STARTED
        finally:
            release.set()
        app._lifecycle.jobs.wait(job.job_id)
        assert app.job_status.execute(job.job_id).state is JobState.COMPLETED
        assert app.search.execute(SearchRequest("beta")).total_matches == 1


def test_rebuild_replaces_incompatible_active_snapshot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("alfa", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        old = app.status.execute().active_snapshot_id
        name = app.snapshots.settings.selected()
    with sqlite3.connect(storage / name) as db:
        db.execute("UPDATE snapshots SET schema_version='old' WHERE id=?", (old,))
    with compose_v2_application(storage) as app:
        assert not app.initialize.execute().search_available
        rebuild = app.rebuild.execute()
        app._lifecycle.jobs.wait(rebuild.job_id)
        assert app.status.execute().search_available
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1


def test_v2_failed_commit_does_not_publish_candidate(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        original = app.status.execute().active_snapshot_id
        note.write_text("beta longer", encoding="utf-8")
        repo = app.snapshots._repo

        def fail():
            raise sqlite3.OperationalError("synthetic commit failure")

        monkeypatch.setattr(repo, "_commit", fail)
        with pytest.raises(StorageFailure):
            app.synchronize.execute()
        assert app.status.execute().active_snapshot_id == original
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1
    with compose_v2_application(storage) as app:
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1
        assert app.search.execute(SearchRequest("beta")).total_matches == 0


def test_v2_acquired_version_survives_two_updates(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        old = app.status.execute().active_snapshot_id
        with app.snapshots.acquire(old) as acquired:
            for text in ("beta longer", "gamma even longer"):
                note.write_text(text, encoding="utf-8")
                app.synchronize.execute()
            assert acquired.snapshot_id == old
            assert acquired.catalog.documents
        from local_document_search.application.errors import SnapshotUnavailable
        with pytest.raises(SnapshotUnavailable):
            with app.snapshots.acquire(old):
                pass


def test_v2_parallel_ingestion_publishes_complete_snapshot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for number in range(6):
        (source / f"note-{number}.txt").write_text(f"marcatore{number}", encoding="utf-8")
    with _compose_v2_application(tmp_path / "storage", read_workers=2) as app:
        state = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(state.job.job_id)
        for number in range(6):
            assert app.search.execute(SearchRequest(f"marcatore{number}")).total_matches == 1


def test_cancel_after_staging_discards_candidate(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        original = app.status.execute().active_snapshot_id
        note.write_text("beta longer", encoding="utf-8")
        repo = app.snapshots._repo
        validate = repo.validate_candidate
        entered, release = Event(), Event()

        def blocked(key):
            entered.set()
            assert release.wait(5)
            return validate(key)

        monkeypatch.setattr(repo, "validate_candidate", blocked)
        try:
            job = app.request_synchronization.execute()
            assert entered.wait(5)
            assert app.cancel_synchronization.execute(job.job_id) is CancelOutcome.ACCEPTED
        finally:
            release.set()
        assert app._lifecycle.jobs.wait(job.job_id) == CancelledResult(job.job_id)
        assert app.status.execute().active_snapshot_id == original
        assert app.search.execute(SearchRequest("beta")).total_matches == 0


def test_v2_staging_digest_rejects_changed_blob(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        previous = app.status.execute().active_snapshot_id
        note.write_text("beta longer", encoding="utf-8")
        repo = app.snapshots._repo
        validate = repo.validate_candidate

        def corrupt(key):
            repo._db.execute("UPDATE versions SET content_blob=x'00' WHERE id LIKE ?",
                             (key + ":%",))
            return validate(key)

        monkeypatch.setattr(repo, "validate_candidate", corrupt)
        with pytest.raises(StorageFailure):
            app.synchronize.execute()
        assert app.status.execute().active_snapshot_id == previous
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1


def test_v2_reader_outcomes_preserve_snapshot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "empty.txt").write_text("", encoding="utf-8")
    (source / "empty.md").write_text("", encoding="utf-8")
    (source / "note.md").write_text("# Alfa", encoding="utf-8")
    empty_pdf = PdfWriter()
    empty_pdf.add_blank_page(width=100, height=100)
    empty_pdf.write(source / "empty.pdf")
    with compose_v2_application(tmp_path / "storage") as app:
        first = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(first.job.job_id)
        original = app.status.execute().active_snapshot_id
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1
        with app.snapshots.acquire() as snapshot:
            assert snapshot.manifest.entries
            assert sum(entry.document_id is None for entry in snapshot.manifest.entries.values()) == 1
        protected = PdfWriter()
        protected.add_blank_page(width=100, height=100)
        protected.encrypt("secret")
        protected.write(source / "protected.pdf")
        from local_document_search.application.errors import ExtractionFailure
        with pytest.raises(ExtractionFailure):
            app.synchronize.execute()
        assert app.status.execute().active_snapshot_id == original


def test_v2_directory_switch_and_clear_during_job(tmp_path, monkeypatch):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    (first_root / "first.txt").write_text("alfa", encoding="utf-8")
    (second_root / "second.txt").write_text("beta", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        job = app.select_directory.execute(str(first_root)).job
        app._lifecycle.jobs.wait(job.job_id)
        first_snapshot = app.status.execute().active_snapshot_id
        job = app.select_directory.execute(str(second_root)).job
        app._lifecycle.jobs.wait(job.job_id)
        from local_document_search.application.errors import SnapshotUnavailable
        with pytest.raises(SnapshotUnavailable):
            with app.snapshots.acquire(first_snapshot):
                pass
        assert app.search.execute(SearchRequest("beta")).total_matches == 1
        (second_root / "third.txt").write_text("gamma", encoding="utf-8")
        entered, release = Event(), Event()
        reader = app._lifecycle.synchronizer.reader
        original = reader.read

        def blocked(candidate):
            entered.set()
            assert release.wait(5)
            return original(candidate)

        monkeypatch.setattr(reader, "read", blocked)
        try:
            job = app.request_synchronization.execute()
            assert entered.wait(5)
            from local_document_search.application.contracts import InvalidInput
            with pytest.raises(InvalidInput):
                app.clear_local_data.execute()
            with pytest.raises(InvalidInput):
                app.select_directory.execute(str(first_root))
        finally:
            release.set()
        app._lifecycle.jobs.wait(job.job_id)
        job = app.select_directory.execute(str(first_root)).job
        app._lifecycle.jobs.wait(job.job_id)
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1
        assert (first_root / "first.txt").exists()


def test_v2_nochange_keeps_snapshot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("alfa", encoding="utf-8")
    with compose_v2_application(tmp_path / "storage") as app:
        job = app.select_directory.execute(str(source)).job
        app._lifecycle.jobs.wait(job.job_id)
        original = app.status.execute().active_snapshot_id
        result = app.synchronize.execute()
        assert not result.changed
        assert result.snapshot_id == original


def test_v2_process_crash_before_commit_recovers_previous(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    note = source / "note.txt"
    note.write_text("alfa", encoding="utf-8")
    storage = tmp_path / "storage"
    with compose_v2_application(storage) as app:
        job = app.select_directory.execute(str(source)).job
        app._lifecycle.jobs.wait(job.job_id)
        original = app.status.execute().active_snapshot_id
    note.write_text("beta longer", encoding="utf-8")
    script = """
import os, sys
from local_document_search.interfaces.composition import compose_v2_application
with compose_v2_application(sys.argv[1], read_workers=1) as app:
    def crash():
        os._exit(77)
    app.snapshots._repo._commit = crash
    app.synchronize.execute()
"""
    process = subprocess.run([sys.executable, "-c", script, str(storage)], capture_output=True)
    assert process.returncode == 77, process.stderr
    with compose_v2_application(storage) as app:
        assert app.status.execute().active_snapshot_id == original
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1
        assert app.search.execute(SearchRequest("beta")).total_matches == 0


@pytest.mark.skipif(sys.platform != "win32", reason="Default storage Windows")
def test_neutral_default_storage_preserves_both_legacy_locations(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    markers = [tmp_path / "LocalDocumentSearch" / "control.sqlite3",
               tmp_path / "LocalDocumentSearchV2" / "control-v2.sqlite3"]
    for marker in markers:
        marker.parent.mkdir()
        marker.write_bytes(b"legacy data")
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("alfa", encoding="utf-8")
    with _compose_v2_application(read_workers=1) as app:
        assert not app.initialize.execute().search_available
        state = app.select_directory.execute(str(source))
        app._lifecycle.jobs.wait(state.job.job_id)
        assert app.search.execute(SearchRequest("alfa")).total_matches == 1
    assert (tmp_path / "LocalDocumentSearch/Data/control-v2.sqlite3").is_file()
    with _compose_v2_application(read_workers=1) as app:
        state = app.initialize.execute()
        assert state.search_available
        app._lifecycle.jobs.wait(state.job.job_id)
        app.clear_local_data.execute()
    assert all(marker.read_bytes() == b"legacy data" for marker in markers)
