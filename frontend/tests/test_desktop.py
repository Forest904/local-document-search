from concurrent.futures import Future
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from types import SimpleNamespace
import ast
import tomllib

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from local_document_search.application.contracts import (
    ApplicationState, JobPhase, JobRef, JobState, JobStatus, SearchResponse,
)
from local_document_search.application.errors import SnapshotUnavailable, StorageFailure
from local_document_search_desktop.composition import compose_desktop, open_document
from local_document_search_desktop.window import PRIVACY, SearchWindow
from conftest import until


class Requests:
    def __init__(self):
        self.calls = []

    def submit(self, *args):
        future = Future()
        self.calls.append((args, future))
        return future


class FakeSession:
    def __init__(self):
        self.state = ApplicationState("C:/source", "N", True)
        self.search, self.get_document = Requests(), Requests()
        self.initialize = SimpleNamespace(execute=lambda: self.state)
        self.status = SimpleNamespace(execute=lambda: self.state)
        self.clear_local_data = SimpleNamespace(execute=self.clear)
        self.closed = False

    def clear(self):
        self.state = ApplicationState(None, None, False)
        return self.state

    def close(self):
        self.closed = True


@pytest.fixture
def window(qt):
    session = FakeSession()
    window = SearchWindow(lambda: session, lambda *_: None)
    window.show()
    yield window, session
    window.close()
    until(lambda: window.closed)


def start(window):
    QTest.mouseClick(window.start, Qt.MouseButton.LeftButton)
    until(lambda: window.session is not None)


def answer(window, session, snapshot="N", total=120):
    session.search.calls[-1][1].set_result(SearchResponse(snapshot, (), total))
    window.tick()
    until(lambda: window.response is not None and window.response.snapshot_id == snapshot)


def test_privacy_precedes_factory_and_enter_only(window):
    w, s = window
    assert w.session is None and w.message.text() == PRIVACY
    assert not w.query.isEnabled()
    start(w)
    w.query.setText("alpha")
    assert not s.search.calls
    QTest.keyClick(w.query, Qt.Key.Key_Return)
    assert s.search.calls[0][0][0].limit == 50
    answer(w, s, total=0)
    assert w.results.topLevelItemCount() == 0
    assert "0 risultati" in w.count.text()
    assert not w.next.isEnabled()


def test_pagination_version_reset_and_stale_reset(window):
    w, s = window
    start(w)
    w.query.setText("alpha")
    w.search()
    answer(w, s)
    w.search(50)
    answer(w, s)
    assert w.offset == 50
    w.search(100)
    s.search.calls[-1][1].set_result(SearchResponse("N2", (), 130))
    until(lambda: len(s.search.calls) == 4)
    assert s.search.calls[-1][0][0].offset == 0
    w.field.setCurrentIndex(1)
    s.search.calls[-1][1].set_result(SearchResponse("N2", (), 130))
    QTest.qWait(250)
    assert w.response is None
    w.search()
    answer(w, s, "N2")
    assert w.offset == 0


def test_changed_snapshot_returns_to_first_page(window):
    w, s = window
    start(w)
    w.query.setText("alpha")
    w.search()
    answer(w, s)
    w.search(50)
    s.search.calls[-1][1].set_result(SearchResponse("N2", (), 0))
    until(lambda: len(s.search.calls) == 3)
    assert s.search.calls[-1][0][0].offset == 0
    answer(w, s, "N2", 0)
    assert w.offset == 0 and w.response.total_matches == 0


