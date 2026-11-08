"""Regressioni desktop v2: controller reale, QML e worker controllati."""
from concurrent.futures import Future
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Event
from types import SimpleNamespace
import ast
import tomllib

import pytest
from PySide6.QtCore import QObject, QUrl, Qt, QTimer
from PySide6.QtGui import QTextDocument
from PySide6.QtTest import QTest

from local_document_search.application.contracts import (
    ApplicationState, CancelOutcome, DocumentDetails, JobDiagnostic, JobPhase, JobRef,
    JobReport, JobState, JobStatus, SearchResponse, SearchResult, SuggestResponse, TextRange,
)
from local_document_search.application.errors import SnapshotUnavailable, StorageFailure
from local_document_search.application.preferences import DesktopPreferences
from local_document_search.domain.documents import (
    DocumentId, DocumentFormat, RelativePath, DocumentMetadata, FileFingerprint,
)
from local_document_search.domain.queries import SearchField
from local_document_search_desktop.composition import compose_desktop, open_document
from local_document_search_desktop.controller import DesktopController
from local_document_search_desktop.main import create_engine
from local_document_search_desktop.models import highlighted, python_cursor
from conftest import until


class Requests:
    def __init__(self):
        self.calls = []

    def execute(self, *args):
        future = Future()
        self.calls.append((args, future))
        return future.result(timeout=10)

    def release(self):
        for _, future in self.calls:
            if not future.done():
                future.set_exception(SnapshotUnavailable("test teardown"))


def operation(function):
    return SimpleNamespace(execute=function)


class FakeSession:
    def __init__(self):
        self.state = ApplicationState("C:/source", "N", True)
        self.search, self.get_document, self.suggest = Requests(), Requests(), Requests()
        self.preferences = DesktopPreferences()
        self.initialize = operation(lambda: self.state)
        self.status = operation(lambda: self.state)
        self.get_preferences = operation(lambda: self.preferences)
        self.save_preferences = operation(self.save)
        self.clear_local_data = operation(self.clear)
        self.job_status = operation(lambda _: self.job)
        self.cancel_synchronization = operation(lambda _: CancelOutcome.ACCEPTED)
        self.request_synchronization = operation(lambda: None)
        self.rebuild = operation(lambda: None)
        self.recover_previous = operation(lambda: None)
        self.closed = False

    def save(self, value):
        self.preferences = value
        return value

    def clear(self):
        self.preferences = DesktopPreferences()
        self.state = ApplicationState(None, None, False)
        return self.state

    def close(self):
        self.closed = True


@pytest.fixture
def controller(qt):
    session = FakeSession()
    c = DesktopController(lambda: session, lambda *_: None)
    yield c, session
    c.requestClose()
    for requests in (session.search, session.get_document, session.suggest):
        requests.release()
    until(lambda: c.closed)


def start(c):
    c.initialize()
    until(lambda: c.session is not None)
    until(lambda: c.control_future is None)


def search(c, s, text="alpha", total=120, items=()):
    c.editQuery(text, len(text))
    count = len(s.search.calls)
    c.search()
    until(lambda: len(s.search.calls) > count)
    s.search.calls[-1][1].set_result(SearchResponse(c.state.active_snapshot_id, items, total))
    until(lambda: c.response is not None)


def result():
    return SearchResult(DocumentId(1), "alpha.txt", RelativePath("alpha.txt"),
                        DocumentFormat.TXT, frozenset({SearchField.CONTENT}))


def test_privacy_precedes_factory_and_typing_only_suggests(controller):
    c, s = controller
    assert c.session is None and not c.view["searchable"]
    start(c)
    c.editQuery("al", 2)
    until(lambda: bool(s.suggest.calls))
    assert not s.search.calls
    s.suggest.calls[-1][1].set_result(SuggestResponse("N", ("alpha",)))
    until(lambda: c.terms == ["alpha"])
    c.acceptSuggestion(0)
    assert c.query == "alpha" and not s.search.calls
    c.search()
    until(lambda: bool(s.search.calls))
    request = s.search.calls[0][0][0]
    assert request.limit == 50 and request.allow_prefixes
    assert request.order.value == "relevance"


@pytest.mark.parametrize("query,cursor,expected", [
    ('"al', 3, None), ('al*', 2, None), ('alpha be', 8, (6, 8, 'be')),
    ('alpha beta', 8, (6, 10, 'be')), ('a', 1, None), ('foo-bar', 7, None),
])
def test_suggestion_token_boundaries(controller, query, cursor, expected):
    c, _ = controller
    c.query, c.cursor = query, cursor
    assert c.suggestion_span() == expected


