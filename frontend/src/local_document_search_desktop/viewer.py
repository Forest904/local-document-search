"""Preparazione del file PDF per il viewer, senza dipendenze dal backend IR."""
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QUrl


@dataclass
class PdfViewerState:
    source: str = ""
    page: int = 0
    name: str = ""
    relative_path: object | None = None

    def open(self, directory, relative_path, name, page):
        self.source = QUrl.fromLocalFile(str(Path(directory) / relative_path.value)).toString()
        self.relative_path = relative_path
        self.name = name
        self.page = page if page is not None else 0

    def clear(self):
        self.source = ""
        self.relative_path = None
        self.name = ""
        self.page = 0
