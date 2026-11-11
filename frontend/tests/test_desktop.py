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
from PySide6.QtCore import QObject, QPoint, QPointF, QUrl, Qt, QTimer
from PySide6.QtGui import QColor, QTextDocument
from PySide6.QtTest import QTest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from local_document_search.application.contracts import (
    ApplicationState, CancelOutcome, DocumentDetails, JobDiagnostic, JobPhase, JobRef,
    JobReport, JobState, JobStatus, SearchResponse, SearchResult, SuggestResponse, TextRange,
    SpellingResponse, SpellingReplacement, TextNavigationTarget,
)
from local_document_search.application.text_view import PrepareTextView, TextViewDocument
from local_document_search.application.errors import SnapshotUnavailable, StorageFailure
from local_document_search.application.preferences import DesktopPreferences
from local_document_search.domain.documents import (
    DocumentId, DocumentFormat, RelativePath, DocumentMetadata, FileFingerprint,
)
from local_document_search.domain.queries import SearchField
from local_document_search_desktop.composition import compose_desktop, open_document, open_document_folder
from local_document_search_desktop.controller import DesktopController, extract_format_filters
from local_document_search_desktop.viewer import _has_searchable_text
from local_document_search_desktop.text_reader import display_text, find_literal, qt_offset
from local_document_search_desktop.main import create_engine
from local_document_search_desktop.models import highlighted, python_cursor
from local_document_search.infrastructure.text_view_source import LocalTextViewSource
from local_document_search.interfaces.composition import compose_cli
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
        self.suggest_spelling = None
        self.prepare_text_view = operation(lambda request: TextViewDocument(
            "alpha first\nalpha second", False, "lf", (TextRange(0, 5),), "ready"))
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
    if session.suggest_spelling is not None:
        session.suggest_spelling.release()
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
                        DocumentFormat.TXT, frozenset({SearchField.CONTENT}),
                        text_target=TextNavigationTarget(10, 1, TextRange(0, 5)))


def test_pdf_viewer_navigates_to_result_page(controller, qt, tmp_path):
    c, s = controller
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=200, height=200)
    writer.write(tmp_path / "sample.pdf")
    s.state = ApplicationState(str(tmp_path), "N", True)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        pdf_result = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                                  DocumentFormat.PDF, frozenset({SearchField.CONTENT}), pdf_target_page=2)
        search(c, s, items=(pdf_result,), total=1)
        c.openResult(0)
        assert c.view["screen"] == "viewer"
        until(lambda: window.findChild(QObject, "pdfViewer") is not None)
        viewer = window.findChild(QObject, "pdfViewer")
        until(lambda: viewer.property("currentPage") == 2)
        c.savePreferences("en", "dark")
        until(lambda: c.view["language"] == "en")
        assert window.findChild(QObject, "openPdfExternally").property("text") == "Open in default app"
        c.navigate("back")
        assert c.view["screen"] == "results"
        assert c.view["viewerSource"] == ""
        QTest.qWait(30)
        c.response = SearchResponse("N", (replace(pdf_result, pdf_target_page=9),), 1)
        c.openResult(0)
        until(lambda: window.findChild(QObject, "pdfViewer") is not None)
        viewer = window.findChild(QObject, "pdfViewer")
        until(lambda: viewer.property("currentPage") == 0)
        warning = window.findChild(QObject, "pdfWarning")
        until(lambda: warning is not None and warning.property("visible"))
        c.navigate("back")
        QTest.qWait(30)
        missing = replace(pdf_result, filename="missing.pdf", relative_path=RelativePath("missing.pdf"))
        c.response = SearchResponse("N", (missing,), 1)
        c.openResult(0)
        assert c.view["screen"] == "viewer"
        warning = window.findChild(QObject, "pdfWarning")
        until(lambda: warning is not None and warning.property("visible"))
    finally:
        if c.screen == "viewer":
            c.navigate("back")
            QTest.qWait(30)
        engine.deleteLater()


