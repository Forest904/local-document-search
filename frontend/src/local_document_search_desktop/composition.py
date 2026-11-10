"""Unico confine verso la composizione del backend e il sistema operativo."""
from pathlib import Path
import os

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from local_document_search.interfaces.composition import compose_v2_application, desktop_storage_directory
from local_document_search.application.errors import StorageFailure


def compose_desktop(storage=None):
    return compose_v2_application(storage)


def open_document(directory, relative_path):
    path = Path(directory) / relative_path.value
    if not path.is_file():
        raise FileNotFoundError("File non disponibile. Premi Sync per aggiornare l'indice.")
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
        raise OSError("Impossibile aprire il file con l'applicazione predefinita.")


def has_local_session():
    """A v2 catalog is created only after the initial local-data notice."""
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return False
    try:
        return (desktop_storage_directory() / "control-v2.sqlite3").is_file()
    except StorageFailure:
        # L'onboarding lascia alla composizione il normale errore visibile nella UI.
        return False