def test_source_unavailable_preserves_search(qt, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("alpha", encoding="utf-8")
    with compose_desktop(tmp_path / "storage") as session:
        session.select_directory.execute(str(source))
        session.synchronize.execute()
    source.rename(tmp_path / "offline")
    w = SearchWindow(lambda: compose_desktop(tmp_path / "storage"), lambda *_: None)
    w.show()
    try:
        start(w)
        until(lambda: w.state.warning is not None)
        assert w.query.isEnabled() and "SourceUnavailable" in w.status.text()
        w.query.setText("alpha")
        w.search()
        until(lambda: w.response is not None)
        assert w.response.total_matches == 1
    finally:
        w.close()
        until(lambda: w.closed)


@pytest.mark.parametrize("change", ["query", "field", "directory"])
@pytest.mark.parametrize("error", [False, True])
def test_obsolete_response_or_error_ignored(window, change, error):
    w, s = window
    start(w)
    w.query.setText("alpha")
    w.search()
    future = s.search.calls[-1][1]
    if change == "query":
        w.query.setText("beta")
    elif change == "field":
        w.field.setCurrentIndex(2)
    else:
        w.apply_state(ApplicationState("C:/other", None, False))
    if error:
        future.set_exception(ValueError("OBSOLETO"))
    else:
        future.set_result(SearchResponse("N", (), 100))
    w.tick()
    assert w.response is None and "OBSOLETO" not in w.message.text()


def test_progress_timer_and_reused_job(window):
    w, s = window
    start(w)
    ref = JobRef("j", JobState.RUNNING, True)
    w.apply_state(replace(s.state, job=ref))
    job = JobStatus("j", JobState.RUNNING, JobPhase.SCANNING, datetime.now(timezone.utc))
    w.apply_job(job)
    assert not w.clear.isEnabled() and not w.choose.isEnabled()
    assert w.query.isEnabled() and w.progress.maximum() == 0
    assert w.timer.interval() == 200 and w.check_timer.interval() == 1500
    w.apply_job(replace(job, state=JobState.COMPLETED))
    assert w.check_timer.isActive()
    w.check_timer.stop()
    w.sync.setText("Sync")
    w.apply_job(replace(job, state=JobState.COMPLETED))
    assert not w.check_timer.isActive() and w.sync.text() == "Sync"
    w.apply_job(replace(job, job_id="failed", state=JobState.FAILED, error="ExtractionFailure"))
    assert "ExtractionFailure" in w.message.text()


def test_clear_confirmation_and_failure(window, monkeypatch):
    w, s = window
    start(w)
    monkeypatch.setattr(QMessageBox, "question", lambda *_: QMessageBox.StandardButton.No)
    w.clear_data()
    assert w.state.active_directory
    monkeypatch.setattr(QMessageBox, "question", lambda *_: QMessageBox.StandardButton.Yes)
    original = s.clear_local_data.execute
    def fail():
        raise StorageFailure("riprovare")
    s.clear_local_data.execute = fail
    w.clear_data()
    until(lambda: not w.control_pending)
    assert "riprovare" in w.message.text() and w.state.active_directory
    s.clear_local_data.execute = original
    w.clear_data()
    until(lambda: w.state.active_directory is None)
    assert not w.query.isEnabled() and w.choose.isEnabled()


def test_startup_failure_can_retry(window):
    w, _ = window
    def fail():
        raise StorageFailure("Istanza già aperta")
    w.factory = fail
    w.initialize()
    until(lambda: not w.control_pending)
    assert "Istanza" in w.message.text() and w.start.isEnabled()


def test_incompatible_startup_without_source_allows_recovery(window):
    w, s = window
    s.state = ApplicationState(None, None, False)
    def incompatible():
        raise SnapshotUnavailable("incompatibile")
    s.initialize.execute = incompatible
    start(w)
    assert w.choose.isEnabled() and w.clear.isEnabled() and not w.query.isEnabled()
    assert "ricostruirlo" in w.message.text()


def test_close_during_composition_waits_and_releases(window):
    w, s = window
    entered, release = Event(), Event()
    def create():
        entered.set()
        assert release.wait(5)
        return s
    w.factory = create
    w.initialize()
    try:
        until(entered.is_set)
        w.close()
        QTest.qWait(80)
        assert not w.closed
    finally:
        release.set()
    until(lambda: w.closed)
    assert s.closed


@pytest.mark.parametrize("operation", ["build", "search", "preview"])
def test_real_workers_keep_event_loop_live_and_close_waits(qt, tmp_path, monkeypatch, operation):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("alpha", encoding="utf-8")
    session = compose_desktop(tmp_path / "storage")
    state = session.select_directory.execute(str(source))
    session._lifecycle.jobs.wait(state.job.job_id)
    entered, release = Event(), Event()
    if operation == "build":
        target, name = session._lifecycle.synchronizer.discovery, "discover"
    else:
        target, name = session.search if operation == "search" else session.get_document, "_execute"
    original = getattr(target, name)
    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)
    monkeypatch.setattr(target, name, blocked)
    w = SearchWindow(lambda: session, lambda *_: None)
    w.show()
    try:
        start(w)
        if operation != "build":
            until(lambda: w.state.job.status == JobState.COMPLETED)
            w.query.setText("alpha")
            w.search()
            if operation == "preview":
                until(lambda: w.response is not None)
                w.results.setCurrentItem(w.results.topLevelItem(0))
        until(entered.is_set)
        beats = []
        QTimer.singleShot(10, lambda: beats.append(True))
        until(lambda: bool(beats))
        assert not w.closed
        w.close()
        QTest.qWait(80)
        assert not w.closed
    finally:
        release.set()
        w.close()
        until(lambda: w.closed)


def test_invalid_query_current_error_and_no_change(window):
    w, s = window
    start(w)
    w.search()
    assert "InvalidInput" in w.message.text()
    w.apply_state(replace(s.state, last_sync_outcome="no_changes"))
    assert w.status.text() == "Indice aggiornato"
    w.query.setText('"aperta')
    w.search()
    s.search.calls[-1][1].set_exception(ValueError("Virgolette sbilanciate"))
    w.tick()
    assert "Virgolette" in w.message.text()


