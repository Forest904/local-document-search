"""Unico confine verso la composizione del backend e il sistema operativo."""
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from local_document_search.interfaces.composition import compose_v2_application


def compose_desktop(storage=None):
    return compose_v2_application(storage)


def open_document(directory, relative_path):
    path = Path(directory) / relative_path.value
    if not path.is_file():
        raise FileNotFoundError("File non disponibile. Premi Sync per aggiornare l'indice.")
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
        raise OSError("Impossibile aprire il file con l'applicazione predefinita.")
