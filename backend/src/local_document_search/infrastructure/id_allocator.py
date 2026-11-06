"""Contatore durevole, indipendente dalla retention degli snapshot."""
import sqlite3

from local_document_search.application.errors import StorageFailure


class SqliteDocumentIdAllocator:
    def __init__(self, directory, *, existing_data=False):
        path = directory / "document-ids.sqlite3"
        self._path = path
        if not path.exists() and existing_data:
            self._db = None
            self.legacy = True
            return
        self.legacy = False
        try:
            self._db = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
            self._db.execute("PRAGMA synchronous=FULL")
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0 and not self._db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table'").fetchone():
                if existing_data:
                    raise StorageFailure("Allocatore documentale incompleto")
                self._db.executescript("BEGIN; CREATE TABLE counter (singleton INTEGER PRIMARY KEY "
                                       "CHECK(singleton=1), next_id INTEGER NOT NULL); "
                                       "INSERT INTO counter VALUES (1,0); PRAGMA user_version=1; COMMIT;")
            elif version != 1:
                raise StorageFailure("Allocatore documentale incompatibile")
            row = self._db.execute("SELECT next_id FROM counter WHERE singleton=1").fetchone()
            if row is None or type(row[0]) is not int or row[0] < 0:
                raise StorageFailure("Allocatore documentale corrotto")
        except BaseException as exc:
            if self._db is not None:
                self._db.close()
                self._db = None
            if isinstance(exc, sqlite3.Error):
                raise StorageFailure("Allocatore documentale non disponibile") from exc
            raise

    def reserve_document_ids(self, count):
        if self.legacy:
            raise StorageFailure("Dati precedenti: eseguire Elimina dati locali prima della sincronizzazione")
        if type(count) is not int or count < 0:
            raise ValueError("Numero di ID non valido")
        try:
            with self._db:
                self._db.execute("BEGIN IMMEDIATE")
                start = self._db.execute("SELECT next_id FROM counter WHERE singleton=1").fetchone()[0]
                self._db.execute("UPDATE counter SET next_id=? WHERE singleton=1", (start + count,))
            return start
        except sqlite3.Error as exc:
            raise StorageFailure("Prenotazione ID fallita") from exc

    def reset(self):
        if self.legacy:
            self._db = sqlite3.connect(self._path, isolation_level=None, check_same_thread=False)
            self._db.execute("PRAGMA synchronous=FULL")
            self._db.executescript("BEGIN; CREATE TABLE counter (singleton INTEGER PRIMARY KEY "
                                   "CHECK(singleton=1), next_id INTEGER NOT NULL); "
                                   "INSERT INTO counter VALUES (1,0); PRAGMA user_version=1; COMMIT;")
            self.legacy = False
        else:
            with self._db:
                self._db.execute("BEGIN IMMEDIATE")
                self._db.execute("UPDATE counter SET next_id=0 WHERE singleton=1")

    def close(self):
        if self._db is not None:
            self._db.close()
