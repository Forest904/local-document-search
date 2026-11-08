"""Catalogo di controllo stabile: settings e selezione atomica del database dati."""
from datetime import datetime
import sqlite3
from threading import RLock

from local_document_search.application.ports import Settings, LastCheck, SyncOutcome
from local_document_search.application.errors import StorageFailure
from local_document_search.application.preferences import DesktopPreferences
from .sqlite_snapshot_storage import storage_directory, _failure


class SqliteSettingsRepository:
    def __init__(self, directory, *, database_name="control.sqlite3", legacy_detection=True):
        self.directory = storage_directory(directory)
        self.lock = RLock()
        self.db = None
        self.desktop_preferences = database_name == "control-v2.sqlite3"
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(self.directory / database_name, isolation_level=None,
                                      check_same_thread=False)
            self.db.execute("PRAGMA synchronous=FULL")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise StorageFailure("Catalogo di controllo incompatibile")
            self.db.executescript("""BEGIN;
                CREATE TABLE IF NOT EXISTS settings(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    root TEXT, checked TEXT, outcome TEXT, diagnostic TEXT);
                CREATE TABLE IF NOT EXISTS selection(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS owned(name TEXT PRIMARY KEY);
                PRAGMA user_version=1;
                COMMIT;""")
            if self.desktop_preferences:
                self.db.execute("""CREATE TABLE IF NOT EXISTS desktop_preferences(
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    language TEXT NOT NULL, theme TEXT NOT NULL)""")
            if (legacy_detection and self.selected() is None and (self.directory / "snapshots.sqlite3").exists()
                    and not self.db.execute("SELECT 1 FROM settings").fetchone()
                    and not self.db.execute("SELECT 1 FROM owned WHERE name='snapshots.sqlite3'").fetchone()):
                with self.db:
                    self.db.execute("BEGIN IMMEDIATE")
                    self.db.execute("INSERT INTO selection VALUES (1,'snapshots.sqlite3')")
                    self.db.execute("INSERT INTO owned VALUES ('snapshots.sqlite3')")
        except BaseException as exc:
            if self.db is not None:
                self.db.close()
            if isinstance(exc, (sqlite3.Error, OSError, MemoryError)):
                raise _failure(exc) from exc
            raise

    def load(self):
        with self.lock:
            try:
                row = self.db.execute("SELECT root,checked,outcome,diagnostic FROM settings").fetchone()
                if row is None:
                    return Settings()
                check = LastCheck(datetime.fromisoformat(row[1]), SyncOutcome(row[2]), row[3]) if row[1] else None
                return Settings(row[0], check)
            except (sqlite3.Error, ValueError) as exc:
                raise _failure(exc) from exc

    def save(self, settings):
        with self.lock:
            check = settings.last_check
            try:
                self.db.execute("INSERT OR REPLACE INTO settings VALUES (1,?,?,?,?)", (
                    settings.active_directory, check.checked_at.isoformat() if check else None,
                    check.outcome.value if check else None, check.diagnostic if check else None))
            except sqlite3.Error as exc:
                raise _failure(exc) from exc

    def clear(self):
        with self.lock:
            try:
                with self.db:
                    self.db.execute("BEGIN IMMEDIATE")
                    self.db.execute("DELETE FROM settings")
                    if self.desktop_preferences:
                        self.db.execute("DELETE FROM desktop_preferences")
            except sqlite3.Error as exc:
                raise _failure(exc) from exc

    def load_preferences(self):
        with self.lock:
            try:
                row = self.db.execute("SELECT language,theme FROM desktop_preferences WHERE singleton=1").fetchone()
                return DesktopPreferences(*row) if row else DesktopPreferences()
            except (sqlite3.Error, ValueError) as exc:
                raise _failure(exc) from exc

    def save_preferences(self, value):
        with self.lock:
            try:
                self.db.execute("INSERT OR REPLACE INTO desktop_preferences VALUES (1,?,?)",
                                (value.language, value.theme))
            except sqlite3.Error as exc:
                raise _failure(exc) from exc

    def selected(self):
        with self.lock:
            row = self.db.execute("SELECT name FROM selection WHERE singleton=1").fetchone()
            return row[0] if row else None

    def select(self, name):
        with self.lock:
            try:
                with self.db:
                    self.db.execute("BEGIN IMMEDIATE")
                    self.db.execute("DELETE FROM selection")
                    if name is not None:
                        self.db.execute("INSERT INTO selection VALUES (1,?)", (name,))
            except sqlite3.Error as exc:
                raise _failure(exc) from exc

    def close(self):
        with self.lock:
            self.db.close()