def _text_pdf(path, page_texts):
    writer = PdfWriter()
    for value in page_texts:
        page = writer.add_blank_page(width=300, height=400)
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 14 Tf 40 300 Td ({value}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                 NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"):
            DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    writer.write(path)


def test_pdf_find_uses_selected_search_query_and_text_probe(controller, qt, tmp_path):
    c, s = controller
    _text_pdf(tmp_path / "sample.pdf", ["needle one", "other page", "needle two"])
    s.state = ApplicationState(str(tmp_path), "N", True)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        item = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                            DocumentFormat.PDF, frozenset({SearchField.CONTENT}), pdf_target_page=1)
        search(c, s, text="needle", items=(item,), total=1)
        c.query = "changed editor"
        c.openResult(0)
        until(lambda: c.view["viewerTextStatus"] == "available")
        viewer = window.findChild(QObject, "pdfViewer")
        until(lambda: viewer is not None and viewer.property("currentPage") == 1)
        assert viewer.property("searchString") == ""
        assert viewer.property("viewportContentWidth") <= viewer.property("viewportWidth") + 2
        assert viewer.property("viewportLeft") - 12 <= viewer.property("viewportContentX") <= viewer.property("viewportRight") + 12
        zoom = viewer.property("renderScale")
        button = window.findChild(QObject, "pdfZoomIn")
        assert button.property("width") == 32 and button.property("height") == 32
        button.click()
        until(lambda: viewer.property("renderScale") > zoom)
        zoom_choice = window.findChild(QObject, "pdfZoomChoice")
        zoom_choice.setProperty("currentIndex", 3)
        zoom_choice.activated.emit(3)
        until(lambda: viewer.property("renderScale") > zoom * 2)
        QTest.keyClick(window, Qt.Key_F, Qt.ControlModifier)
        field = window.findChild(QObject, "pdfFindField")
        until(lambda: field is not None and field.property("visible"))
        assert field.property("text") == "needle"
        assert viewer.property("searchString") == ""
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: viewer.property("searchCount") == 2)
        until(lambda: viewer.property("currentPage") == 0)
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: viewer.property("currentPage") == 2)
        QTest.keyClick(window, Qt.Key_Return, Qt.ShiftModifier)
        until(lambda: viewer.property("currentPage") == 0)
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: not field.property("visible"))
        assert c.view["screen"] == "viewer" and viewer.property("searchString") == ""
        QTest.keyClick(window, Qt.Key_F, Qt.ControlModifier)
        until(lambda: field.property("visible"))
        field.setProperty("text", "absent")
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: viewer.property("searchString") == "absent")
        until(lambda: viewer.property("searchCount") == 0)
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: not field.property("visible"))
        QTest.keyClick(window, Qt.Key_F, Qt.ControlModifier)
        until(lambda: field.property("visible"))
        assert field.property("text") == "absent"
        window.findChild(QObject, "pdfHighlightAll").forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: not field.property("visible"))
        assert c.view["screen"] == "viewer"
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: c.view["screen"] == "results")
        until(lambda: window.findChild(QObject, "pdfFindBar") is None)
    finally:
        if c.screen == "viewer":
            c.navigate("back")
        engine.deleteLater()


def test_pdf_find_disabled_for_image_only_pdf(controller, qt, tmp_path):
    c, s = controller
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    writer.write(tmp_path / "sample.pdf")
    s.state = ApplicationState(str(tmp_path), "N", True)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        item = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                            DocumentFormat.PDF, frozenset({SearchField.FILENAME}), pdf_target_page=0)
        search(c, s, items=(item,), total=1)
        c.openResult(0)
        until(lambda: c.view["viewerTextStatus"] == "unavailable")
        assert not window.findChild(QObject, "pdfFindButton").property("enabled")
    finally:
        if c.screen == "viewer":
            c.navigate("back")
        engine.deleteLater()


