"""M7: interleaving controllati da eventi, senza attese temporali di correttezza."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import subprocess
import sys
from threading import Event

import pytest

from local_document_search.application.contracts import InvalidInput, JobPhase, JobState, SearchRequest
from local_document_search.application.errors import ExtractionFailure, SnapshotUnavailable, StorageFailure
from local_document_search.interfaces.composition import compose_persistent_application


@pytest.fixture
def corpus(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("alpha", encoding="utf-8")
    return source, tmp_path / "storage"


def ready(app, source):
    state = app.select_directory.execute(str(source))
    app._lifecycle.jobs.wait(state.job.job_id)
    return app.status.execute().active_snapshot_id


@contextmanager
def blocked_method(monkeypatch, target, name):
    entered, release = Event(), Event()
    original = getattr(target, name)
    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(10), "test did not release operation"
        return original(*args, **kwargs)
    monkeypatch.setattr(target, name, blocked)
    try:
        yield entered, release
    finally:
        release.set()


def test_overlapping_async_and_blocking_share_job(corpus, monkeypatch):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        discovery = app._lifecycle.synchronizer.discovery
        with blocked_method(monkeypatch, discovery, "discover") as (entered, release):
            state = app.select_directory.execute(str(source))
            assert entered.wait(5)
            first = state.job
            with ThreadPoolExecutor(max_workers=8) as callers:
                refs = list(callers.map(lambda _: app.request_synchronization.execute(), range(20)))
                assert all(ref.job_id == first.job_id and ref.reused for ref in refs)
                waiting = Event()
                original = app._lifecycle.jobs.wait
                def wait(key):
                    waiting.set()
                    return original(key)
                monkeypatch.setattr(app._lifecycle.jobs, "wait", wait)
                sync = callers.submit(app.synchronize.execute)
                assert waiting.wait(5) and not sync.done()
                status = app.job_status.execute(first.job_id)
                assert status.phase == JobPhase.SCANNING and status.bytes_total is None
                assert status.files_total is None and status.progress is None
                with pytest.raises(InvalidInput):
                    app.clear_local_data.execute()
                with pytest.raises(InvalidInput):
                    app.select_directory.execute(str(source))
                release.set()
                result = sync.result(5)
            assert app.job_status.execute(first.job_id).state == JobState.COMPLETED
            assert result.snapshot_id == app.status.execute().active_snapshot_id
            assert app.job_status.execute(first.job_id).progress == 1
        with pytest.raises(InvalidInput):
            app.job_status.execute("unknown")
        with pytest.raises(InvalidInput):
            app.request_synchronization.execute("unknown")


def test_commit_does_not_block_old_snapshot_queries(corpus, monkeypatch):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        (source / "a.txt").write_text("replacement", encoding="utf-8")
        repo = app.snapshots._repo
        with blocked_method(monkeypatch, repo, "_commit") as (entered, release):
            job = app.request_synchronization.execute()
            assert entered.wait(5)
            response = app.search.submit(SearchRequest("alpha")).result(5)
            assert response.snapshot_id == old and response.total_matches == 1
            detail = app.get_document.submit(response.results[0].document_id, old).result(5)
            assert detail.extracted_text == "alpha"
            status = app.job_status.execute(job.job_id)
            assert status.phase == JobPhase.COMMITTING and status.state == JobState.RUNNING
            assert status.bytes_completed == status.bytes_total == len("replacement")
            assert status.files_completed == status.files_total == 1
            assert status.progress < 1
            release.set()
            app._lifecycle.jobs.wait(job.job_id)
        assert app.search.submit(SearchRequest("replacement")).result(5).snapshot_id != old
        assert app.search.execute(SearchRequest("alpha")).total_matches == 0


def test_long_query_keeps_version_through_two_commits(corpus, monkeypatch):
    from local_document_search.domain.queries import QueryEvaluator
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        with blocked_method(monkeypatch, QueryEvaluator, "evaluate") as (entered, release):
            query = app.search.submit(SearchRequest("alpha"))
            assert entered.wait(5)
            for content in ("bravo bravo", "charlie charlie charlie"):
                (source / "a.txt").write_text(content, encoding="utf-8")
                app.synchronize.execute()
            with app.snapshots.acquire(old) as snapshot:
                assert "alpha" in snapshot.content_index.terms
            release.set()
            result = query.result(5)
            assert result.snapshot_id == old and result.total_matches == 1
        with pytest.raises(SnapshotUnavailable):
            with app.snapshots.acquire(old):
                pass


def test_failed_job_then_retry_and_async_error(corpus, monkeypatch):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        (source / "bad.txt").write_bytes(b"\xff")
        job = app.request_synchronization.execute()
        with pytest.raises(ExtractionFailure):
            app._lifecycle.jobs.wait(job.job_id)
        failure = app.job_status.execute(job.job_id)
        assert failure.state == JobState.FAILED and failure.error == "ExtractionFailure"
        assert not failure.report.complete
        assert failure.report.published_snapshot_id is None
        assert failure.report.diagnostics[0].relative_path == "bad.txt"
        assert "\\xff" not in failure.report.diagnostics[0].reason
        assert failure.finished_at >= failure.started_at
        assert failure.progress != 1 and app.status.execute().active_snapshot_id == old
        (source / "bad.txt").unlink()
        next_job = app.request_synchronization.execute()
        assert next_job.job_id != job.job_id and not next_job.reused
        app._lifecycle.jobs.wait(next_job.job_id)
        assert app.job_status.execute(job.job_id) == failure
        with pytest.raises(InvalidInput):
            app.search.submit(SearchRequest('"unfinished')).result(5)


def test_reader_report_never_exposes_raw_exception_text(corpus, monkeypatch):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        ready(app, source)
        (source / "b.txt").write_text("bravo", encoding="utf-8")
        def unsafe(_):
            raise RuntimeError("secret query /absolute/private/path")
        monkeypatch.setattr(app._lifecycle.synchronizer.reader, "read", unsafe)
        job = app.request_synchronization.execute()
        with pytest.raises(ExtractionFailure):
            app._lifecycle.jobs.wait(job.job_id)
        diagnostic = app.job_status.execute(job.job_id).report.diagnostics[-1]
        assert diagnostic.relative_path == "b.txt"
        assert "secret" not in diagnostic.reason
        assert "/absolute/" not in diagnostic.reason


@pytest.mark.parametrize("scenario", ["empty", "zero", "removals", "unchanged", "excluded"])
def test_progress_zero_work_and_exclusions(corpus, scenario):
    from local_document_search.application.ports import Excluded
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        ready(app, source)
        if scenario in ("empty", "removals"):
            (source / "a.txt").unlink()
        elif scenario == "zero":
            (source / "a.txt").write_bytes(b"")
        elif scenario == "excluded":
            (source / "a.txt").write_text("excluded bytes", encoding="utf-8")
            app._lifecycle.synchronizer.reader.read = lambda _: Excluded("synthetic")
        if scenario == "empty":
            app.synchronize.execute()
        job = app.request_synchronization.execute()
        result = app._lifecycle.jobs.wait(job.job_id)
        status = app.job_status.execute(job.job_id)
        assert status.state == JobState.COMPLETED and status.progress == 1
        assert status.files_completed == status.files_total
        assert status.bytes_completed == status.bytes_total == result.processed_bytes
        if scenario == "excluded":
            assert result.excluded == 1 and status.files_completed == 1
            assert status.report.excluded == 1
            assert status.report.diagnostics[0].relative_path == "a.txt"
            assert result.report == status.report


def test_commit_failure_never_reports_success(corpus, monkeypatch):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        (source / "b.txt").write_text("bravo", encoding="utf-8")
        def fail():
            raise StorageFailure("synthetic commit failure")
        monkeypatch.setattr(app.snapshots._repo, "_commit", fail)
        job = app.request_synchronization.execute()
        with pytest.raises(StorageFailure):
            app._lifecycle.jobs.wait(job.job_id)
        status = app.job_status.execute(job.job_id)
        assert status.phase == JobPhase.COMMITTING and status.state == JobState.FAILED
        assert status.progress < 1 and app.status.execute().active_snapshot_id == old


def test_close_waits_for_job_and_read_and_rejects_admissions(corpus, monkeypatch):
    from local_document_search.domain.queries import QueryEvaluator
    source, storage = corpus
    app = compose_persistent_application(storage)
    try:
        ready(app, source)
        with blocked_method(monkeypatch, QueryEvaluator, "evaluate") as (read_entered, read_release):
            query = app.search.submit(SearchRequest("alpha"))
            assert read_entered.wait(5)
            with blocked_method(monkeypatch, app._lifecycle.synchronizer.discovery, "discover") as (entered, release):
                app.request_synchronization.execute()
                assert entered.wait(5)
                closing = Event()
                original = app._reads.stop_accepting
                def stop():
                    original()
                    closing.set()
                monkeypatch.setattr(app._reads, "stop_accepting", stop)
                with ThreadPoolExecutor(max_workers=1) as pool:
                    closed = pool.submit(app.close)
                    try:
                        assert closing.wait(5) and not closed.done()
                        with pytest.raises(InvalidInput):
                            app.search.submit(SearchRequest("alpha"))
                        with pytest.raises(InvalidInput):
                            app.search.execute(SearchRequest("alpha"))
                        with pytest.raises(InvalidInput):
                            app.request_synchronization.execute()
                        with pytest.raises(StorageFailure):
                            compose_persistent_application(storage)
                    finally:
                        release.set()
                        read_release.set()
                    closed.result(5)
                assert query.result(5).total_matches == 1
        app.close()
        with compose_persistent_application(storage) as restarted:
            assert restarted.status.execute().search_available
    finally:
        app.close()


def test_select_invalidates_new_details_but_existing_query_finishes(corpus, monkeypatch):
    from local_document_search.domain.queries import QueryEvaluator
    source, storage = corpus
    other = source.parent / "other"
    other.mkdir()
    (other / "b.txt").write_text("bravo", encoding="utf-8")
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        identity = app.search.execute(SearchRequest("alpha")).results[0].document_id
        with blocked_method(monkeypatch, QueryEvaluator, "evaluate") as (entered, release):
            pending = app.search.submit(SearchRequest("alpha"))
            assert entered.wait(5)
            ready(app, other)
            with pytest.raises(SnapshotUnavailable):
                app.get_document.execute(identity, old)
            release.set()
            assert pending.result(5).snapshot_id == old


def test_lock_second_process_and_stale_file(corpus):
    source, storage = corpus
    script = """
