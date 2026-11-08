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
    assert request.limit == 20 and request.allow_prefixes
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
    if change == "options":
        until(lambda: len(s.search.calls) == 2)
        assert c.response is None and c.view["searchDuration"] == -1 and not c.message_key
        s.search.calls[-1][1].set_result(SearchResponse("N", (), 0))
        until(lambda: c.response is not None)
    else:
        until(lambda: c.read_future is None)
        assert c.response is None and c.view["searchDuration"] == -1 and not c.message_key


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
    assert s.search.calls[-1][0][0].offset == 20
    s.search.calls[-1][1].set_result(SearchResponse("N", (), 120))
    until(lambda: c.offset == 20)
    s.state = replace(s.state, active_snapshot_id="N2")
    c.apply_state(s.state)
    until(lambda: len(s.search.calls) == 3)
    assert s.search.calls[-1][0][0].offset == 0
    s.search.calls[-1][1].set_result(SearchResponse("N2", (), 0))
    until(lambda: c.response is not None)
    assert not c.view["canNext"] and not c.view["canPrevious"]


def test_results_show_elapsed_time_in_both_languages(controller, qt):
    import re

    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        c.editQuery("alpha", 5)
        c.search()
        until(lambda: bool(s.search.calls))
        summary = window.findChild(QObject, "resultsSummary")
        assert summary.property("text") == c.labels["searching"]
        QTest.qWait(30)
        s.search.calls[-1][1].set_result(SearchResponse("N", (), 75))
        until(lambda: c.response is not None and c.read_future is None)
        assert c.view["searchDuration"] >= 0.02
        assert re.fullmatch(r"Risultati 75 in [0-9]+,[0-9]{3} secondi",
                            summary.property("text"))
        c.savePreferences("en", "light")
        until(lambda: c.preferences.language == "en")
        assert re.fullmatch(r"Results 75 in [0-9]+\.[0-9]{3} seconds",
                            summary.property("text"))
        c.editQuery("beta", 4)
        assert c.view["searchDuration"] == -1
    finally:
        window.hide()
        engine.deleteLater()


def test_pagination_visibility_and_labels(controller, qt):
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        for total in (0, 19, 20, 21):
            search(c, s, total=total)
            until(lambda: c.response is not None and c.response.total_matches == total
                  and c.read_future is None)
            pagination = window.findChild(QObject, "pagination")
            QTest.qWait(20)
            assert pagination.property("visible") == (total > 20)
            assert c.view["canNext"] == (total > 20)
        summary = window.findChild(QObject, "pageSummary")
        assert summary.property("text") == "Pagina 1 \u00b7 Risultati 1\u201320 / 21"
        c.page(1)
        until(lambda: len(s.search.calls) == 5)
        assert s.search.calls[-1][0][0].offset == 20
        s.search.calls[-1][1].set_result(SearchResponse("N", (), 21))
        until(lambda: c.offset == 20)
        assert summary.property("text") == "Pagina 2 \u00b7 Risultati 21\u201321 / 21"
        assert not c.view["canNext"] and c.view["canPrevious"]
        c.savePreferences("en", "light")
        until(lambda: c.preferences.language == "en")
        assert summary.property("text") == "Page 2 \u00b7 Results 21\u201321 / 21"
    finally:
        window.hide()
        engine.deleteLater()


def test_direct_open_without_preview_and_obsolete_result(controller):
    c, s = controller
    opened = []
    c.opener = lambda *args: opened.append(args)
    start(c)
    search(c, s, items=(result(),), total=1)
    c.openResult(0)
    assert opened == [("C:/source", RelativePath("alpha.txt"))]
    assert not s.get_document.calls
    c.editQuery("beta", 4)
    c.openResult(0)
    assert len(opened) == 1


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
        query.forceActiveFocus()
        for key in (Qt.Key_A, Qt.Key_L, Qt.Key_P, Qt.Key_H, Qt.Key_A):
            QTest.keyClick(window, key)
        assert c.query == "alpha"
        QTest.keyClick(window, Qt.Key_Tab)
        assert window.activeFocusItem().objectName() == "searchButton"
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


