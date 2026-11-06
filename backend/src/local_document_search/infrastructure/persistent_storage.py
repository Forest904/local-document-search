"""Lifecycle dello storage, distinto dal formato versionato degli snapshot."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from threading import Condition
from uuid import uuid4

from local_document_search.application.errors import SnapshotUnavailable, StorageFailure
from .sqlite_snapshot_storage import SqliteSnapshotRepository, storage_directory


class PersistentSnapshotRepository:
    def __init__(self, settings):
        self.settings = settings
        self.directory = settings.directory
        self._condition = Condition()
        self._readers = 0
        self._blocked = False
        self._retired = []
        self._candidate = None
        self._candidate_name = None
        self._repo = None
        self.incompatible = False
        self.cleanup_diagnostic = None
        name = settings.selected()
        if name:
            self._validate_name(name)
            if not (self.directory / name).is_file():
                raise StorageFailure("Database selezionato assente")
            settings.db.execute("INSERT OR IGNORE INTO owned VALUES (?)", (name,))
            try:
                self._repo = SqliteSnapshotRepository(self.directory, database_name=name)
            except SnapshotUnavailable:
                self.incompatible = True
        self._cleanup()

    @staticmethod
    def _validate_name(name):
        if Path(name).name != name or not (name == "snapshots.sqlite3" or
                (name.startswith("snapshot-") and name.endswith(".sqlite3")
                 and len(name) == len("snapshot-.sqlite3") + 32
                 and all(c in "0123456789abcdef" for c in name[9:-8]))):
            raise StorageFailure("Riferimento database non valido")

    def _cleanup(self):
        if self._readers:
            return
        try:
            for repo in self._retired:
                repo.close()
            self._retired.clear()
            keep = {self.settings.selected(), self._candidate_name}
            for (name,) in self.settings.db.execute("SELECT name FROM owned").fetchall():
                self._validate_name(name)
                if name not in keep:
                    for suffix in ("", "-journal", "-wal", "-shm"):
                        (self.directory / (name + suffix)).unlink(missing_ok=True)
                    self.settings.db.execute("DELETE FROM owned WHERE name=?", (name,))
            self.cleanup_diagnostic = None
        except (OSError, sqlite3.Error, StorageFailure):
            self.cleanup_diagnostic = "Pulizia database da riprovare"

    def load_active(self):
        return self._repo.load_active() if self._repo else None

    @contextmanager
    def acquire(self, snapshot_id=None):
        with self._condition:
            if self._blocked or self._repo is None:
                raise SnapshotUnavailable("Snapshot non disponibile")
            repo = self._repo
            lease = repo.acquire(snapshot_id)
            snapshot = lease.__enter__()
            self._readers += 1
        try:
            yield snapshot
        finally:
            with self._condition:
                try:
                    lease.__exit__(None, None, None)
                finally:
                    self._readers -= 1
                    self._cleanup()
                    self._condition.notify_all()

    def select_directory(self, root):
        storage_directory(self.directory, source_directory=root)
        with self._condition:
            # M5 non salvava settings: la prima scelta fornisce la sorgente del rebuild.
            if self.incompatible and self.settings.load().active_directory is None:
                return
            self.settings.select(None)
            if self._repo:
                self._retired.append(self._repo)
            self._repo = None
            self.incompatible = False
            self._cleanup()

    def save_candidate(self, snapshot):
        if self._repo is not None:
            self._repo.save_candidate(snapshot)
            return
        name = "snapshot-" + uuid4().hex + ".sqlite3"
        self.settings.db.execute("INSERT INTO owned VALUES (?)", (name,))
        self._candidate_name = name
        self._candidate = SqliteSnapshotRepository(self.directory, source_directory=snapshot.root_directory,
                                                   database_name=name)
        self._candidate.save_candidate(snapshot)

    def validate_candidate(self, key):
        (self._candidate or self._repo).validate_candidate(key)

    def activate(self, key):
        repo = self._candidate or self._repo
        repo.activate(key)
        if self._candidate:
            self.settings.select(self._candidate_name)
            self._repo = repo
            self._candidate = None
            self._candidate_name = None
            self.incompatible = False
        self._cleanup()

    def discard_candidate(self, key):
        if self._candidate:
            self._candidate.discard_candidate(key)
            self._candidate.close()
            self._candidate = None
            self._candidate_name = None
            self._cleanup()
        elif self._repo:
            self._repo.discard_candidate(key)
        elif self._candidate_name:
            self._candidate_name = None
            self._cleanup()

    def clear(self):
        with self._condition:
            self._blocked = True
            try:
                while self._readers:
                    self._condition.wait()
                self.settings.select(None)
                if self._repo:
                    self._retired.append(self._repo)
                self._repo = None
                self.incompatible = False
                self._cleanup()
                if self.cleanup_diagnostic:
                    raise StorageFailure(self.cleanup_diagnostic)
                self.settings.clear()
            finally:
                self._blocked = False

    def close(self):
        with self._condition:
            if self._readers:
                raise StorageFailure("Letture in corso")
            if self._candidate:
                self._candidate.close()
                self._candidate = None
                self._candidate_name = None
            self._cleanup()
            if self._repo:
                self._repo.close()
            self.settings.close()
