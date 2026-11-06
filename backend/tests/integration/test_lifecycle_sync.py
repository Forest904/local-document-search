import os
from contextlib import closing
import sqlite3
from threading import Thread, Event

import pytest

from local_document_search.application.contracts import SearchRequest, InvalidInput
from local_document_search.application.errors import ExtractionFailure, SnapshotUnavailable, SourceUnavailable, StorageFailure
from local_document_search.application.synchronization import IndexSynchronizer
from local_document_search.infrastructure.filesystem import DocumentFileDiscovery
from local_document_search.infrastructure.readers.text import TextReader
from local_document_search.infrastructure.snapshot_storage import InMemorySnapshotRepository
from local_document_search.interfaces.composition import compose_persistent_application


@pytest.fixture
def roots(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    return source, tmp_path / 'storage'


def write(root, name, text):
    (root / name).write_text(text, encoding='utf-8')


def results(app, query):
    return app.search.execute(SearchRequest(query)).total_matches


def test_incremental_reuse_identity_and_isolation(roots):
    source, _ = roots
    write(source, 'keep.txt', 'unchanged')
    write(source, 'edit.txt', 'old')
    write(source, 'gone.txt', 'removed')
    repo = InMemorySnapshotRepository()
    reader = TextReader()
    sync = IndexSynchronizer(DocumentFileDiscovery(), reader, repo)
    sync.execute(str(source))
    old = repo.load_active()
    previous_ids = {p.value: e.document_id for p, e in old.manifest.entries.items()}
    write(source, 'edit.txt', 'replacement text')
    (source / 'gone.txt').rename(source / 'renamed.txt')
    calls = []
    original = reader.read
    def read(candidate):
        calls.append(candidate.metadata.relative_path.value)
        return original(candidate)
    reader.read = read
    report = sync.execute(str(source))
    current = repo.load_active()
    current_ids = {p.value: e.document_id for p, e in current.manifest.entries.items()}
    assert (report.added, report.modified, report.removed, report.unchanged) == (1, 1, 1, 1)
    assert calls == ['edit.txt', 'renamed.txt']
    assert previous_ids['edit.txt'] == current_ids['edit.txt']
    assert current_ids['renamed.txt'].value > max(i.value for i in previous_ids.values())
    assert current.catalog.documents[current_ids['keep.txt']] is old.catalog.documents[previous_ids['keep.txt']]
    assert 'old' in old.content_index.terms and 'old' not in current.content_index.terms
    assert 'gone' in old.filename_index.terms and 'gone' not in current.filename_index.terms
    assert 'renamed' in current.filename_index.terms


def test_restart_no_change_and_accepted_fingerprint_limit(roots):
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        state = app.select_directory.execute(str(source))
        key = state.active_snapshot_id
    stat = (source / 'a.txt').stat()
    write(source, 'a.txt', 'bravo')
    os.utime(source / 'a.txt', ns=(stat.st_atime_ns, stat.st_mtime_ns))
    with compose_persistent_application(storage) as app:
        state = app.initialize.execute()
        assert state.active_snapshot_id == key
        assert state.last_sync_outcome == 'no_changes'
        assert results(app, 'alpha') == 1
        assert results(app, 'bravo') == 0


def test_missing_source_keeps_search(roots):
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
    source.rename(source.with_name('moved'))
    with compose_persistent_application(storage) as app:
        state = app.initialize.execute()
        assert state.search_available and state.warning == 'SourceUnavailable'
        assert results(app, 'alpha') == 1


def test_directory_switch_and_invalid_selection(roots):
    source, storage = roots
    other = source.with_name('other')
    other.mkdir()
    write(source, 'a.txt', 'alpha')
    write(other, 'b.txt', 'bravo')
    with compose_persistent_application(storage) as app:
        a = app.select_directory.execute(str(source))
        with pytest.raises(SourceUnavailable):
            app.select_directory.execute(str(source / 'missing'))
        assert results(app, 'alpha') == 1
        with app.snapshots.acquire() as held:
            app.select_directory.execute(str(other))
            assert held.snapshot_id == a.active_snapshot_id
            assert results(app, 'alpha') == 0
            with pytest.raises(SnapshotUnavailable):
                with app.snapshots.acquire(a.active_snapshot_id):
                    pass
        again = app.select_directory.execute(str(source))
        assert again.active_snapshot_id != a.active_snapshot_id
        assert results(app, 'alpha') == 1


def test_failure_preserves_old_and_guard(roots):
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        before = app.select_directory.execute(str(source))
        lifecycle = app.synchronize.lifecycle
        original = lifecycle.synchronizer.reader.read
        def read(candidate):
            with pytest.raises(InvalidInput):
                app.clear_local_data.execute()
            with pytest.raises(InvalidInput):
                app.select_directory.execute(str(source))
            return original(candidate)
        lifecycle.synchronizer.reader.read = read
        (source / 'bad.txt').write_bytes(b'\xff')
        with pytest.raises(ExtractionFailure):
            app.synchronize.execute()
        assert app.status.execute().active_snapshot_id == before.active_snapshot_id
        assert app.status.execute().last_sync_outcome == 'failed'
        assert results(app, 'alpha') == 1


@pytest.mark.parametrize('kind', ['physical', 'processing', 'schema'])
@pytest.mark.parametrize('fail', [False, True])
def test_incompatible_rebuild(roots, kind, fail):
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        old = app.select_directory.execute(str(source)).active_snapshot_id
        name = app.snapshots.settings.selected()
    with closing(sqlite3.connect(storage / name)) as db:
        if kind == 'physical':
            db.execute('PRAGMA user_version=99')
        else:
            column = 'processing_version' if kind == 'processing' else 'schema_version'
            db.execute(f"UPDATE snapshots SET {column}='99'")
        db.commit()
    if fail:
        (source / 'bad.txt').write_bytes(b'\xff')
    with compose_persistent_application(storage) as app:
        with pytest.raises(SnapshotUnavailable):
            results(app, 'alpha')
        if fail:
            with pytest.raises(ExtractionFailure):
                app.initialize.execute()
            assert app.snapshots.settings.selected() == name
            assert (storage / name).exists()
        else:
            state = app.initialize.execute()
            assert state.active_snapshot_id != old and state.search_available
            assert results(app, 'alpha') == 1
            assert not (storage / name).exists()


def test_empty_and_removal_only(roots):
    source, storage = roots
    with compose_persistent_application(storage) as app:
        first = app.select_directory.execute(str(source))
        assert first.search_available
        assert not app.synchronize.execute().changed
        write(source, 'a.txt', 'alpha')
        app.synchronize.execute()
        (source / 'a.txt').unlink()
        result = app.synchronize.execute()
        assert result.removed == 1 and result.processed_bytes == 0
        assert results(app, 'alpha') == 0


def test_clear_waits_for_reader_and_preserves_foreign_files(roots):
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
        write(storage, 'foreign.txt', 'keep')
        entered, release = Event(), Event()
        def reader():
            with app.snapshots.acquire() as snapshot:
                entered.set()
                release.wait(5)
                assert snapshot.catalog.documents
        thread = Thread(target=reader)
        thread.start()
        assert entered.wait(5)
        def unblock():
            # clear must set its read barrier before the existing lease ends.
            for _ in range(1000):
                if app.snapshots._blocked:
                    with pytest.raises(SnapshotUnavailable):
                        with app.snapshots.acquire():
                            pass
                    release.set()
                    return
                Event().wait(.005)
            release.set()
        helper = Thread(target=unblock)
        helper.start()
        assert app.clear_local_data.execute().active_directory is None
        thread.join(5)
        helper.join(5)
        assert (source / 'a.txt').read_text() == 'alpha'
        assert (storage / 'foreign.txt').read_text() == 'keep'
        assert not list(storage.glob('snapshot-*.sqlite3'))
        assert not app.initialize.execute().search_available


def test_excluded_reuse_and_transitions(roots):
    from local_document_search.application.ports import Excluded
    source, _ = roots
    write(source, 'a.txt', 'excluded')
    repo = InMemorySnapshotRepository()
    reader = TextReader()
    calls = []
    original = reader.read
    def read(candidate):
        calls.append(candidate)
        if (source / 'a.txt').read_text() == 'excluded':
            return Excluded('synthetic exclusion')
        return original(candidate)
    reader.read = read
    sync = IndexSynchronizer(DocumentFileDiscovery(), reader, repo)
    assert sync.execute(str(source)).excluded == 1
    assert not sync.execute(str(source)).changed
    assert len(calls) == 1
    write(source, 'a.txt', 'indexed text')
    assert sync.execute(str(source)).excluded == 0
    assert repo.load_active().catalog.documents
    write(source, 'a.txt', 'excluded')
    assert sync.execute(str(source)).excluded == 1
    assert not repo.load_active().catalog.documents
    assert not repo.load_active().filename_index.terms
    assert not repo.load_active().content_index.terms


def test_legacy_m5_storage(roots):
    from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository
    from local_document_search.application.synchronization import BuildIndex
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with SqliteSnapshotRepository(storage) as repo:
        result = BuildIndex(DocumentFileDiscovery(), TextReader(), repo).execute(str(source))
    with compose_persistent_application(storage) as app:
        assert app.initialize.execute().active_snapshot_id == result.snapshot_id
        assert app.snapshots.settings.selected() == 'snapshots.sqlite3'


def test_incompatible_source_absent(roots):
    source, storage = roots
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
        name = app.snapshots.settings.selected()
    with closing(sqlite3.connect(storage / name)) as db:
        db.execute('PRAGMA user_version=99')
    source.rmdir()
    with compose_persistent_application(storage) as app:
        with pytest.raises(SourceUnavailable):
            app.initialize.execute()
        assert (storage / name).exists()
        assert not app.status.execute().search_available


def test_clear_failure_is_retryable(roots, monkeypatch):
    from pathlib import Path
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
        unlink = Path.unlink
        def fail(path, *args, **kwargs):
            if path.name.startswith('snapshot-'):
                raise PermissionError('synthetic')
            return unlink(path, *args, **kwargs)
        monkeypatch.setattr(Path, 'unlink', fail)
        with pytest.raises(StorageFailure):
            app.clear_local_data.execute()
        assert not app.status.execute().search_available
        monkeypatch.setattr(Path, 'unlink', unlink)
        assert app.clear_local_data.execute().active_directory is None
        assert (source / 'a.txt').exists()


@pytest.mark.parametrize('phase', ['before', 'after'])
def test_rebuild_process_crash(roots, phase):
    import subprocess
    import sys
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        old = app.select_directory.execute(str(source)).active_snapshot_id
        name = app.snapshots.settings.selected()
    with closing(sqlite3.connect(storage / name)) as db:
        db.execute('PRAGMA user_version=99')
    script = '''
import os, sys
from local_document_search.interfaces.composition import compose_persistent_application
app = compose_persistent_application(sys.argv[1])
settings = app.snapshots.settings
original = settings.select
def crash(name):
    if sys.argv[2] == 'after':
        original(name)
    os._exit(77)
settings.select = crash
app.initialize.execute()
'''
    process = subprocess.run([sys.executable, '-c', script, str(storage), phase], capture_output=True)
    assert process.returncode == 77, process.stderr
    with compose_persistent_application(storage) as app:
        if phase == 'before':
            assert app.snapshots.settings.selected() == name
            assert not app.status.execute().search_available
        else:
            assert app.snapshots.settings.selected() != name
            assert app.status.execute().search_available
        state = app.initialize.execute()
        assert state.active_snapshot_id != old
        assert results(app, 'alpha') == 1
        assert len(list(storage.glob('snapshot-*.sqlite3'))) == 1


def test_commit_failure_preserves_snapshot(roots, monkeypatch):
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        old = app.select_directory.execute(str(source)).active_snapshot_id
        write(source, 'a.txt', 'new text')
        def fail():
            raise sqlite3.OperationalError('synthetic full disk')
        monkeypatch.setattr(app.snapshots._repo, '_commit', fail)
        with pytest.raises(StorageFailure):
            app.synchronize.execute()
        assert app.status.execute().active_snapshot_id == old
        assert results(app, 'alpha') == 1


def test_corrupt_storage_is_not_incompatibility(roots):
    source, storage = roots
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
        name = app.snapshots.settings.selected()
    (storage / name).write_bytes(b'not a database')
    with pytest.raises(StorageFailure):
        compose_persistent_application(storage)
    assert (storage / name).read_bytes() == b'not a database'


def test_unchanged_does_not_analyze(roots, monkeypatch):
    from local_document_search.domain.analysis import ContentAnalyzer, FilenameAnalyzer
    source, storage = roots
    write(source, 'a.txt', 'alpha')
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
        def fail(*args):
            pytest.fail('analyzer invoked for unchanged document')
        monkeypatch.setattr(ContentAnalyzer, 'analyze', fail)
        monkeypatch.setattr(FilenameAnalyzer, 'analyze', fail)
        report = app.synchronize.execute()
        assert not report.changed and report.processed_bytes == 0


def test_selection_failure_preserves_incompatible_database(roots, monkeypatch):
    source, storage = roots
    with compose_persistent_application(storage) as app:
        app.select_directory.execute(str(source))
        name = app.snapshots.settings.selected()
    with closing(sqlite3.connect(storage / name)) as db:
        db.execute('PRAGMA user_version=99')
    with compose_persistent_application(storage) as app:
        def fail(name):
            raise StorageFailure('synthetic selection failure')
        monkeypatch.setattr(app.snapshots.settings, 'select', fail)
        with pytest.raises(StorageFailure):
            app.initialize.execute()
        assert app.snapshots.settings.selected() == name
        assert not app.status.execute().search_available
        assert list(storage.glob('snapshot-*.sqlite3')) == [storage / name]


def test_fresh_start_and_corrupt_control(roots):
    _, storage = roots
    with compose_persistent_application(storage) as app:
        assert app.initialize.execute().active_directory is None
        with pytest.raises(InvalidInput):
            app.synchronize.execute()
    (storage / 'control.sqlite3').write_bytes(b'corrupt control')
    with pytest.raises(StorageFailure):
        compose_persistent_application(storage)


def test_legacy_incompatible_without_settings_requires_source(roots):
    from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository
    from local_document_search.application.synchronization import BuildIndex
    source, storage = roots
    with SqliteSnapshotRepository(storage) as repo:
        BuildIndex(DocumentFileDiscovery(), TextReader(), repo).execute(str(source))
    with closing(sqlite3.connect(storage / 'snapshots.sqlite3')) as db:
        db.execute('PRAGMA user_version=99')
    with compose_persistent_application(storage) as app:
        with pytest.raises(SnapshotUnavailable, match='selezionare'):
            app.initialize.execute()
        assert (storage / 'snapshots.sqlite3').exists()
        assert app.select_directory.execute(str(source)).search_available