def test_settings_entry_is_only_on_home(controller, qt):
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        navigation = window.findChild(QObject, "settingsNavigation")
        assert navigation.property("visible")
        c.navigate("settings")
        assert navigation.property("visible")
        c.navigate("back")
        assert c.view["screen"] == "home"
        search(c, s, total=1)
        assert c.view["screen"] == "results"
        assert not navigation.property("visible")
    finally:
        window.hide()
        engine.deleteLater()


def test_empty_results_query_returns_home_on_enter(controller, qt):
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        c.editQuery("alpha", 5)
        c.search()
        until(lambda: bool(s.search.calls))
        s.search.calls[-1][1].set_result(SearchResponse("N", (), 1))
        until(lambda: c.response is not None)
        query = window.findChild(QObject, "query")
        query.forceActiveFocus()
        query.selectAll()
        QTest.keyClick(window, Qt.Key_Backspace)
        assert c.query == ""
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: c.view["screen"] == "home")
        assert len(s.search.calls) == 1
        assert c.query == ""
    finally:
        window.hide()
        engine.deleteLater()


@pytest.mark.parametrize("focus_name", ["query", "results"])
def test_escape_from_results_returns_home(controller, qt, focus_name):
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, total=1, items=(result(),))
        window.findChild(QObject, focus_name).forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: c.view["screen"] == "home")
        assert c.query == "alpha"
        assert len(s.search.calls) == 1
    finally:
        window.hide()
        engine.deleteLater()


def test_escape_from_results_suggestions_returns_home(controller, qt):
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, total=1)
        c.editQuery("al", 2)
        c.suggest()
        until(lambda: bool(s.suggest.calls))
        s.suggest.calls[-1][1].set_result(SuggestResponse("N", ("alpha",)))
        until(lambda: c.terms == ["alpha"])
        window.findChild(QObject, "suggestions").forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: c.view["screen"] == "home")
        assert c.query == "al"
    finally:
        window.hide()
        engine.deleteLater()


def test_real_backend_search_open_restart_clear(qt, tmp_path):
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
        c.openResult(0)
        assert "&lt;literal&gt;" in c.model.rows[0]["snippetHtml"]
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


def test_navigation_filters_and_directory_reset(controller):
    c, s = controller
    assert c.view["screen"] == "onboarding"
    start(c)
    assert c.view["screen"] == "home"
    search(c, s, items=(result(),), total=1)
    c.navigate("settings")
    assert c.view["screen"] == "settings"
    c.setOptions("content", ["pdf"], "work", "path")
    until(lambda: len(s.search.calls) == 2)
    s.search.calls[-1][1].set_result(SearchResponse("N", (), 0))
    until(lambda: c.response is not None)
    assert c.view["restricted"] and "PDF" in c.view["optionsSummary"]
    c.navigate("back")
    assert c.view["screen"] == "results" and c.query == "alpha"
    s.state = ApplicationState("C:/other", None, False)
    c.apply_state(s.state)
    assert c.view["screen"] == "onboarding" and not c.view["restricted"]
    assert not c.query and c.order.value == "relevance"
    s.state = ApplicationState("C:/other", "NEW", True)
    c.apply_state(s.state)
    assert c.view["screen"] == "home"


def test_open_failure_and_stale_snapshot(controller):
    c, s = controller
    start(c)
    search(c, s, items=(result(),), total=1)
    c.opener = lambda *_: (_ for _ in ()).throw(FileNotFoundError())
    c.openResult(0)
    assert c.message_key == "FileNotFoundError"
    assert not s.get_document.calls
    c.message_key = ""
    c.state = replace(c.state, active_snapshot_id="NEW")
    c.openResult(0)
    assert c.message_key == ""


@pytest.mark.parametrize("outcome", [JobState.FAILED, JobState.CANCELLED])
def test_failed_initial_index_stays_onboarding(controller, outcome):
    c, s = controller
    s.state = ApplicationState("C:/source", None, False)
    start(c)
    c.job = JobStatus("job", outcome, JobPhase.EXTRACTING, datetime.now(timezone.utc))
    assert c.view["screen"] == "onboarding"
    assert c.view["jobProblem"] and c.view["canManage"]
    assert not c.view["searchable"]