def test_pdf_viewer_folder_action_uses_original_directory(controller, qt, tmp_path, monkeypatch):
    c, s = controller
    source = tmp_path / "nested"
    source.mkdir()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    writer.write(source / "sample.pdf")
    s.state = ApplicationState(str(tmp_path), "N", True)
    opened = []
    monkeypatch.setattr("local_document_search_desktop.composition.QDesktopServices.openUrl",
                        lambda url: opened.append(url.toLocalFile()) or True)
    engine = create_engine(c)
    try:
        start(c)
        item = SearchResult(DocumentId(1), "sample.pdf", RelativePath("nested/sample.pdf"),
                            DocumentFormat.PDF, frozenset({SearchField.FILENAME}), pdf_target_page=0)
        search(c, s, items=(item,), total=1)
        c.openResult(0)
        c.openViewerFolder()
        assert list(map(Path, opened)) == [source]
        c.openViewerExternally()
        # The default opener is injectable; the folder action is separate.
        assert list(map(Path, opened)) == [source]
    finally:
        if c.screen == "viewer":
            c.navigate("back")
        engine.deleteLater()


def test_open_document_folder_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        open_document_folder(str(tmp_path), RelativePath("missing/missing.pdf"))


def test_pdf_text_probe_scans_past_empty_pages(tmp_path):
    mixed = tmp_path / "mixed.pdf"
    _text_pdf(mixed, ["", "", "needle"])
    assert _has_searchable_text(mixed)
    image_only = tmp_path / "image-only.pdf"
    _text_pdf(image_only, ["", ""])
    assert not _has_searchable_text(image_only)


def test_pdf_toolbar_page_zoom_rotation_and_highlights(controller, qt, tmp_path):
    c, s = controller
    _text_pdf(tmp_path / "sample.pdf", ["needle one", "needle two", "needle three"])
    s.state = ApplicationState(str(tmp_path), "N", True)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        item = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                            DocumentFormat.PDF, frozenset({SearchField.CONTENT}), pdf_target_page=1)
        search(c, s, text="needle", items=(item,), total=1)
        c.openResult(0)
        until(lambda: c.view["viewerTextStatus"] == "available")
        viewer = window.findChild(QObject, "pdfViewer")
        until(lambda: viewer is not None and viewer.property("currentPage") == 1)
        assert viewer.property("renderScale") == 1
        window.setWidth(900)
        until(lambda: window.findChild(QObject, "pdfToolbar").property("width") == window.width())
        assert window.findChild(QObject, "pdfToolbar").property("width") == window.width()
        folder = window.findChild(QObject, "openPdfFolder")
        assert folder.mapToScene(QPointF(folder.width(), 0)).x() <= window.width()
        table = window.findChild(QObject, "pdfTableView")
        assert table.property("topMargin") == 50
        assert window.findChild(QObject, "pdfPreviousPage").property("enabled")
        window.findChild(QObject, "pdfNextPage").click()
        until(lambda: viewer.property("currentPage") == 2)
        number = window.findChild(QObject, "pdfPageNumber")
        assert number.property("text") == "3"
        number.setProperty("text", "99")
        number.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Return)
        assert number.property("invalid") and viewer.property("currentPage") == 2
        number.setProperty("text", "1")
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: viewer.property("currentPage") == 0)
        assert not number.property("invalid")
        window.findChild(QObject, "pdfRotate").click()
        until(lambda: viewer.property("pageRotation") == 90)
        choice = window.findChild(QObject, "pdfZoomChoice")
        choice.setProperty("currentIndex", 2)
        choice.activated.emit(2)
        until(lambda: viewer.property("renderScale") > 1)
        assert window.findChild(QObject, "pdfViewerPage").property("zoomMode") == "page"
        for index, percent in enumerate((50, 75, 100, 125, 150, 200, 300, 400), start=4):
            choice.setProperty("currentIndex", index)
            choice.activated.emit(index)
            until(lambda: abs(viewer.property("renderScale") - percent / 100) < 0.001)
            assert choice.property("displayText") == f"{percent}%"
        choice.setProperty("currentIndex", 1)
        choice.activated.emit(1)
        until(lambda: abs(viewer.property("renderScale") - 1) < 0.001)
        QTest.keyClick(window, Qt.Key_F, Qt.ControlModifier)
        field = window.findChild(QObject, "pdfFindField")
        until(lambda: field is not None and field.property("visible"))
        assert table.property("bottomMargin") == 52
        find_bar = window.findChild(QObject, "pdfFindBar")
        assert find_bar.property("height") == 52
        assert window.height() - 100 <= find_bar.mapToScene(QPointF(0, 0)).y() + 52 <= window.height()
        assert find_bar.property("z") > window.findChild(QObject, "pdfToolbar").property("z")
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: viewer.property("searchCount") == 3)
        assert not viewer.property("highlightAll")
        highlight = window.findChild(QObject, "pdfHighlightAll")
        highlight.click()
        assert viewer.property("highlightAll")
    finally:
        if c.screen == "viewer":
            c.navigate("back")
        engine.deleteLater()


