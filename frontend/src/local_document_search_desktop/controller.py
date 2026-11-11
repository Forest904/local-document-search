"""Coordinamento desktop: contratti applicativi nei worker, Qt nel thread GUI."""
from concurrent.futures import ThreadPoolExecutor
from html import escape
import re
import time

from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer, QUrl

from local_document_search.application.contracts import (
    SearchRequest, SearchField, SearchOrder, SuggestMode, SuggestRequest, SpellingRequest, JobState, InvalidInput,
)
from local_document_search.application.errors import SnapshotUnavailable
from local_document_search.application.preferences import DesktopPreferences
from local_document_search.domain.documents import DocumentFormat

from .i18n import catalog, translate
from .models import ResultsModel, python_cursor, result_rows
from .viewer import PdfTextProbe, PdfViewerState
from .text_reader import TextReaderBridge


PAGE_SIZE = 20


def extract_format_filters(query):
    """Consume standalone format tokens outside quoted phrases."""
    tokens = []
    token = []
    quoted = False
    started_quoted = False
    for char in query:
        if char.isspace() and not quoted:
            if token:
                tokens.append(("".join(token), started_quoted))
                token = []
                started_quoted = False
        else:
            if char == '"':
                quoted = not quoted
                started_quoted = True
            token.append(char)
    if token:
        tokens.append(("".join(token), started_quoted))
    formats = set()
    remaining = []
    for value, has_quote in tokens:
        extension = value.lower()
        if not has_quote and extension in (".txt", ".md", ".pdf"):
            formats.add(DocumentFormat(extension[1:]))
        else:
            remaining.append(value)
    return " ".join(remaining), frozenset(formats)


