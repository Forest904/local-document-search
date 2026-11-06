"""Avvio desktop in-process, distinto dalla CLI Homework."""
import sys

from PySide6.QtWidgets import QApplication

from .composition import compose_desktop, open_document
from .window import SearchWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Local Document Search")
    window = SearchWindow(compose_desktop, open_document)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