import sys
from local_document_search.interfaces.composition import compose_persistent_application
from local_document_search.application.errors import StorageFailure
try:
    with compose_persistent_application(sys.argv[1]):
        pass
except StorageFailure:
    sys.exit(23)
"""
    with compose_persistent_application(storage) as app:
        ready(app, source)
        before = {p.name: p.read_bytes() for p in storage.glob("*.sqlite3")}
        child = subprocess.run([sys.executable, "-c", script, str(storage)], capture_output=True, timeout=10)
        assert child.returncode == 23, child.stderr
        assert {p.name: p.read_bytes() for p in storage.glob("*.sqlite3")} == before
    assert (storage / "session.lock").exists()
    child = subprocess.run([sys.executable, "-c", script, str(storage)], capture_output=True, timeout=10)
    assert child.returncode == 0, child.stderr


@pytest.mark.parametrize("phase", ["before", "after"])
def test_kill_releases_lock_and_recovers_commit(corpus, phase):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
    (source / "a.txt").write_text("replacement", encoding="utf-8")
    script = """
import os, sys
from local_document_search.interfaces.composition import compose_persistent_application
app = compose_persistent_application(sys.argv[1])
repo = app.snapshots._repo
original = repo._commit
def crash():
    if sys.argv[2] == 'after':
        original()
    os._exit(77)