class DesktopController(QObject):
    changed = Signal()
    preferencesChanged = Signal()
    closeReady = Signal()
    queryReplacement = Signal(str, int)

    def __init__(self, factory, opener, parent=None):
        super().__init__(parent)
        self.factory, self.opener = factory, opener
        self.session = self.state = self.job = self.response = self.selected = None
        self.preferences = DesktopPreferences()
        self.model = ResultsModel(self)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="desktop-control")
        self.reader = ThreadPoolExecutor(max_workers=1, thread_name_prefix="desktop-read")
        self.control_future = self.read_future = None
        self.queued_control = None
        self.queued_reads = {}
        self.generation = self.suggest_generation = self.spelling_generation = 0
        self.query = ""
        self.screen = "home"
        self.viewer = PdfViewerState()
        self.viewer_probe = PdfTextProbe(self)
        self.viewer_probe.changed.connect(self.changed)
        self.text_reader = TextReaderBridge(self)
        self.viewer_kind = "pdf"
        self.viewer_result = self.viewer_root = self.viewer_snapshot = None
        self.response_query = ""
        self.results_scroll = 0.0
        self.results_index = -1
        self.focus_result_on_return = False
        self.return_screen = "home"
        self.cursor = 0
        self.field = SearchField.BOTH
        self.formats = None
        self.folder = None
        self.order = SearchOrder.RELEVANCE
        self.offset = 0
        self.search_duration = None
        self.terms = []
        self.spelling = None
        self.message_key = ""
        self.closing = self.closed = False
        self.last_poll = 0.0
        self.last_report = None
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(200)
        self.debounce.timeout.connect(self.suggest)

    @Property(QObject, constant=True)
    def results(self):
        return self.model

    @Property(QObject, constant=True)
    def textReader(self):
        return self.text_reader

    @Property('QVariantMap', notify=preferencesChanged)
    def labels(self):
        return catalog(self.preferences.language)

    @Property('QVariantMap', notify=changed)
    def view(self):
        state = self.state
        running = bool(state and state.job and state.job.status in (JobState.PENDING, JobState.RUNNING))
        busy = bool(self.queued_control or self.control_future is not None and self.control_future[3] != "poll")
        ready = self.session is not None and not busy and not self.closing
        searchable = bool(ready and state and state.search_available)
        status = "closing" if self.closing else (
            "old" if running and state.search_available else
            self.job.state.value if self.job else "ready" if searchable else "building" if state and state.active_directory else "welcome")
        return {"initialized": self.session is not None, "busy": busy,
                "screen": self.screen if state and state.search_available else "onboarding",
                "query": self.query, "field": self.field.value,
                "formats": sorted(f.value for f in self.formats) if self.formats is not None else ["txt", "md", "pdf"],
                "folder": self.folder or "", "order": self.order.value,
                "restricted": self.field != SearchField.BOTH or self.folder is not None or
                    self.formats is not None and self.formats != frozenset(DocumentFormat),
                "optionsSummary": self.options_summary(),
                "closing": self.closing, "closed": self.closed, "ready": ready,
                "canManage": ready and not running, "searchable": searchable,
                "running": running, "canCancel": ready and running,
                "jobProblem": bool(self.job and self.job.state in (JobState.FAILED, JobState.CANCELLED)),
                "directory": state.active_directory if state and state.active_directory else "",
                "status": self.tr(status), "message": self.tr(self.message_key) if self.message_key else "",
                "language": self.preferences.language, "theme": self.preferences.theme,
                "suggestions": self.terms,
                "spellingProposal": self.spelling.proposed_query if self.spelling else "",
                "spellingChanges": ", ".join(f"<b>{escape(item.original)} → {escape(item.replacement)}</b>"
                                              for item in self.spelling.replacements) if self.spelling else "",
                "selectedPath": self.selected.relative_path.value if self.selected else "",
                "viewerSource": self.viewer.source, "viewerPage": self.viewer.page,
                "viewerName": self.viewer.name, "viewerQuery": self.viewer.query,
                "viewerKind": self.viewer_kind,
                "viewerTextStatus": self.viewer_probe.status,
                "resultsScroll": self.results_scroll, "resultsIndex": self.results_index,
                "focusResultOnReturn": self.focus_result_on_return,
                "total": self.response.total_matches if self.response else 0,
                "hasResponse": self.response is not None, "offset": self.offset,
                "pageSize": PAGE_SIZE,
                "searchDuration": self.search_duration if self.search_duration is not None else -1,
                "canPrevious": searchable and self.response is not None and self.offset > 0,
                "canNext": searchable and self.response is not None and self.offset + PAGE_SIZE < self.response.total_matches,
                "reading": self.read_future is not None or bool(self.queued_reads),
                "searching": bool(self.read_future and self.read_future[4] == "search" or
                                  "search" in self.queued_reads),
                "progress": self.job.progress if self.job and self.job.progress is not None else -1,
                "phase": self.tr(self.job.phase.value) if self.job and running else "",
                "counts": f"{self.job.files_completed} / {self.job.files_total or 'â€”'}" if self.job and running else "",
                "diagnostics": self.diagnostics()}

    def options_summary(self):
        parts = []
        if self.field != SearchField.BOTH:
            parts.append(self.tr(self.field.value))
        if self.formats is not None and self.formats != frozenset(DocumentFormat):
            parts.append(" / ".join(sorted(f.value.upper() for f in self.formats)))
        if self.folder:
            parts.append(self.folder)
        return " Â· ".join(parts)

    @Slot(str)
    def navigate(self, screen):
        if self.screen == "viewer" and self.viewer_kind == "text" and self.text_reader.dirty:
            return
        if screen == "back" and self.screen == "viewer":
            self.screen = "results"
            self.focus_result_on_return = True
            self.viewer_probe.cancel()
            self.viewer.clear()
            self.text_reader.cancel()
            self.viewer_result = self.viewer_root = self.viewer_snapshot = None
            self.changed.emit()
            return
        if screen == "settings":
            self.return_screen = self.screen
        elif screen == "back":
            screen = self.return_screen
        if screen in ("home", "results", "settings"):
            self.screen = screen
            self.debounce.stop()
            self.suggest_generation += 1
            self.queued_reads.pop("suggest", None)
            self.terms = []
            self.changed.emit()

    @Slot()
    def resetOptions(self):
        self.setOptions("both", ["txt", "md", "pdf"], "", "relevance")

    def tr(self, key):
        return translate(key, self.preferences.language)

    def diagnostics(self):
        if not self.last_report:
            return ""
        report = self.last_report
        lines = [self.tr("complete" if report.complete else "incomplete"),
                 f"{self.tr('excluded')}: {report.excluded}"]
        # Translation only: reasons never determine operational behavior.
        for item in report.diagnostics:
            from .i18n import diagnostic_text
            lines.append(f"{item.relative_path or 'â€”'} Â· {self.tr(item.phase.value)} Â· "
                         f"{diagnostic_text(item.reason, item.category, self.preferences.language)}")
        return "\n".join(lines)

    def error(self, exc):
        self.message_key = type(exc).__name__
        self.changed.emit()

    def control(self, operation, success, kind="control"):
        if self.closing or self.queued_control:
            return False
        if self.control_future:
            if self.control_future[3] == "poll" and kind != "poll":
                self.queued_control = (operation, success, kind)
                self.changed.emit()
                return True
            return False
        self.control_future = (self.executor.submit(operation), success, self.error, kind)
        self.changed.emit()
        return True

    @Slot()
    def initialize(self):
        if self.session or self.closing:
            return

        def create():
            session = self.factory()
            try:
                preferences = session.get_preferences.execute()
                try:
                    state = session.initialize.execute()
                    error = None
                except SnapshotUnavailable as exc:
                    state, error = session.status.execute(), exc
                return session, state, preferences, error
            except BaseException:
                session.close()
                raise

        def ready(value):
            self.session, state, self.preferences, error = value
            self.preferencesChanged.emit()
            self.apply_state(state)
            self.message_key = type(error).__name__ if error else ""

        self.control(create, ready)

    def invalidate(self, *, keep_viewer=False):
        if self.screen == "viewer" and not keep_viewer:
            self.screen = "results"
            self.viewer_probe.cancel()
            self.viewer.clear()
            self.text_reader.cancel()
            self.viewer_result = self.viewer_root = self.viewer_snapshot = None
        self.generation += 1
        self.suggest_generation += 1
        self.spelling_generation += 1
        self.response = self.selected = None
        self.response_query = ""
        self.results_scroll = 0.0
        self.results_index = -1
        self.focus_result_on_return = False
        self.search_duration = None
        self.offset = 0
        self.terms = []
        self.spelling = None
        self.queued_reads.clear()
        self.model.replace([])
        self.changed.emit()

    @Slot(str, int)
    def editQuery(self, text, cursor):
        if text == self.query and python_cursor(text, cursor) == self.cursor:
            return
        if text != self.query:
            self.query = text
            self.invalidate()
            self.message_key = ""
        self.cursor = python_cursor(text, cursor)
        self.suggest_generation += 1
        self.terms = []
        self.debounce.start()
        self.changed.emit()

    @Slot(str, 'QVariantList', str, str)
    def setOptions(self, field, formats, folder, order):
        try:
            values = (SearchField(field), frozenset(DocumentFormat(value) for value in formats),
                      folder.strip() or None, SearchOrder(order))
            if not values[1]:
                raise ValueError("At least one format is required")
            rerun = self.response is not None or self.screen == "results" or self.return_screen == "results"
            self.field, self.formats, self.folder, self.order = values
            self.invalidate()
            if rerun and self.query.strip():
                self.search_page(0)
        except ValueError as exc:
            self.message_key = "InvalidInput"
            self.changed.emit()

    def enqueue_read(self, kind, operation, success, token, current):
        if self.closing:
            return
        self.queued_reads[kind] = (operation, success, token, current)
        self.start_read()

    def start_read(self):
        if self.read_future or not self.queued_reads or self.closing:
            return
        kind = next((key for key in ("search", "suggest", "spelling") if key in self.queued_reads))
        operation, success, token, current = self.queued_reads.pop(kind)
        if token != current():
            return
        self.read_future = (self.reader.submit(operation), success, token, current, kind)
        self.changed.emit()

    @Slot()
    def search(self):
        if not self.view["searchable"] or not self.query.strip():
            return
        query, formats = extract_format_filters(self.query)
        if formats:
            self.formats = formats
            if query != self.query:
                self.editQuery(query, len(query))
                self.debounce.stop()
                self.queryReplacement.emit(query, len(query.encode("utf-16-le")) // 2)
            else:
                self.invalidate()
            if not query:
                self.screen = "home"
                self.changed.emit()
                QTimer.singleShot(0, lambda: self.queryReplacement.emit("", 0))
                return
        self.screen = "results"
        self.search_page(0)

    def search_page(self, offset):
        if not self.view["searchable"]:
            return
        self.debounce.stop()
        self.suggest_generation += 1
        self.terms = []
        if offset == 0:
            self.spelling_generation += 1
            self.queued_reads.pop("spelling", None)
            self.spelling = None
        self.generation += 1
        self.selected = None
        self.results_scroll = 0.0
        self.results_index = -1
        try:
            request = SearchRequest(self.query, self.field, offset=offset, limit=PAGE_SIZE, allow_wildcards=True,
                                    formats=self.formats, folder=self.folder, order=self.order,
                                    snapshot_id=self.state.active_snapshot_id)
        except InvalidInput as exc:
            self.error(exc)
            return
        token = self.generation
        session = self.session
        started = time.perf_counter()
        self.search_duration = None

        def execute():
            response = session.search.execute(request)
            return response, result_rows(response)

        def complete(value):
            response, rows = value
            if response.snapshot_id != self.state.active_snapshot_id:
                self.search_page(0)
                return
            self.response, self.offset = response, offset
            self.response_query = request.query
            self.search_duration = max(0.0, time.perf_counter() - started)
            self.model.replace(rows)
            self.message_key = ""
            if offset == 0 and self.session.suggest_spelling is not None:
                spelling_request = SpellingRequest(request.query, request.field, response.snapshot_id)
                spelling_token = self.spelling_generation
                self.enqueue_read("spelling", lambda: session.suggest_spelling.execute(spelling_request),
                                  self.complete_spelling, spelling_token, lambda: self.spelling_generation)

        self.enqueue_read("search", execute, complete, token, lambda: self.generation)

    def complete_spelling(self, response):
        if response.snapshot_id == self.state.active_snapshot_id:
            self.spelling = response if response.proposed_query else None

    @Slot()
    def acceptSpelling(self):
        if not self.spelling or not self.view["searchable"]:
            return
        proposal = self.spelling.proposed_query
        self.editQuery(proposal, len(proposal.encode("utf-16-le")) // 2)
        self.debounce.stop()
        self.queryReplacement.emit(proposal, len(proposal.encode("utf-16-le")) // 2)
        self.search_page(0)

    @Slot(int)
    def page(self, direction):
        if direction < 0 and self.view["canPrevious"]:
            self.search_page(max(0, self.offset - PAGE_SIZE))
        elif direction > 0 and self.view["canNext"]:
            self.search_page(self.offset + PAGE_SIZE)

    def suggestion_span(self):
        before = self.query[:self.cursor]
        if before.count('"') % 2:
            return None
        match = re.search(r"[^\W_]+$", before, re.UNICODE)
        if not match or len(match[0]) < 2:
            return None
        start = match.start()
        mode = SuggestMode.PREFIX
        if start and before[start - 1] == '*':
            start -= 1
            mode = SuggestMode.SUFFIX
        if start and before[start - 1] not in ' \t\n':
            return None
        after = re.match(r"[^\W_]*", self.query[self.cursor:])[0]
        end = self.cursor + len(after)
        if self.query[end:end + 1] == "*" or '*' in self.query[self.cursor:end]:
            return None
        return start, end, match[0], mode

    def suggest(self):
        span = self.suggestion_span()
        if not span or not self.view["searchable"]:
            return
        request = SuggestRequest(span[2], self.field, 10, self.state.active_snapshot_id, span[3])
        token = (self.generation, self.suggest_generation)
        session = self.session

        def complete(response):
            if response.snapshot_id == self.state.active_snapshot_id:
                self.terms = list(response.terms)

        self.enqueue_read("suggest", lambda: session.suggest.execute(request), complete,
                          token, lambda: (self.generation, self.suggest_generation))

    @Slot(int)
    def acceptSuggestion(self, index):
        span = self.suggestion_span()
        if span and 0 <= index < len(self.terms):
            term = self.terms[index]
            text = self.query[:span[0]] + term + self.query[span[1]:]
            cursor = len((self.query[:span[0]] + term).encode("utf-16-le")) // 2
            self.editQuery(text, cursor)
            self.debounce.stop()
            self.queryReplacement.emit(text, cursor)

    @Slot(int)
    def acceptSuggestionAndSearch(self, index):
        before = self.query
        self.acceptSuggestion(index)
        if self.query != before:
            self.search()

    @Slot(int)
    def openResult(self, index):
        if (not self.response or not 0 <= index < len(self.response.results)
                or not self.view["searchable"]
                or self.response.snapshot_id != self.state.active_snapshot_id):
            return
        self.selected = self.response.results[index]
        self.results_index = index
        self.focus_result_on_return = False
        self.openSelected()

    @Slot()
    def resultFocusRestored(self):
        self.focus_result_on_return = False

    @Slot(float)
    def rememberResultsScroll(self, value):
        if self.screen == "viewer":
            self.results_scroll = value

    def apply_state(self, state):
        previous = self.state
        changed_directory = previous and previous.active_directory != state.active_directory
        changed_snapshot = previous and previous.active_snapshot_id != state.active_snapshot_id
        rerun = bool(self.response or self.read_future and self.read_future[4] == "search")
        self.state = state
        if changed_directory or changed_snapshot:
            self.invalidate(keep_viewer=bool(changed_snapshot and not changed_directory and self.screen == "viewer"))
            if changed_directory:
                self.job = self.last_report = None
                self.field, self.formats, self.folder, self.order = SearchField.BOTH, None, None, SearchOrder.RELEVANCE
                self.screen = self.return_screen = "home"
                self.query = ""
            elif rerun and self.query.strip() and not self.closing:
                self.search_page(0)
        if state.warning:
            self.message_key = state.warning

    @Slot(str)
    def chooseDirectory(self, url):
        if self.screen == "viewer" and self.viewer_kind == "text" and self.text_reader.dirty:
            return
        if not self.view["canManage"]:
            return
        path = QUrl(url).toLocalFile()
        if self.control(lambda: self.session.select_directory.execute(path), self.apply_state):
            self.invalidate()

    @Slot(str)
    def action(self, name):
        if not self.session or self.closing:
            return
        if name == "cancel" and self.view["canCancel"]:
            job_id = self.state.job.job_id
            self.control(lambda: self.session.cancel_synchronization.execute(job_id),
                         lambda outcome: setattr(self, "message_key", outcome.value))
            return
        if not self.view["canManage"]:
            return
        operations = {"sync": self.session.request_synchronization.execute,
                      "retry": self.session.request_synchronization.execute,
                      "rebuild": self.session.rebuild.execute,
                      "recover": self.session.recover_previous.execute,
                      "clear": self.session.clear_local_data.execute}
        if name not in operations:
            return

        def execute():
            operations[name]()
            return self.session.status.execute(), self.session.get_preferences.execute()

        def complete(value):
            state, self.preferences = value
            self.preferencesChanged.emit()
            self.message_key = ""
            self.apply_state(state)
            if name == "clear":
                self.job = self.last_report = None
                self.invalidate()

        self.control(execute, complete)

    @Slot(str, str)
    def savePreferences(self, language, theme):
        try:
            value = DesktopPreferences(language, theme)
        except InvalidInput as exc:
            self.error(exc)
            return
        if self.session:
            def complete(saved):
                self.preferences = saved
                self.preferencesChanged.emit()
                self.message_key = ""
            self.control(lambda: self.session.save_preferences.execute(value), complete)

    @Slot()
    def openSelected(self):
        if self.screen == "viewer" and self.viewer_kind == "text" and self.text_reader.dirty:
            return
        if self.selected and self.view["searchable"]:
            try:
                if self.selected.format is DocumentFormat.PDF:
                    self.viewer_kind = "pdf"
                    self.viewer.open(self.state.active_directory, self.selected.relative_path,
                                     self.selected.filename, self.selected.pdf_target_page, self.response_query)
                    self.viewer_probe.start(self.viewer.path)
                    self.screen = "viewer"
                    self.changed.emit()
                else:
                    self.viewer_kind = "text"
                    self.viewer_result = self.selected
                    self.viewer_root = self.state.active_directory
                    self.viewer_snapshot = self.response.snapshot_id
                    self.viewer.open(self.state.active_directory, self.selected.relative_path,
                                     self.selected.filename, None, self.response_query)
                    self.text_reader.open(self.session, self.state.active_directory,
                                          self.selected, self.response.snapshot_id)
                    self.screen = "viewer"
                    self.changed.emit()
            except Exception as exc:
                self.error(exc)

    @Slot()
    def retryTextViewer(self):
        if (self.screen == "viewer" and self.viewer_kind == "text" and self.viewer_result
                and self.session and self.state and self.state.active_directory == self.viewer_root):
            self.text_reader.open(self.session, self.viewer_root,
                                  self.viewer_result, self.viewer_snapshot)

    @Slot()
    def openViewerExternally(self):
        if self.screen == "viewer" and self.viewer.relative_path and self.state:
            try:
                self.opener(self.state.active_directory, self.viewer.relative_path)
            except Exception as exc:
                self.error(exc)

    @Slot()
    def openViewerFolder(self):
        if self.screen == "viewer" and self.viewer.relative_path and self.state:
            try:
                from .composition import open_document_folder
                open_document_folder(self.state.active_directory, self.viewer.relative_path)
            except Exception as exc:
                self.error(exc)

    def poll(self):
        session = self.session

        def execute():
            state = session.status.execute()
            job = session.job_status.execute(state.job.job_id) if state.job else None
            return state, job

        def complete(value):
            state, job = value
            self.job = job
            if job and job.report:
                self.last_report = job.report
            self.apply_state(state)

        self.control(execute, complete, "poll")

    @Slot()
    def requestClose(self):
        if self.screen == "viewer" and self.viewer_kind == "text" and (self.text_reader.dirty or self.text_reader.saving):
            return
        if self.closing or self.closed:
            return
        self.closing = True
        self.queued_control = None
        self.debounce.stop()
        self.invalidate()
        self.viewer_probe.close()
        self.text_reader.close()

    def tick(self):
        if self.control_future and self.control_future[0].done():
            future, success, failure, kind = self.control_future
            self.control_future = None
            try:
                success(future.result())
            except Exception as exc:
                failure(exc)
                if kind == "close":
                    self.closing = False
            self.changed.emit()
        if self.read_future and self.read_future[0].done():
            future, success, token, current, kind = self.read_future
            self.read_future = None
            if not self.closing and token == current():
                try:
                    success(future.result())
                except Exception as exc:
                    if isinstance(exc, SnapshotUnavailable) and kind == "search":
                        self.response = None
                        self.model.replace([])
                    if kind != "spelling":
                        self.error(exc)
            self.changed.emit()
        if self.closed:
            return
        if self.closing:
            if self.control_future is None and self.read_future is None:
                def finished(_):
                    self.closed = True
                    self.reader.shutdown(wait=False)
                    self.executor.shutdown(wait=False)
                    self.timer.stop()
                    self.changed.emit()
                    self.closeReady.emit()
                self.control_future = (self.executor.submit(lambda: self.session.close() if self.session else None),
                                       finished, self.error, "close")
            return
        if self.queued_control and not self.control_future:
            operation, success, kind = self.queued_control
            self.queued_control = None
            self.control(operation, success, kind)
        self.start_read()
        if self.session and not self.control_future and time.monotonic() - self.last_poll >= 0.25:
            self.last_poll = time.monotonic()
            self.poll()