def test_pdf_mixed_page_widths_keep_narrow_page_centered(controller, qt, tmp_path):
    c, s = controller
    writer = PdfWriter()
    writer.add_blank_page(width=1800, height=600)
    writer.add_blank_page(width=300, height=600)
    writer.write(tmp_path / "sample.pdf")
    s.state = ApplicationState(str(tmp_path), "N", True)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        item = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                            DocumentFormat.PDF, frozenset({SearchField.FILENAME}), pdf_target_page=1)
        search(c, s, items=(item,), total=1)
        c.openResult(0)
        viewer = window.findChild(QObject, "pdfViewer")
        until(lambda: viewer is not None and viewer.property("currentPage") == 1)
        until(lambda: abs(viewer.property("viewportContentX") -
                          (viewer.property("viewportContentWidth") - viewer.property("viewportWidth")) / 2) < 2)
        assert viewer.property("currentPageWidth") < viewer.property("viewportWidth")
        window.findChild(QObject, "pdfPreviousPage").click()
        until(lambda: viewer.property("currentPage") == 0)
        window.findChild(QObject, "pdfZoomIn").click()
        until(lambda: viewer.property("currentPageWidth") > viewer.property("viewportWidth"))
    finally:
        if c.screen == "viewer":
            c.navigate("back")
        engine.deleteLater()


def test_pdf_overlay_stays_above_scrolling_and_zoom_popup_uses_theme(controller, qt, tmp_path):
    c, s = controller
    writer = PdfWriter()
    for _ in range(16):
        writer.add_blank_page(width=400, height=700)
    writer.write(tmp_path / "sample.pdf")
    s.state = ApplicationState(str(tmp_path), "N", True)
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        item = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                            DocumentFormat.PDF, frozenset({SearchField.FILENAME}), pdf_target_page=0)
        search(c, s, items=(item,), total=1)
        c.openResult(0)
        viewer = window.findChild(QObject, "pdfViewer")
        until(lambda: viewer is not None and viewer.property("currentPage") == 0)
        toolbar = window.findChild(QObject, "pdfToolbar")
        table = window.findChild(QObject, "pdfTableView")
        assert toolbar.property("z") > viewer.property("z")
        assert toolbar.property("y") == 0
        table.setProperty("contentY", 1000)
        until(lambda: table.property("contentY") > 500)
        assert toolbar.property("y") == 0 and toolbar.property("visible")
        assert window.findChild(QObject, "pdfZoomIn").property("visible")
        choice = window.findChild(QObject, "pdfZoomChoice")
        for language, mode, surface in (("it", "light", "#ffffff"), ("en", "dark", "#242a26")):
            c.savePreferences(language, mode)
            until(lambda: c.view["theme"] == mode)
            center = choice.mapToScene(QPointF(choice.width() / 2, choice.height() / 2))
            QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(round(center.x()), round(center.y())))
            popup = window.findChild(QObject, "pdfZoomPopup")
            until(lambda: popup.property("visible"))
            assert popup.property("background").property("color") == QColor(surface)
            QTest.keyClick(window, Qt.Key_Escape)
        c.savePreferences("it", "light")
        QTest.keyClick(window, Qt.Key_F, Qt.ControlModifier)
        # Image-only PDFs keep find disabled, including the keyboard shortcut.
        assert not window.findChild(QObject, "pdfFindBar").property("visible")
    finally:
        if c.screen == "viewer":
            c.navigate("back")
        engine.deleteLater()