def test_qml_all_pages_and_catalogs(controller, qt):
    from PySide6.QtCore import qInstallMessageHandler
    from local_document_search_desktop.i18n import MESSAGES
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, text: messages.append(text))
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        window.setWidth(900)
        window.setHeight(640)
        QTest.qWait(40)
        start(c)
        search(c, s, items=(result(),), total=1)
        for language, theme in (("it", "light"), ("en", "dark")):
            c.savePreferences(language, theme)
            until(lambda: c.preferences.language == language and c.preferences.theme == theme)
            for page in ("settings", "home", "results"):
                c.navigate(page)
                QTest.qWait(50)
                assert not window.grabWindow().isNull()
        assert all(len(values) == 2 and all(values) for values in MESSAGES.values())
        assert not [m for m in messages if any(term in m for term in
                    ("ReferenceError", "TypeError", "Binding loop", "Unable to assign", "Cannot load", "unavailable"))], "\n".join(messages)
    finally:
        window.hide()
        engine.deleteLater()
        QTest.qWait(20)
        qInstallMessageHandler(previous)


def test_returning_session_detection_is_v2_only(tmp_path, monkeypatch):
    from local_document_search_desktop.composition import has_local_session
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert not has_local_session()
    old = tmp_path / "LocalDocumentSearch"
    old.mkdir()
    (old / "control.sqlite3").touch()
    assert not has_local_session()
    new = tmp_path / "LocalDocumentSearchV2"
    new.mkdir()
    (new / "control-v2.sqlite3").touch()
    assert has_local_session()


def test_qml_result_opens_once_by_keyboard_and_click(controller, qt):
    from PySide6.QtCore import QPoint
    c, s = controller
    opened = []
    c.opener = lambda *args: opened.append(args)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, items=(result(),), total=1)
        listing = window.findChild(QObject, "results")
        QTest.qWait(50)
        listing.setProperty("currentIndex", 0)
        listing.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Return)
        assert len(opened) == 1 and not s.get_document.calls
        item = listing.property("currentItem")
        point = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(round(point.x()), round(point.y())))
        assert len(opened) == 2 and not s.get_document.calls
    finally:
        window.hide()
        engine.deleteLater()


def test_reset_keeps_query_and_rejects_empty_formats(controller):
    c, s = controller
    start(c)
    c.editQuery("alpha", 5)
    c.setOptions("filename", ["pdf"], "work", "path")
    c.resetOptions()
    assert c.query == "alpha" and not c.view["restricted"]
    assert c.field is SearchField.BOTH and c.order.value == "relevance"
    c.setOptions("content", [], "", "relevance")
    assert c.message_key == "InvalidInput" and c.field is SearchField.BOTH


def test_theme_text_and_focus_contrast():
    def luminance(color):
        channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
        return sum(a*b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))
    for foregrounds, backgrounds in (
        (("#252826", "#606861", "#315D50"), ("#FAF9F6", "#FFFFFF")),
        (("#EDF1ED", "#B5BFB7", "#ACD5BC"), ("#191D1B", "#242A26")),
    ):
        for foreground in foregrounds:
            for background in backgrounds:
                a, b = sorted((luminance(foreground), luminance(background)))
                assert (b + 0.05) / (a + 0.05) >= 4.5


def test_actual_entrypoint_starts_and_closes(tmp_path):
    import os
    import subprocess
    import sys
    script = tmp_path / "entrypoint_smoke.py"
    script.write_text("""from PySide6.QtCore import QTimer
from local_document_search_desktop import main as entry
original = entry.create_engine

def create(controller):
    engine = original(controller)
    assert engine.rootObjects()
    QTimer.singleShot(250, engine.rootObjects()[0].close)
    return engine

entry.create_engine = create
raise SystemExit(entry.main())
""", encoding="utf-8")
    environment = dict(os.environ, LOCALAPPDATA=str(tmp_path / "profile"), QT_QPA_PLATFORM="offscreen")
    result = subprocess.run([sys.executable, str(script)], env=environment,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "profile" / "LocalDocumentSearchV2").exists()


def test_settings_keyboard_focus_scrolls_into_view(controller, qt):
    c, _ = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        window.setWidth(900)
        window.setHeight(640)
        start(c)
        c.navigate("settings")
        QTest.qWait(40)
        field = window.findChild(QObject, "field")
        theme = window.findChild(QObject, "theme")
        field.forceActiveFocus()
        visited = set()
        for _ in range(24):
            item = window.activeFocusItem()
            visited.add(item.objectName())
            if item == theme:
                break
            QTest.keyClick(window, Qt.Key_Tab)
        assert "language" in visited and window.activeFocusItem() == theme
        location = theme.mapToScene(theme.boundingRect().center())
        assert 60 < location.y() < window.height() - 24
    finally:
        window.hide()
        engine.deleteLater()


