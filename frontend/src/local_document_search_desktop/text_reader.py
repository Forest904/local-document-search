"""Sessione del reader testuale: I/O nei worker, QTextDocument nel thread GUI."""
from array import array
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
import re
from threading import Event

from PySide6.QtCore import QObject, Property, QRegularExpression, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QGuiApplication, QTextCharFormat, QTextCursor, QSyntaxHighlighter
from shiboken6 import isValid

from local_document_search.application.text_view import TextViewRequest, SaveTextRequest
from local_document_search.domain.documents import DocumentFormat
from .markdown_preview import render_preview


def display_text(source):
    return source.replace("\r\n", "\n").replace("\r", "\n")


def qt_offset(source, offset):
    """Convert a source Python offset through newline folding and UTF-16."""
    prefix = display_text(source[:offset])
    return len(prefix.encode("utf-16-le", errors="surrogatepass")) // 2


def find_literal(text, needle, cancelled=None):
    regex = QRegularExpression(QRegularExpression.escape(needle), QRegularExpression.CaseInsensitiveOption)
    if not regex.isValid():
        raise ValueError("Ricerca non valida")
    found = array("I")
    iterator = regex.globalMatch(text)
    while iterator.hasNext():
        if cancelled is not None and cancelled.is_set():
            return array("I")
        match = iterator.next()
        found.extend((match.capturedStart(), match.capturedEnd()))
    return found


def prepare_display(operation, request):
    prepared = operation(request)
    source = prepared.source
    shown = display_text(source)
    target = tuple((qt_offset(source, item.start), qt_offset(source, item.end))
                   for item in prepared.source_ranges)
    starts = array("I", [0])
    position = 0
    for char in shown:
        position += 2 if ord(char) > 0xFFFF else 1
        if char == "\n":
            starts.append(position)
    preview = render_preview(shown, tuple((len(display_text(source[:item.start])), len(display_text(source[:item.end])))
                                          for item in prepared.source_ranges)) if request.format is DocumentFormat.MARKDOWN else ("", None, "")
    return prepared, shown, target, starts, preview


class MatchHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.ranges = ()
        self.color = QColor("#E9E5F3")

    def set_mark(self, ranges, color):
        previous = self.ranges
        self.ranges = tuple(ranges)
        self.color = QColor(color)
        document = self.document()
        if document is None:
            return
        affected = set()
        for first, last in (*previous, *self.ranges):
            block = document.findBlock(first)
            while block.isValid() and block.position() < last:
                affected.add(block.blockNumber())
                block = block.next()
        for number in sorted(affected):
            self.rehighlightBlock(document.findBlockByNumber(number))

    def highlightBlock(self, text):
        block = self.currentBlock()
        first, last = block.position(), block.position() + block.length()
        fmt = QTextCharFormat()
        fmt.setBackground(self.color)
        for start, end in self.ranges:
            if start < last and end > first:
                self.setFormat(max(0, start - first), min(end, last) - max(start, first), fmt)