@pytest.mark.parametrize("change,error", [("query", False), ("query", True), ("options", False), ("directory", True)])
def test_obsolete_results_and_errors_ignored(controller, change, error):
    c, s = controller
    start(c)
    c.editQuery("alpha", 5)
    c.search()
    until(lambda: bool(s.search.calls))
    if change == "query":
        c.editQuery("beta", 4)
    elif change == "options":
        c.setOptions("content", ["txt"], "notes", "path")
    else:
        s.state = ApplicationState("C:/other", None, False)
        c.apply_state(s.state)
    future = s.search.calls[0][1]
    if error:
        future.set_exception(StorageFailure("old error"))
    else:
        future.set_result(SearchResponse("N", (), 5))
    until(lambda: c.read_future is None)
    assert c.response is None and not c.message_key


def test_bounded_suggestions_and_latest_query(controller):
    c, s = controller
    start(c)
    c.editQuery("al", 2)
    c.suggest()
    until(lambda: bool(s.suggest.calls))
    for index in range(50):
        c.editQuery("beta" + str(index), 6)
        c.suggest()
    assert len(s.suggest.calls) == 1 and len(c.queued_reads) <= 1
    s.suggest.calls[0][1].set_result(SuggestResponse("N", ("alpha",)))
    until(lambda: len(s.suggest.calls) == 2)
    assert c.terms == []


def test_filters_pagination_and_snapshot_restart(controller):
    c, s = controller
    start(c)
    c.setOptions("content", ["md", "txt"], "work", "path")
    search(c, s)
    request = s.search.calls[0][0][0]
    assert request.folder == "work" and request.formats == {DocumentFormat.TXT, DocumentFormat.MARKDOWN}
    c.page(1)
    until(lambda: len(s.search.calls) == 2)
    assert s.search.calls[-1][0][0].offset == 50
    s.search.calls[-1][1].set_result(SearchResponse("N", (), 120))
    until(lambda: c.offset == 50)
    s.state = replace(s.state, active_snapshot_id="N2")
    c.apply_state(s.state)
    until(lambda: len(s.search.calls) == 3)
    assert s.search.calls[-1][0][0].offset == 0
    s.search.calls[-1][1].set_result(SearchResponse("N2", (), 0))
    until(lambda: c.response is not None)
    assert not c.view["canNext"] and not c.view["canPrevious"]


def test_preview_is_bound_to_version_and_selection(controller):
    c, s = controller
    start(c)
    search(c, s, items=(result(),), total=1)
    c.selectResult(0)
    until(lambda: bool(s.get_document.calls))
    assert s.get_document.calls[0][0][1:] == ("N", "alpha", SearchField.BOTH, True)
    c.editQuery("beta", 4)
    s.get_document.calls[0][1].set_exception(SnapshotUnavailable("old preview"))
    until(lambda: c.read_future is None)
    assert not c.preview_html and not c.message_key


def test_unicode_and_literal_markup(qt):
    text = '😀 <img src="https://example.invalid/image"> alpha & beta'
    start = text.index("alpha")
    html = highlighted(text, (TextRange(start, start + 5),))
    assert "<img" not in html and "&lt;img" in html
    document = QTextDocument()
    document.setHtml(html)
    assert document.toPlainText() == text
    assert python_cursor("😀alpha", 4) == 3


@pytest.mark.parametrize("outcome", list(CancelOutcome))
def test_cancel_outcomes_are_explicit(controller, outcome):
    c, s = controller
    start(c)
    s.state = replace(s.state, job=JobRef("job", JobState.RUNNING))
    s.job = JobStatus("job", JobState.RUNNING, JobPhase.EXTRACTING, datetime.now(timezone.utc))
    c.apply_state(s.state)
    s.cancel_synchronization = operation(lambda _: outcome)
    c.action("cancel")
    until(lambda: c.message_key == outcome.value)
    assert c.view["running"] and c.view["status"] == c.tr("old")


def test_clear_and_preferences_failure_then_retry(controller):
    c, s = controller
    start(c)
    s.save_preferences = operation(lambda _: (_ for _ in ()).throw(StorageFailure("disk")))
    c.savePreferences("en", "dark")
    until(lambda: c.message_key == "StorageFailure")
    assert c.preferences == DesktopPreferences()
    s.save_preferences = operation(s.save)
    c.savePreferences("en", "dark")
    until(lambda: c.preferences.language == "en")
    c.action("clear")
    until(lambda: c.state.active_directory is None)
    assert c.preferences == DesktopPreferences() and not c.view["searchable"]


def test_clear_rejected_during_job(controller):
    c, s = controller
    start(c)
    s.state = replace(s.state, job=JobRef("job", JobState.RUNNING))
    s.job = JobStatus("job", JobState.RUNNING, JobPhase.BUILDING, datetime.now(timezone.utc))
    c.apply_state(s.state)
    c.action("clear")
    assert s.state.active_directory == "C:/source"