repo._commit = crash
app.synchronize.execute()
"""
    child = subprocess.run([sys.executable, "-c", script, str(storage), phase], capture_output=True, timeout=10)
    assert child.returncode == 77, child.stderr
    with compose_persistent_application(storage) as app:
        response = app.search.execute(SearchRequest("alpha" if phase == "before" else "replacement"))
        assert response.total_matches == 1
        assert (response.snapshot_id == old) == (phase == "before")


def test_composition_failure_releases_lock(corpus, monkeypatch):
    import local_document_search.interfaces.composition as composition
    _, storage = corpus
    original = composition.PersistentSnapshotRepository
    def fail(*args):
        raise StorageFailure("synthetic setup failure")
    monkeypatch.setattr(composition, "PersistentSnapshotRepository", fail)
    with pytest.raises(StorageFailure):
        composition.compose_persistent_application(storage)
    monkeypatch.setattr(composition, "PersistentSnapshotRepository", original)
    with composition.compose_persistent_application(storage):
        pass


def test_startup_returns_compatible_snapshot_before_scan_finishes(corpus, monkeypatch):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
    with compose_persistent_application(storage) as app:
        with blocked_method(monkeypatch, app._lifecycle.synchronizer.discovery, "discover") as (entered, release):
            state = app.initialize.execute()
            assert entered.wait(5)
            assert state.search_available and state.active_snapshot_id == old
            assert state.job is not None
            assert app.search.submit(SearchRequest("alpha")).result(5).snapshot_id == old
            release.set()
            app._lifecycle.jobs.wait(state.job.job_id)


def test_progress_phases_and_monotone_completed_bytes(corpus):
    from local_document_search.application.synchronization import IndexSynchronizer
    from local_document_search.infrastructure.filesystem import DocumentFileDiscovery
    from local_document_search.infrastructure.readers.text import TextReader
    from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
    source, _ = corpus
    (source / "b.txt").write_text("bravo bravo", encoding="utf-8")
    progress = []
    sync = IndexSynchronizer(DocumentFileDiscovery(), TextReader(), InMemorySnapshotRepository())
    sync.execute(str(source), lambda **changes: progress.append(changes))
    phases = [item["phase"] for item in progress if "phase" in item]
    assert phases[0] == JobPhase.SCANNING and phases[-1] == JobPhase.COMMITTING
    assert JobPhase.EXTRACTING in phases and JobPhase.ANALYZING in phases
    assert [item["bytes_completed"] for item in progress if "bytes_completed" in item] == [5, 16]
    assert [item["files_completed"] for item in progress if "files_completed" in item] == [1, 2]


def test_clear_waits_for_async_query_and_removes_operational_state(corpus, monkeypatch):
    from local_document_search.domain.queries import QueryEvaluator
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        with blocked_method(monkeypatch, QueryEvaluator, "evaluate") as (entered, release):
            query = app.search.submit(SearchRequest("alpha"))
            assert entered.wait(5)
            barrier = Event()
            original = app.snapshots._condition.wait
            def wait(*args, **kwargs):
                barrier.set()
                return original(*args, **kwargs)
            monkeypatch.setattr(app.snapshots._condition, "wait", wait)
            with ThreadPoolExecutor(max_workers=1) as pool:
                cleared = pool.submit(app.clear_local_data.execute)
                try:
                    assert barrier.wait(5) and not cleared.done()
                    with pytest.raises(SnapshotUnavailable):
                        app.search.execute(SearchRequest("alpha"))
                finally:
                    release.set()
                state = cleared.result(5)
            assert query.result(5).snapshot_id == old
            assert state.active_directory is None and state.job is None
            assert state.last_sync_outcome is None


def test_queued_query_uses_snapshot_at_execution_and_cancel_does_not_leak(corpus, monkeypatch):
    from local_document_search.domain.queries import QueryEvaluator
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
        with blocked_method(monkeypatch, QueryEvaluator, "evaluate") as (entered, release):
            first = app.search.submit(SearchRequest("alpha"))
            assert entered.wait(5)
            queued = app.search.submit(SearchRequest("replacement"))
            cancelled = app.search.submit(SearchRequest("alpha"))
            assert cancelled.cancel()
            (source / "a.txt").write_text("replacement", encoding="utf-8")
            current = app.synchronize.execute().snapshot_id
            release.set()
            assert first.result(5).snapshot_id == old
            response = queued.result(5)
            assert response.snapshot_id == current and response.total_matches == 1


def test_external_kill_releases_os_lock(corpus):
    source, storage = corpus
    with compose_persistent_application(storage) as app:
        old = ready(app, source)
    script = """
import sys
from threading import Event
from local_document_search.interfaces.composition import compose_persistent_application
app = compose_persistent_application(sys.argv[1])
def discover(root):
    print('scanning', flush=True)
    Event().wait()
app._lifecycle.synchronizer.discovery.discover = discover
app.synchronize.execute()
"""
    child = subprocess.Popen([sys.executable, "-u", "-c", script, str(storage)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            assert pool.submit(child.stdout.readline).result(5).strip() == "scanning"
            with pytest.raises(StorageFailure):
                compose_persistent_application(storage)
        finally:
            child.kill()
            child.communicate(timeout=5)
    with compose_persistent_application(storage) as app:
        assert app.search.execute(SearchRequest("alpha")).snapshot_id == old