def test_snapshot_change_keeps_open_pdf_but_drops_old_selection(controller):
    c, s = controller
    start(c)
    c.screen = "viewer"
    c.viewer.source = "file:///sample.pdf"
    c.viewer.relative_path = RelativePath("sample.pdf")
    c.selected = SearchResult(DocumentId(1), "sample.pdf", RelativePath("sample.pdf"),
                              DocumentFormat.PDF, frozenset({SearchField.CONTENT}), pdf_target_page=1)
    c.apply_state(ApplicationState("C:/source", "new", True))
    assert c.view["screen"] == "viewer"
    assert c.view["viewerSource"] == "file:///sample.pdf"
    assert c.selected is None
    c.navigate("back")
    assert c.view["screen"] == "results"


def test_spelling_proposal_requires_selection_and_discards_stale(controller):
    c, s = controller
    s.suggest_spelling = Requests()
    start(c)
    search(c, s, "famos", total=1, items=(result(),))
    until(lambda: len(s.suggest_spelling.calls) == 1)
    request = s.suggest_spelling.calls[0][0][0]
    assert request.query == "famos" and request.snapshot_id == "N"
    s.suggest_spelling.calls[0][1].set_result(SpellingResponse(
        "N", "famous", (SpellingReplacement(0, 5, "famos", "famous", 1, 0.4),)))
    until(lambda: c.view["spellingProposal"] == "famous")
    assert c.query == "famos" and c.response.total_matches == 1
    c.acceptSpelling()
    assert c.query == "famous" and c.spelling is None
    until(lambda: len(s.search.calls) == 2)
    c.editQuery("other", 5)
    s.search.calls[-1][1].set_result(SearchResponse("N", (), 0))
    assert c.view["spellingProposal"] == ""
    s.suggest_spelling.release()


def test_spelling_survives_pagination_but_not_query_change(controller):
    c, s = controller
    s.suggest_spelling = Requests()
    start(c)
    search(c, s, "famos", total=40)
    until(lambda: len(s.suggest_spelling.calls) == 1)
    c.page(1)
    s.suggest_spelling.calls[0][1].set_result(SpellingResponse(
        "N", "famous", (SpellingReplacement(0, 5, "famos", "famous", 1, 0.4),)))
    until(lambda: len(s.search.calls) == 2)
    s.search.calls[-1][1].set_result(SearchResponse("N", (), 40))
    until(lambda: c.offset == 20)
    until(lambda: c.view["spellingProposal"] == "famous")
    assert len(s.suggest_spelling.calls) == 1
    c.editQuery("other", 5)
    assert c.view["spellingProposal"] == ""
    s.suggest_spelling.release()


def test_qml_spelling_button_keyboard(controller, qt):
    c, s = controller
    s.suggest_spelling = Requests()
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, "famos", total=0)
        until(lambda: len(s.suggest_spelling.calls) == 1)
        s.suggest_spelling.calls[0][1].set_result(SpellingResponse(
            "N", "famous", (SpellingReplacement(0, 5, "famos", "famous", 1, 0.4),)))
        until(lambda: c.view["spellingProposal"] == "famous")
        button = window.findChild(QObject, "acceptSpelling")
        assert button is not None and button.property("visible")
        button.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        until(lambda: len(s.search.calls) == 2)
        assert s.search.calls[-1][0][0].query == "famous"
    finally:
        s.suggest_spelling.release()
        window.hide()
        engine.deleteLater()


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
    assert request.limit == 20 and request.allow_wildcards
    assert request.order.value == "relevance"


