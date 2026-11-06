"""Lock OS di sessione: il file può restare, il possesso termina col processo."""
import os

from local_document_search.application.errors import StorageFailure
from .sqlite_snapshot_storage import storage_directory


class StorageLock:
    def __init__(self, directory=None):
        self.directory = storage_directory(directory)
        self._file = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            self._file = open(self.directory / "session.lock", "a+b")
            if os.name == "nt":
                import msvcrt
                self._file.seek(0)
                msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if self._file is not None:
                self._file.close()
                self._file = None
            raise StorageFailure("Storage occupato o lock non acquisibile") from exc

    def close(self):
        if self._file is not None:
            # Anche il crash rilascia il lock tramite la chiusura OS del descriptor.
            self._file.close()
            self._file = None
