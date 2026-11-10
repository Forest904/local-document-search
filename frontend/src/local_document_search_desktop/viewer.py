"""Preparazione del file PDF per il viewer, senza dipendenze dal backend IR."""
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtPdf import QPdfDocument


def _has_searchable_text(path, cancelled=None):
    document = QPdfDocument()
    try:
        if document.load(str(path)) != QPdfDocument.Error.None_:
            return False
        for page in range(document.pageCount()):
            if cancelled is not None and cancelled.is_set():
                return False
            if document.getAllText(page).text().strip():
                return True
        return False
    finally:
        document.close()


class PdfTextProbe(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pdf-text-probe")
        self._future = None
        self._cancelled = None
        self._generation = 0
        self.status = "idle"
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._poll)

    def start(self, path):
        self.cancel()
        self.status = "checking"
        self._cancelled = Event()
        self._future = (self._executor.submit(_has_searchable_text, path, self._cancelled), self._generation)
        self._timer.start()
        self.changed.emit()

    def cancel(self):
        self._generation += 1
        self._timer.stop()
        if self._cancelled:
            self._cancelled.set()
        self._cancelled = None
        if self._future:
            self._future[0].cancel()
        self._future = None
        self.status = "idle"
        self.changed.emit()

    def _poll(self):
        if not self._future or not self._future[0].done():
            return
        future, generation = self._future
        self._future = None
        self._timer.stop()
        if generation != self._generation:
            return
        try:
            self.status = "available" if future.result() else "unavailable"
        except Exception:
            self.status = "unavailable"
        self.changed.emit()

    def close(self):
        self.cancel()
        self._executor.shutdown(wait=False, cancel_futures=True)


@dataclass
class PdfViewerState:
    source: str = ""
    page: int = 0
    name: str = ""
    query: str = ""
    path: Path | None = None
    relative_path: object | None = None

    def open(self, directory, relative_path, name, page, query=""):
        self.path = Path(directory) / relative_path.value
        self.source = QUrl.fromLocalFile(str(self.path)).toString()
        self.relative_path = relative_path
        self.name = name
        self.query = query
        self.page = page if page is not None else 0

    def clear(self):
        self.source = ""
        self.relative_path = None
        self.name = ""
        self.query = ""
        self.path = None
        self.page = 0
