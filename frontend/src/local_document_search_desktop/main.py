"""Avvio desktop in-process, distinto dalla CLI Homework."""
from pathlib import Path
import ctypes
import os
import sys
import tempfile

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .composition import compose_desktop, open_document
from .controller import DesktopController


def create_engine(controller):
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("desktop", controller)
    source = Path(__file__).parent / "qml" / "Main.qml"
    packaged = Path(sys.executable).parent / "local_document_search_desktop" / "qml" / "Main.qml"
    if not source.is_file() and packaged.is_file():
        source = packaged
    engine.load(QUrl.fromLocalFile(str(source)))
    return engine


def main():
    # Il wizard può rilevare un'istanza aperta senza terminarla.
    running_mutex = None
    if os.name == "nt":
        create_mutex = ctypes.windll.kernel32.CreateMutexW
        create_mutex.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
        create_mutex.restype = ctypes.c_void_p
        running_mutex = create_mutex(None, False, "Local\\LocalDocumentSearchV2Running")
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Local Document Search")
    controller = DesktopController(compose_desktop, open_document)
    engine = create_engine(controller)
    if not engine.rootObjects():
        (Path(tempfile.gettempdir()) / "lds-v2-06-qml-error.log").write_text(
            f"source={Path(__file__)}\nexe={sys.executable}\n", encoding="utf-8")
        return 1
    result = app.exec()
    if running_mutex:
        ctypes.windll.kernel32.CloseHandle(running_mutex)
    return result


if __name__ == "__main__":
    sys.exit(main())