def test_startup_failure_retries_and_incompatible_state(controller):
    c, s = controller
    c.factory = lambda: (_ for _ in ()).throw(StorageFailure("lock"))
    c.initialize()
    until(lambda: c.message_key == "StorageFailure")
    assert c.session is None
    c.factory = lambda: s
    s.initialize = operation(lambda: (_ for _ in ()).throw(SnapshotUnavailable("incompatible")))
    start(c)
    assert c.view["canManage"] and c.message_key == "SnapshotUnavailable"


def test_close_waits_for_composition(qt):
    entered, release = Event(), Event()
    s = FakeSession()
    def factory():
        entered.set()
        assert release.wait(5)
        return s
    c = DesktopController(factory, lambda *_: None)
    c.initialize()
    until(entered.is_set)
    c.requestClose()
    assert not c.closed
    release.set()
    until(lambda: c.closed)
    assert s.closed


def test_close_waits_for_read_and_event_loop_lives(controller):
    c, s = controller
    start(c)
    c.editQuery("alpha", 5)
    c.search()
    until(lambda: bool(s.search.calls))
    ticks = []
    QTimer.singleShot(10, lambda: ticks.append(True))
    c.requestClose()
    until(lambda: bool(ticks))
    assert not c.closed
    s.search.calls[0][1].set_result(SearchResponse("N", (), 0))
    until(lambda: c.closed)


def test_qml_load_keyboard_search_and_theme(controller, qt):
    c, s = controller
    engine = create_engine(c)
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    try:
        start(c)
        query = window.findChild(QObject, "query")
        query.setProperty("text", "alpha")
        query.setProperty("cursorPosition", 5)
        query.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Tab)
        assert window.activeFocusItem().objectName() == "field"
        QTest.keyClick(window, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        assert window.activeFocusItem().objectName() == "query"
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: bool(s.search.calls))
        s.search.calls[0][1].set_result(SearchResponse("N", (), 0))
        until(lambda: c.response is not None)
        c.savePreferences("en", "dark")
        until(lambda: window.property("dark"))
        assert c.labels["search"] == "Search"
        window.close()
        until(lambda: c.closed)
    finally:
        window.hide()
        engine.deleteLater()


def test_real_backend_search_preview_restart_clear(qt, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "alpha.txt").write_text("😀 alpha beta <literal>", encoding="utf-8")
    storage = tmp_path / "storage"
    c = DesktopController(lambda: compose_desktop(storage), lambda *_: None)
    try:
        start(c)
        c.chooseDirectory(QUrl.fromLocalFile(str(source)).toString())
        until(lambda: c.view["searchable"] and not c.view["running"], timeout=20000)
        c.editQuery("alpha", 5)
        c.search()
        until(lambda: c.response is not None)
        assert c.response.total_matches == 1
        c.selectResult(0)
        until(lambda: bool(c.preview_html))
        assert "&lt;literal&gt;" in c.preview_html
        c.savePreferences("en", "dark")
        until(lambda: c.preferences.language == "en")
    finally:
        c.requestClose()
        until(lambda: c.closed)
    (source / "alpha.txt").unlink()
    source.rmdir()
    c = DesktopController(lambda: compose_desktop(storage), lambda *_: None)
    try:
        start(c)
        until(lambda: not c.view["running"])
        assert c.view["searchable"] and c.preferences.language == "en"
        c.editQuery("alpha", 5)
        c.search()
        until(lambda: c.response is not None)
        assert c.response.total_matches == 1
        c.action("clear")
        until(lambda: c.state.active_directory is None)
        assert c.preferences == DesktopPreferences()
    finally:
        c.requestClose()
        until(lambda: c.closed)


def test_file_opener_missing_and_local_url(tmp_path, monkeypatch):
    from local_document_search_desktop import composition
    with pytest.raises(FileNotFoundError):
        open_document(str(tmp_path), RelativePath("missing.txt"))
    (tmp_path / "hello.txt").write_text("hello")
    captured = []
    monkeypatch.setattr(composition.QDesktopServices, "openUrl", lambda url: captured.append(url) or True)
    open_document(str(tmp_path), RelativePath("hello.txt"))
    assert captured[0].isLocalFile()


def test_frontend_boundaries_and_backend_without_qt_dependency():
    root = Path(__file__).resolve().parents[2]
    project = tomllib.loads((root / "backend/pyproject.toml").read_text())
    assert not any("qt" in dependency.lower() for dependency in project["project"]["dependencies"])
    for file in (root / "frontend/src/local_document_search_desktop").glob("*.py"):
        if file.name == "composition.py":
            continue
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("local_document_search.infrastructure")
                assert not node.module.startswith("local_document_search.interfaces")