@pytest.mark.parametrize("query,cursor,expected", [
    ('"al', 3, None), ('al*', 2, None), ('alpha be', 8, (6, 8, 'be')),
    ('alpha beta', 8, (6, 10, 'be')), ('a', 1, None), ('foo-bar', 7, None),
    ('alpha *ing beta', 10, (6, 10, 'ing')), ('*ing', 3, (0, 4, 'in')),
    ('x*ing', 5, None), ('**ing', 5, None), ('*ing*', 4, None),
])
def test_suggestion_token_boundaries(controller, query, cursor, expected):
    c, _ = controller
    c.query, c.cursor = query, cursor
    span = c.suggestion_span()
    assert (None if span is None else span[:3]) == expected


def test_suffix_suggestion_replaces_whole_clause(controller):
    from local_document_search.application.contracts import SuggestMode

    c, s = controller
    start(c)
    c.editQuery("alpha *ing beta", 10)
    c.suggest()
    until(lambda: bool(s.suggest.calls))
    request = s.suggest.calls[-1][0][0]
    assert request.text == "ing" and request.mode is SuggestMode.SUFFIX
    assert not s.search.calls
    s.suggest.calls[-1][1].set_result(SuggestResponse("N", ("walking",)))
    until(lambda: c.terms == ["walking"])
    c.acceptSuggestionAndSearch(0)
    assert c.query == "alpha walking beta"
    until(lambda: bool(s.search.calls))
    assert s.search.calls[-1][0][0].allow_wildcards


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


@pytest.mark.parametrize(("source", "query", "formats"), [
    ("contratto .PDF", "contratto", {DocumentFormat.PDF}),
    (".txt alpha .MD .txt", "alpha", {DocumentFormat.TXT, DocumentFormat.MARKDOWN}),
    ("alpha .pdf beta", "alpha beta", {DocumentFormat.PDF}),
    ('".pdf" relazione.pdf .doc', '".pdf" relazione.pdf .doc', set()),
    ('"testo .pdf" .txt', '"testo .pdf"', {DocumentFormat.TXT}),
])
def test_format_filter_tokens(source, query, formats):
    assert extract_format_filters(source) == (query, frozenset(formats))


def test_query_format_filter_uses_existing_search_options(controller):
    c, s = controller
    start(c)
    c.setOptions("content", ["txt"], "work", "path")
    c.editQuery("contratto .PDF", len("contratto .PDF"))
    c.search()
    until(lambda: len(s.search.calls) == 1)
    request = s.search.calls[0][0][0]
    assert request.query == c.query == "contratto"
    assert request.formats == {DocumentFormat.PDF}
    assert request.field == SearchField.CONTENT and request.folder == "work"
    assert request.order.value == "path"
    assert c.view["screen"] == "results" and "PDF" in c.view["optionsSummary"]
    c.resetOptions()
    assert c.query == "contratto" and c.formats == frozenset(DocumentFormat)


def test_format_only_prepares_filter_without_search(controller):
    c, s = controller
    start(c)
    c.editQuery(".pdf", 4)
    c.search()
    assert c.query == "" and c.screen == "home"
    assert c.formats == {DocumentFormat.PDF} and not s.search.calls


def test_format_filter_discards_old_search_response(controller):
    c, s = controller
    start(c)
    c.editQuery("alpha", 5)
    c.search()
    until(lambda: len(s.search.calls) == 1)
    c.editQuery("beta .md", 8)
    c.search()
    s.search.calls[0][1].set_result(SearchResponse("N", (), 7))
    until(lambda: len(s.search.calls) == 2)
    assert c.response is None
    assert s.search.calls[1][0][0].query == "beta"
    assert s.search.calls[1][0][0].formats == {DocumentFormat.MARKDOWN}