def test_result_snippet_uses_compact_text_without_losing_highlights():
    from local_document_search.application.contracts import SearchSnippet
    from local_document_search_desktop.models import result_rows
    item = replace(result(), snippet=SearchSnippet("alpha\n\n<literal>", 0, False, False, (TextRange(0, 5),)))
    rows = result_rows(SearchResponse("N", (item,), 1))
    assert "<br>" not in rows[0]["snippetHtml"]
    assert "<b>alpha</b>" in rows[0]["snippetHtml"] and "&lt;literal&gt;" in rows[0]["snippetHtml"]



def test_suggestion_selection_starts_search(controller, qt):
    c, s = controller
    start(c)
    c.editQuery("al", 2)
    c.suggest()
    until(lambda: bool(s.suggest.calls))
    s.suggest.calls[-1][1].set_result(SuggestResponse("N", ("alpha",)))
    until(lambda: c.terms == ["alpha"])
    c.acceptSuggestionAndSearch(0)
    until(lambda: bool(s.search.calls))
    assert c.query == "alpha" and c.view["screen"] == "results"
    assert s.search.calls[-1][0][0].query == "alpha"


def test_search_icon_click_runs_from_home_and_results(controller, qt):
    from PySide6.QtCore import QPoint
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        for text in ("alpha", "beta"):
            c.editQuery(text, len(text))
            QTest.qWait(40)
            button = window.findChild(QObject, "searchButton")
            point = button.mapToScene(button.boundingRect().center())
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                             QPoint(round(point.x()), round(point.y())))
            until(lambda: len(s.search.calls) == (1 if text == "alpha" else 2))
            assert c.view["screen"] == "results"
            assert s.search.calls[-1][0][0].query == text
            s.search.calls[-1][1].set_result(SearchResponse("N", (), 0))
            until(lambda: c.read_future is None)
    finally:
        window.hide()
        engine.deleteLater()


def test_qml_suggestion_click_searches_and_opens_results(controller, qt):
    from PySide6.QtCore import QPoint
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        c.editQuery("al", 2)
        c.suggest()
        until(lambda: bool(s.suggest.calls))
        s.suggest.calls[-1][1].set_result(SuggestResponse("N", ("alpha",)))
        until(lambda: c.terms == ["alpha"])
        suggestions = window.findChild(QObject, "suggestions")
        QTest.qWait(40)
        item = suggestions.property("currentItem")
        if item is None:
            suggestions.setProperty("currentIndex", 0)
            item = suggestions.property("currentItem")
        point = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                         QPoint(round(point.x()), round(point.y())))
        until(lambda: bool(s.search.calls))
        assert c.query == "alpha" and c.view["screen"] == "results"
    finally:
        window.hide()
        engine.deleteLater()


def test_settings_binary_choices_keyboard_and_reset(controller, qt):
    from PySide6.QtCore import QPointF
    c, _ = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        c.navigate("settings")
        QTest.qWait(40)
        for name, attribute, expected in (("language", "language", "en"),
                                          ("theme", "theme", "dark")):
            control = window.findChild(QObject, name)
            control.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Right)
            until(lambda: getattr(c.preferences, attribute) == expected)
            assert control.property("currentIndex") == 1
            QTest.keyClick(window, Qt.Key_Space)
            until(lambda: getattr(c.preferences, attribute) != expected)
            assert control.property("currentIndex") == 0
        order = window.findChild(QObject, "order")
        order.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        assert c.order.value == "path"
        c.resetOptions()
        QTest.qWait(20)
        assert order.property("currentIndex") == 0
        assert not order.property("checked")
        QTest.keyClick(window, Qt.Key_Space)
        assert c.order.value == "path"
        # Clicking an already selected segment must not invert the choice.
        for fraction, expected in ((0.75, "path"), (0.25, "relevance"), (0.25, "relevance")):
            point = order.mapToScene(QPointF(order.width() * fraction, order.height() / 2))
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point.toPoint())
            assert c.order.value == expected
    finally:
        window.hide()
        engine.deleteLater()
