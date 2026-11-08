"""Modello Qt e conversione sicura degli intervalli Unicode applicativi."""
from html import escape

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


def highlighted(text, ranges):
    # Escaping prima del markup: nessuna risorsa, link o HTML dai documenti.
    parts, cursor = [], 0
    for span in ranges:
        parts.extend((escape(text[cursor:span.start]), '<b>',
                      escape(text[span.start:span.end]), '</b>'))
        cursor = span.end
    parts.append(escape(text[cursor:]))
    return "".join(parts).replace("\n", "<br>")


def python_cursor(text, utf16_position):
    return len(text.encode("utf-16-le")[:utf16_position * 2].decode("utf-16-le", errors="ignore"))


class ResultsModel(QAbstractListModel):
    roles = {Qt.UserRole + 1: b"nameHtml", Qt.UserRole + 2: b"pathText",
             Qt.UserRole + 3: b"snippetHtml", Qt.UserRole + 4: b"accessibleText", Qt.UserRole + 5: b"formatText"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def roleNames(self):
        return self.roles

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.rows):
            return None
        key = self.roles.get(role)
        return self.rows[index.row()].get(key.decode()) if key else None

    def replace(self, rows):
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()


def result_rows(response):
    rows = []
    for item in response.results:
        snippet = item.snippet
        rows.append({"formatText": item.format.value.upper(), "nameHtml": highlighted(item.filename, item.filename_highlights),
                     "pathText": item.relative_path.value,
                     "snippetHtml": (("…" if snippet.truncated_before else "") +
                                     highlighted(snippet.text, snippet.highlights).replace("<br>", " ") +
                                     ("…" if snippet.truncated_after else "")) if snippet else "",
                     "accessibleText": item.relative_path.value + "\n" + (snippet.text if snippet else "")})
    return rows