def test_filter_summary_icon_is_accessible_and_resets(controller, qt):
    c, _ = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        c.setOptions("both", ["pdf"], "", "relevance")
        icon = window.findChild(QObject, "clearFilters")
        assert icon is not None and icon.property("visible")
        from PySide6.QtGui import QAccessible
        assert QAccessible.queryAccessibleInterface(icon).text(QAccessible.Name) == c.labels["resetFilters"]
        assert window.findChild(QObject, "settingsNavigation") is not None
        point = icon.mapToScene(icon.boundingRect().center())
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                         QPoint(round(point.x()), round(point.y())))
        assert not c.view["restricted"]
        c.setOptions("both", ["md"], "", "relevance")
        icon.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        assert not c.view["restricted"]
        c.editQuery("alpha .pdf", 10)
        c.search()
        until(lambda: c.screen == "results")
        assert window.findChild(QObject, "clearFilters") is not None
        assert not window.findChild(QObject, "settingsNavigation").property("visible")
    finally:
        window.hide()
        engine.deleteLater()


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


def test_internal_text_open_without_preview_and_obsolete_result(controller):
    c, s = controller
    opened = []
    c.opener = lambda *args: opened.append(args)
    start(c)
    search(c, s, items=(result(),), total=1)
    c.openResult(0)
    assert opened == [] and c.view["screen"] == "viewer"
    until(lambda: c.text_reader.state in ("populating", "ready"))
    assert not s.get_document.calls
    c.editQuery("beta", 4)
    c.openResult(0)
    assert opened == []


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
    s.prepare_text_view = operation(lambda _: (_ for _ in ()).throw(FileNotFoundError()))
    c.openResult(0)
    until(lambda: c.text_reader.state == "error")
    assert c.text_reader.errorKey == "FileNotFoundError"
    assert not s.get_document.calls
    s.prepare_text_view = operation(lambda _: TextViewDocument("alpha", False, "none", (), "filename"))
    c.retryTextViewer()
    until(lambda: c.text_reader.state == "populating")
    c.navigate("back")
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


def test_returning_session_detection_ignores_legacy_locations(tmp_path, monkeypatch):
    from local_document_search_desktop.composition import has_local_session
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert not has_local_session()
    old = tmp_path / "LocalDocumentSearch"
    old.mkdir()
    (old / "control.sqlite3").touch()
    assert not has_local_session()
    previous = tmp_path / "LocalDocumentSearchV2"
    previous.mkdir()
    (previous / "control-v2.sqlite3").touch()
    assert not has_local_session()
    new = old / "Data"
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
        until(lambda: c.view["screen"] == "viewer")
        until(lambda: window.findChild(QObject, "textReaderArea") is not None)
        assert len(opened) == 0 and not s.get_document.calls
        c.navigate("back")
        until(lambda: window.findChild(QObject, "results") is not None)
        listing = window.findChild(QObject, "results")
        item = listing.property("currentItem")
        point = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(round(point.x()), round(point.y())))
        until(lambda: c.view["screen"] == "viewer")
        assert len(opened) == 0 and not s.get_document.calls
    finally:
        window.hide()
        engine.deleteLater()