class TextReaderBridge(QObject):
    changed = Signal()
    gutterChanged = Signal()
    jumpRequested = Signal(int, int)
    saveCompleted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="text-view")
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._poll)
        self._chunks = QTimer(self)
        self._chunks.setInterval(0)
        self._chunks.timeout.connect(self._append_chunk)
        self._gutter_timer = QTimer(self)
        self._gutter_timer.setInterval(0)
        self._gutter_timer.timeout.connect(self._build_block_y_step)
        self._gutter_block = None
        self._wrapper = self._document = self._highlighter = None
        self._open_future = self._find_future = None
        self._save_future = None
        self._preview_future = None
        self._preview_revision = 0
        self._session = self._directory = self._relative_path = self._format = None
        self._version = None
        self._saved_display = ""
        self._sync_warning = False
        self._mode = "source"
        self._preview_html = ""
        self._preview_target = None
        self._preview_plain = ""
        self._editing = False
        self._dirty = False
        self._generation = self._find_generation = 0
        self._source = self._display = ""
        self._target = ()
        self._line_starts = array("I", [0])
        self._block_y = []
        self._inserted = 0
        self._matches = array("I")
        self._match_index = -1
        self._find_cancelled = None
        self._find_direction = 1
        self._last_needle = ""
        self._wrapped = False
        self._mark = ""
        self._dark = False
        self.status = "idle"
        self.error = ""
        self.warning = ""
        self.name = ""
        self.path = ""
        self.bom = False
        self.line_endings = "none"
        self._timer.start()

    @Property(str, notify=changed)
    def state(self): return self.status

    @Property(str, notify=changed)
    def errorKey(self): return self.error

    @Property(str, notify=changed)
    def warningKey(self): return self.warning

    @Property(str, notify=changed)
    def filename(self): return self.name

    @Property(str, notify=changed)
    def marker(self): return self._mark

    @Property(int, notify=changed)
    def matchCount(self): return len(self._matches) // 2

    @Property(int, notify=changed)
    def matchIndex(self): return self._match_index + 1

    @Property(bool, notify=changed)
    def searching(self): return self._find_future is not None

    @Property(bool, notify=changed)
    def wrapped(self): return self._wrapped

    @Property(bool, notify=changed)
    def ready(self): return self.status == "ready"

    @Property(bool, notify=changed)
    def markdown(self): return self._format is DocumentFormat.MARKDOWN

    @Property(bool, notify=changed)
    def editing(self): return self._editing

    @Property(bool, notify=changed)
    def dirty(self): return self._dirty

    @Property(bool, notify=changed)
    def saving(self): return self._save_future is not None

    @Property(bool, notify=changed)
    def syncWarning(self): return self._sync_warning

    @Property(str, notify=changed)
    def mode(self): return self._mode

    @Property(str, notify=changed)
    def previewHtml(self): return self._preview_html

    @Property('QVariantList', notify=changed)
    def previewTarget(self): return list(self._preview_target or ())

    @Slot(QObject)
    def attach(self, wrapper):
        self._wrapper = wrapper
        self._document = wrapper.textDocument()
        self._document.setUndoRedoEnabled(False)
        self._highlighter = MatchHighlighter(self._document)
        self._document.contentsChanged.connect(self._document_changed)
        self._reset_document()
        if self.status == "populating":
            self._chunks.start()

    @Slot()
    def detach(self):
        self._chunks.stop()
        self._gutter_timer.stop()
        self._wrapper = self._document = self._highlighter = None

    def _reset_document(self):
        self._chunks.stop()
        self._gutter_timer.stop()
        if self._highlighter and isValid(self._highlighter):
            self._highlighter.set_mark((), "#E9E5F3")
        if self._document and isValid(self._document):
            self._document.clear()
            self._document.setUndoRedoEnabled(False)
        elif self._document:
            self.detach()

    def open(self, session, directory, result, snapshot_id):
        self.cancel()
        self._session, self._directory = session, directory
        self._relative_path, self._format = result.relative_path, result.format
        self.name = result.filename
        self.path = result.relative_path.value
        self.status = "loading"
        self.changed.emit()
        request = TextViewRequest(directory, result.relative_path, result.format,
                                  snapshot_id, result.text_target)
        self._open_future = (self._executor.submit(prepare_display,
                                                  session.prepare_text_view.execute, request), self._generation)

    @Slot()
    def cancel(self):
        self._generation += 1
        self._preview_revision += 1
        self._find_generation += 1
        self._chunks.stop()
        if self._open_future:
            self._open_future[0].cancel()
        if self._find_future:
            self._find_future[0].cancel()
        if self._find_cancelled:
            self._find_cancelled.set()
        self._open_future = self._find_future = None
        if self._preview_future:
            self._preview_future[0].cancel()
        self._preview_future = None
        self._find_cancelled = None
        self._source = self._display = ""
        self._dirty = self._editing = False
        self._mode = "source"
        self._version = None
        self._sync_warning = False
        self._preview_html = self._preview_plain = ""
        self._preview_target = None
        self._target = ()
        self._line_starts = array("I", [0])
        self._block_y = []
        self._gutter_block = None
        self._matches = array("I")
        self._match_index = -1
        self._mark = ""
        self._wrapped = False
        self.status = "idle"
        self.error = self.warning = ""
        self._reset_document()
        self.changed.emit()

    def _poll(self):
        if self._open_future and self._open_future[0].done():
            future, generation = self._open_future
            self._open_future = None
            if generation == self._generation:
                try:
                    prepared, shown, target, line_starts, preview = future.result()
                    self._source = prepared.source
                    self._display = shown
                    self.bom = prepared.bom
                    self.line_endings = prepared.line_endings
                    self._version = prepared.source_version
                    self._saved_display = shown
                    self._target = target
                    self._preview_html, self._preview_target, self._preview_plain = preview
                    self.warning = prepared.destination_status if prepared.destination_status in ("changed", "unavailable") else ""
                    self._line_starts = line_starts
                    self._inserted = 0
                    self.status = "populating"
                    if self._document:
                        self._chunks.start()
                    self.changed.emit()
                except MemoryError:
                    self.error, self.status = "ResourceFailure", "error"
                    self.changed.emit()
                except Exception as exc:
                    self.error, self.status = type(exc).__name__, "error"
                    self.changed.emit()
        if self._find_future and self._find_future[0].done():
            future, generation = self._find_future
            self._find_future = None
            if generation == self._find_generation and self.status == "ready":
                try:
                    self._matches = future.result()
                    self._match_index = (0 if self._find_direction >= 0 else len(self._matches) // 2 - 1) if self._matches else -1
                    self._mark = "manual" if self._matches else ""
                    self._wrapped = False
                    self._apply_mark()
                    self.changed.emit()
                    self._jump_current()
                except Exception:
                    self._matches = array("I")
                    self._match_index = -1
                    self.changed.emit()
        if self._save_future and self._save_future.done():
            future = self._save_future
            self._save_future = None
            try:
                saved = future.result()
                self._source = saved.source
                self._version = saved.source_version
                self._saved_display = self._display
                self._dirty = False
                self.error = ""
                self._sync_warning = not saved.sync_requested
                self.saveCompleted.emit()
            except Exception as exc:
                self.error = type(exc).__name__
            self.changed.emit()
        if self._preview_future and self._preview_future[0].done():
            future, revision = self._preview_future
            self._preview_future = None
            if revision == self._preview_revision and not self._editing:
                try:
                    self._preview_html, self._preview_target, self._preview_plain = future.result()
                    self._mode = "preview"
                    self.warning = ""
                except Exception:
                    self.warning = "unavailable"
                    self._mode = "source"
                self.changed.emit()

    def _append_chunk(self):
        if not self._document or not isValid(self._document) or self.status != "populating":
            self._chunks.stop()
            return
        try:
            if self._inserted < len(self._display):
                cursor = QTextCursor(self._document)
                cursor.movePosition(QTextCursor.End)
                segment = self._display[self._inserted:self._inserted + 16384]
                cursor.insertText(segment)
                self._inserted += len(segment)
                return
            self._chunks.stop()
            self.status = "ready"
            self._document.setUndoRedoEnabled(True)
            if self.markdown:
                if self._target and self._preview_target is None:
                    self._mode = "source"
                    self.warning = "unavailable"
                else:
                    self._mode = "preview"
            self.invalidateLayout()
            if self._target:
                self._mark = "snapshot"
                self._apply_mark()
            self.changed.emit()
            if self._target:
                self.jumpRequested.emit(*self._target[0])
        except MemoryError:
            self._chunks.stop()
            self.error, self.status = "ResourceFailure", "error"
            self.changed.emit()

    def _build_block_y_step(self):
        if not self._document or not isValid(self._document) or self.status != "ready":
            self._gutter_timer.stop()
            return
        block = self._gutter_block
        layout = self._document.documentLayout()
        for _ in range(256):
            if not block.isValid():
                self._gutter_timer.stop()
                block = None
                break
            self._block_y.append(layout.blockBoundingRect(block).top())
            block = block.next()
        if block is not None and not block.isValid():
            self._gutter_timer.stop()
            block = None
        self._gutter_block = block
        self.gutterChanged.emit()

    @Slot()
    def refreshLayout(self):
        if self.status == "ready" and self._gutter_block is not None and not self._gutter_timer.isActive():
            self._gutter_timer.start()

    @Slot()
    def invalidateLayout(self):
        self._gutter_timer.stop()
        self._block_y = []
        self._gutter_block = self._document.begin() if self._document and isValid(self._document) else None
        if self.status == "ready" and self._gutter_block is not None:
            self._gutter_timer.start()

    @Slot(float, float, result='QVariantList')
    def visibleLines(self, top, height):
        if self.status != "ready" or not self._block_y or not self._document or not isValid(self._document):
            return []
        index = max(0, bisect_right(self._block_y, top) - 1)
        output = []
        while index < len(self._block_y) and self._block_y[index] < top + height:
            block = self._document.findBlockByNumber(index)
            number = bisect_right(self._line_starts, block.position())
            output.append({"number": number, "y": self._block_y[index]})
            index += 1
        return output

    @Slot(bool)
    def setDark(self, dark):
        self._dark = dark
        self._apply_mark()

    def _apply_mark(self):
        if not self._highlighter or not isValid(self._highlighter):
            return
        if self._mark == "snapshot":
            self._highlighter.set_mark(self._target, "#51456E" if self._dark else "#E9E5F3")
        elif self._mark == "manual" and self._match_index >= 0:
            i = self._match_index * 2
            self._highlighter.set_mark(((self._matches[i], self._matches[i + 1]),),
                                       "#315D50" if self._dark else "#DFEAE2")
        else:
            self._highlighter.set_mark((), "#E9E5F3")

    @Slot()
    def clearFind(self):
        self._find_generation += 1
        if self._find_future:
            self._find_future[0].cancel()
        if self._find_cancelled:
            self._find_cancelled.set()
        self._find_future = None
        self._find_cancelled = None
        self._last_needle = ""
        self._matches = array("I")
        self._match_index = -1
        self._wrapped = False
        if self._mark == "manual":
            self._mark = ""
        self._apply_mark()
        self.changed.emit()

    @Slot(str, int)
    def find(self, needle, direction):
        if self.status != "ready" or not needle or re.search(r"[\r\n]", needle):
            return
        if self._matches and self._mark == "manual" and needle == self._last_needle:
            self.step(direction)
            return
        self._find_generation += 1
        self._matches = array("I")
        self._match_index = -1
        self._mark = ""
        self._wrapped = False
        self._last_needle = needle
        self._find_direction = direction
        self._find_cancelled = Event()
        self._apply_mark()
        self._find_future = (self._executor.submit(find_literal, self._preview_plain if self._mode == "preview" else self._display, needle,
                                                   self._find_cancelled), self._find_generation)
        self.changed.emit()

    @Slot(int)
    def step(self, direction):
        if not self._matches:
            return
        count = len(self._matches) // 2
        next_index = self._match_index + direction
        self._wrapped = next_index < 0 or next_index >= count
        self._match_index = next_index % count
        self._apply_mark()
        self.changed.emit()
        self._jump_current()

    def _jump_current(self):
        if self._match_index >= 0:
            i = self._match_index * 2
            self.jumpRequested.emit(self._matches[i], self._matches[i + 1])

    def close(self):
        self.cancel()
        self._timer.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _document_changed(self):
        if self.status != "ready" or not self._editing or self._save_future:
            return
        self._display = self._document.toPlainText()
        self._preview_revision += 1
        if self._last_needle:
            self.clearFind()
        self._dirty = self._display != self._saved_display
        self._target = ()
        self._preview_target = None
        if self._mark == "snapshot":
            self._mark = ""
            self._apply_mark()
        self.changed.emit()

    @Slot()
    def startEditing(self):
        if self.ready and not self.saving:
            self.clearFind()
            self._preview_revision += 1
            self._mode = "source"
            self._editing = True
            self.changed.emit()

    @Slot()
    def stopEditing(self):
        if self.ready and not self.saving:
            self.clearFind()
            self._editing = False
            if self.markdown:
                self._mode = "rendering"
                self._preview_future = (self._executor.submit(render_preview, self._display), self._preview_revision)
            self.changed.emit()

    @Slot()
    def save(self):
        if not self.ready or not self._dirty or self.saving or self._version is None:
            return
        request = SaveTextRequest(self._directory, self._relative_path, self._format,
                                  self._display, self._source, self.bom, self._version)
        self._save_future = self._executor.submit(self._session.save_text_document.execute, request)
        self.changed.emit()

    @Slot()
    def copyDraft(self):
        QGuiApplication.clipboard().setText(self._display)

    @Slot()
    def discard(self):
        self._dirty = False
        self.changed.emit()

    @Slot(str)
    def copyLink(self, address):
        QGuiApplication.clipboard().setText(address)

    @Slot(str, int, int)
    def formatSelection(self, kind, start, end):
        if not self.ready or not self._editing or not self.markdown or self.saving:
            return
        cursor = QTextCursor(self._document)
        cursor.setPosition(min(start, end))
        cursor.setPosition(max(start, end), QTextCursor.KeepAnchor)
        selected = cursor.selectedText().replace("\u2029", "\n")
        if kind.startswith("h") and kind[1:].isdigit():
            replacement = "#" * max(1, min(6, int(kind[1:]))) + " " + selected
        elif kind == "bold": replacement = "**" + selected + "**"
        elif kind == "italic": replacement = "*" + selected + "*"
        elif kind == "bullet": replacement = "- " + selected
        elif kind == "number": replacement = "1. " + selected
        elif kind == "quote": replacement = "> " + selected
        elif kind == "link": replacement = "[" + (selected or "testo") + "](url)"
        elif kind == "code": replacement = "`" + selected + "`"
        elif kind == "block": replacement = "```\n" + selected + "\n```"
        else: return
        cursor.beginEditBlock()
        cursor.insertText(replacement)
        cursor.endEditBlock()