def test_poll_does_not_accumulate_and_close_waits(window):
    w, s = window
    start(w)
    entered, release = Event(), Event()
    def status():
        entered.set()
        assert release.wait(5)
        return s.state
    s.status.execute = status
    try:
        until(entered.is_set)
        QTest.qWait(450)
        assert len(w.pending) == 1
        beats = []
        QTimer.singleShot(10, lambda: beats.append(True))
        w.close()
        QTest.qWait(80)
        assert beats and not w.closed
    finally:
        release.set()
    until(lambda: w.closed)
    assert s.closed


def test_real_backend_search_preview_restart_clear(qt, tmp_path, monkeypatch):
    source, storage = tmp_path / "source", tmp_path / "storage"
    source.mkdir()
    for i in range(55):
        (source / f"file{i:02}.txt").write_text("alpha <b>testo semplice</b>", encoding="utf-8")
    w = SearchWindow(lambda: compose_desktop(storage), lambda *_: None)
    w.show()
    try:
        start(w)
        monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *_: str(source))
        w.select_directory()
        until(lambda: w.state.search_available or bool(w.message.text()))
        assert w.state.search_available, w.message.text()
        with pytest.raises(StorageFailure):
            compose_desktop(storage)
        w.query.setText("alpha")
        w.search()
        until(lambda: w.response is not None)
        assert w.results.topLevelItemCount() == 50 and w.response.total_matches == 55
        w.results.setCurrentItem(w.results.topLevelItem(0))
        until(lambda: "<b>" in w.preview.toPlainText())
        w.search(50)
        until(lambda: w.offset == 50)
        assert w.results.topLevelItemCount() == 5
        snapshot = w.response.snapshot_id
    finally:
        w.close()
        until(lambda: w.closed)
    w = SearchWindow(lambda: compose_desktop(storage), lambda *_: None)
    w.show()
    try:
        start(w)
        until(lambda: w.state.job.status == JobState.COMPLETED)
        assert w.state.active_snapshot_id == snapshot
        monkeypatch.setattr(QMessageBox, "question", lambda *_: QMessageBox.StandardButton.Yes)
        w.clear_data()
        until(lambda: w.state.active_directory is None)
        assert len(list(source.glob("*.txt"))) == 55
    finally:
        w.close()
        until(lambda: w.closed)


def test_preview_obsolete_and_removed_snapshot(window):
    w, s = window
    start(w)
    from PySide6.QtWidgets import QTreeWidgetItem
    w.response = SearchResponse("N", (), 1)
    item = QTreeWidgetItem(["a.txt"])
    item.setData(0, Qt.ItemDataRole.UserRole, SimpleNamespace(document_id=1))
    w.results.addTopLevelItem(item)
    w.results.setCurrentItem(item)
    first = s.get_document.calls[-1][1]
    w.invalidate()
    first.set_result(SimpleNamespace(extracted_text="obsoleto"))
    w.tick()
    assert not w.preview.toPlainText()
    w.response = SearchResponse("N", (), 1)
    item = QTreeWidgetItem(["a.txt"])
    item.setData(0, Qt.ItemDataRole.UserRole, SimpleNamespace(document_id=1))
    w.results.addTopLevelItem(item)
    w.results.setCurrentItem(item)
    s.get_document.calls[-1][1].set_exception(SnapshotUnavailable())
    w.tick()
    assert "Ripeti la ricerca" in w.message.text()


def test_file_opener_missing_and_local_url(tmp_path, monkeypatch):
    from local_document_search_desktop import composition
    relative = SimpleNamespace(value="a b.txt")
    with pytest.raises(FileNotFoundError, match="Sync"):
        open_document(str(tmp_path), relative)
    (tmp_path / relative.value).write_text("alpha")
    calls = []
    monkeypatch.setattr(composition.QDesktopServices, "openUrl", lambda url: calls.append(url) or True)
    open_document(str(tmp_path), relative)
    assert calls[0].isLocalFile() and Path(calls[0].toLocalFile()) == tmp_path / relative.value
    monkeypatch.setattr(composition.QDesktopServices, "openUrl", lambda _: False)
    with pytest.raises(OSError):
        open_document(str(tmp_path), relative)


def test_frontend_boundaries_and_backend_without_qt_dependency():
    root = Path(__file__).resolve().parents[2]
    for file in (root / "frontend/src").rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                if name.startswith("local_document_search."):
                    assert ".domain" not in name and ".infrastructure" not in name
                    assert ".interfaces" not in name or file.name == "composition.py"
    metadata = tomllib.loads((root / "backend/pyproject.toml").read_text())
    assert not any("pyside" in dep.lower() for dep in metadata["project"]["dependencies"])