def test_text_reader_qml_jump_find_and_read_only(controller, qt):
    c, s = controller
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, items=(result(),), total=1)
        c.openResult(0)
        until(lambda: c.text_reader.ready)
        area = window.findChild(QObject, "textReaderArea")
        assert area is not None and area.property("readOnly")
        assert area.property("text") == "alpha first\nalpha second"
        QTest.keyClick(window, Qt.Key_Z)
        assert area.property("text") == "alpha first\nalpha second"
        area.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Tab)
        assert not area.property("activeFocus")
        assert c.text_reader.marker == "snapshot"
        until(lambda: len(c.text_reader.visibleLines(0, 500)) == 2)
        assert [row["number"] for row in c.text_reader.visibleLines(0, 500)] == [1, 2]
        wrap_button = window.findChild(QObject, "textWrapButton")
        assert wrap_button.property("checked")
        wrap_button.click()
        assert not wrap_button.property("checked")
        wrap_button.click()
        assert wrap_button.property("checked")
        QTest.keyClick(window, Qt.Key_F, Qt.ControlModifier)
        field = window.findChild(QObject, "textFindField")
        until(lambda: field is not None and field.property("visible"))
        field.setProperty("text", "alpha")
        QTest.keyClick(window, Qt.Key_Return)
        until(lambda: c.text_reader.matchCount == 2)
        assert c.text_reader.marker == "manual"
        assert field.property("activeFocus")
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: not field.property("visible"))
        assert c.view["screen"] == "viewer"
        QTest.keyClick(window, Qt.Key_Escape)
        until(lambda: c.view["screen"] == "results")
        until(lambda: window.findChild(QObject, "results") is not None)
        assert window.findChild(QObject, "results").property("activeFocus")
    finally:
        window.hide()
        engine.deleteLater()


def test_text_reader_coordinates_and_literal_case_rules(qt):
    source = "😀 alpha\r\nCAFÉ cafe\u0301 &amp;"
    assert display_text(source) == "😀 alpha\nCAFÉ cafe\u0301 &amp;"
    assert qt_offset(source, source.index("CAFÉ")) == len("😀 alpha\n".encode("utf-16-le")) // 2
    matches = find_literal(display_text(source), "café")
    assert len(matches) == 2
    assert find_literal(display_text(source), "&amp;")
    assert len(find_literal(display_text(source), "cafe")) == 2


def test_markdown_result_reaches_original_source_in_qml(controller, qt, tmp_path):
    c, s = controller
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("front **alpha** tail", encoding="utf-8")
    backend = compose_cli(str(root))
    backend.build.execute(str(root))
    from local_document_search.application.contracts import SearchRequest
    response = backend.search.execute(SearchRequest("alpha"))
    s.state = ApplicationState(str(root), response.snapshot_id, True)
    s.prepare_text_view = PrepareTextView(LocalTextViewSource())
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, items=response.results, total=1)
        c.openResult(0)
        until(lambda: c.text_reader.ready)
        area = window.findChild(QObject, "textReaderArea")
        until(lambda: area is not None and area.property("selectedText") == "alpha")
        assert area.property("text") == "front **alpha** tail"
        assert c.text_reader.marker == "snapshot"
    finally:
        window.hide()
        engine.deleteLater()


def test_text_reader_changed_file_opens_without_snapshot_jump(controller, qt):
    c, s = controller
    s.prepare_text_view = operation(lambda _: TextViewDocument("current alpha", False, "none", (), "changed"))
    engine = create_engine(c)
    window = engine.rootObjects()[0]
    try:
        start(c)
        search(c, s, items=(result(),), total=1)
        c.openResult(0)
        until(lambda: c.text_reader.ready)
        area = window.findChild(QObject, "textReaderArea")
        assert area.property("text") == "current alpha"
        assert c.text_reader.marker == ""
        warning = window.findChild(QObject, "textWarning")
        assert warning.property("visible") and "cambiato" in warning.property("text")
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
    assert not (tmp_path / "profile" / "LocalDocumentSearch" / "Data").exists()


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


def test_suggestion_selection_applies_format_token(controller):
    c, s = controller
    start(c)
    c.editQuery("al .pdf", 2)
    c.suggest()
    until(lambda: bool(s.suggest.calls))
    s.suggest.calls[-1][1].set_result(SuggestResponse("N", ("alpha",)))
    until(lambda: c.terms == ["alpha"])
    c.acceptSuggestionAndSearch(0)
    until(lambda: bool(s.search.calls))
    assert c.query == s.search.calls[-1][0][0].query == "alpha"
    assert s.search.calls[-1][0][0].formats == {DocumentFormat.PDF}


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
