"""Snapshot completi SQLite. Una sessione proprietaria, nessun accesso multiprocesso."""
from contextlib import contextmanager
from datetime import datetime
import os
from pathlib import Path
import sqlite3

from local_document_search.application.errors import ResourceFailure, SnapshotUnavailable, StorageFailure
from local_document_search.domain.documents import (
    DocumentDescriptor, DocumentFormat, DocumentId, DocumentMetadata, FileFingerprint,
    IndexedDocument, RelativePath,
)
from local_document_search.domain.index import PositionalIndex, Posting
from local_document_search.domain.snapshots import (
    DocumentCatalog, EntryOutcome, FileEntry, IndexManifest, IndexSnapshot,
)


SCHEMA = """
CREATE TABLE snapshots(id TEXT PRIMARY KEY, root TEXT NOT NULL, created TEXT NOT NULL,
                       schema_version TEXT NOT NULL, processing_version TEXT NOT NULL);
CREATE TABLE manifest(snapshot TEXT REFERENCES snapshots(id) ON DELETE CASCADE,
    path TEXT, filename TEXT NOT NULL, format TEXT NOT NULL, size INTEGER NOT NULL,
    mtime INTEGER NOT NULL, outcome TEXT NOT NULL, document_id INTEGER, reason TEXT,
    PRIMARY KEY(snapshot, path), UNIQUE(snapshot, document_id));
CREATE TABLE documents(snapshot TEXT, id INTEGER, text TEXT NOT NULL,
    filename_count INTEGER NOT NULL, content_count INTEGER NOT NULL,
    PRIMARY KEY(snapshot, id), FOREIGN KEY(snapshot, id)
    REFERENCES manifest(snapshot, document_id) ON DELETE CASCADE);
CREATE TABLE positions(snapshot TEXT, field TEXT CHECK(field IN ('filename', 'content')),
    term TEXT, document_id INTEGER, position INTEGER,
    PRIMARY KEY(snapshot, field, term, document_id, position),
    FOREIGN KEY(snapshot, document_id) REFERENCES documents(snapshot, id) ON DELETE CASCADE);
CREATE TABLE active(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    current TEXT REFERENCES snapshots(id), previous TEXT REFERENCES snapshots(id));
PRAGMA user_version=1;
"""


def storage_directory(directory=None, *, source_directory=None, repository_directory=None):
    """Risolve solo il percorso; nessuna creazione o cancellazione implicita."""
    if directory is None:
        if os.name != "nt" or not os.environ.get("LOCALAPPDATA"):
            raise StorageFailure("Directory applicativa esplicita richiesta")
        directory = Path(os.environ["LOCALAPPDATA"]) / "LocalDocumentSearch"
    target = Path(directory).resolve()
    forbidden = [Path(repository_directory).resolve()] if repository_directory else []
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            forbidden.append(parent)
            break
    if source_directory is not None:
        forbidden.append(Path(source_directory).resolve())
    if any(target.is_relative_to(root) for root in forbidden):
        raise StorageFailure("Storage dentro repository o directory indicizzata")
    return target


def _failure(exc):
    if isinstance(exc, MemoryError) or (isinstance(exc, sqlite3.Error)
            and getattr(exc, "sqlite_errorcode", 0) in (sqlite3.SQLITE_FULL, sqlite3.SQLITE_NOMEM)):
        return ResourceFailure("Risorse insufficienti nello storage")
    return StorageFailure("Lettura, scrittura o validazione dello storage fallita")


class SqliteSnapshotRepository:
    def __init__(self, directory=None, *, source_directory=None, database_name="snapshots.sqlite3"):
        self.directory = storage_directory(directory, source_directory=source_directory)
        self._db = None
        self._active = None
        self._candidate = None
        self._validated = False
        self._readers = {}
        self.cleanup_diagnostic = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            if Path(database_name).name != database_name:
                raise StorageFailure("Nome database non valido")
            self._db = sqlite3.connect(self.directory / database_name, isolation_level=None,
                                      check_same_thread=False)
            self._db.execute("PRAGMA foreign_keys=ON")
            version = self._db.execute("PRAGMA user_version").fetchone()[0]
            tables = self._db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if version != 1 and (version != 0 or tables):
                raise SnapshotUnavailable("Schema fisico incompatibile")
            self._db.execute("PRAGMA journal_mode=DELETE")
            self._db.execute("PRAGMA synchronous=FULL")
            if version == 0:
                self._db.executescript("BEGIN;" + SCHEMA + "COMMIT;")
            row = self._db.execute("SELECT current FROM active WHERE singleton=1").fetchone()
            if self._db.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Riferimenti persistiti non coerenti")
            has_snapshots = self._db.execute("SELECT 1 FROM snapshots LIMIT 1").fetchone()
            if (row is None and has_snapshots) or (row is not None and row[0] is None):
                raise ValueError("Riferimento attivo mancante")
            if row and row[0]:
                self._active = self._read(row[0])
            self._cleanup()
        except BaseException as exc:
            if self._db is not None:
                self._db.close()
                self._db = None
            if isinstance(exc, (sqlite3.Error, ValueError, TypeError, OSError, MemoryError)):
                raise _failure(exc) from exc
            raise

    def _connection(self):
        if self._db is None:
            raise StorageFailure("Repository chiuso")
        return self._db

    def load_active(self):
        self._connection()
        return self._active

    def _read(self, key):
        db = self._connection()
        row = db.execute("SELECT * FROM snapshots WHERE id=?", (key,)).fetchone()
        if row is None:
            raise SnapshotUnavailable("Snapshot non disponibile")
        if row[3:5] != ("1", "1"):
            raise SnapshotUnavailable("Versione snapshot incompatibile")
        entries, metadata = {}, {}
        for _, path, filename, fmt, size, mtime, outcome, doc_id, reason in db.execute(
                "SELECT * FROM manifest WHERE snapshot=?", (key,)):
            item = DocumentMetadata(RelativePath(path), filename, DocumentFormat(fmt),
                                    FileFingerprint(size, mtime))
            identity = DocumentId(doc_id) if doc_id is not None else None
            entries[item.relative_path] = FileEntry(item, EntryOutcome(outcome), identity, reason)
            if identity is not None:
                metadata[identity] = item
        documents = {}
        for _, doc_id, text, filename_count, content_count in db.execute(
                "SELECT * FROM documents WHERE snapshot=?", (key,)):
            identity = DocumentId(doc_id)
            if identity not in metadata:
                raise ValueError("Documento senza manifest")
            documents[identity] = IndexedDocument(DocumentDescriptor(identity, metadata[identity]),
                                                  text, filename_count, content_count)
        fields = {"filename": {}, "content": {}}
        for _, field, term, doc_id, position in db.execute(
                "SELECT * FROM positions WHERE snapshot=? ORDER BY position", (key,)):
            if field not in fields:
                raise ValueError("Campo sconosciuto")
            fields[field].setdefault(term, {}).setdefault(DocumentId(doc_id), []).append(position)
        indexes = [PositionalIndex({term: {doc: Posting(tuple(positions))
                   for doc, positions in postings.items()} for term, postings in fields[field].items()})
                   for field in ("filename", "content")]
        return IndexSnapshot(*row[:2], datetime.fromisoformat(row[2]), *row[3:],
                             IndexManifest(entries), DocumentCatalog(documents), *indexes)

    def save_candidate(self, snapshot):
        db = self._connection()
        if self._candidate is not None:
            raise StorageFailure("Un candidato è già in costruzione")
        storage_directory(self.directory, source_directory=snapshot.root_directory)
        if (snapshot.schema_version, snapshot.processing_version) != ("1", "1"):
            raise SnapshotUnavailable("Versione snapshot incompatibile")
        try:
            snapshot.__post_init__()
            db.execute("BEGIN IMMEDIATE")
            self._candidate = snapshot
            self._validated = False
            key = snapshot.snapshot_id
            db.execute("INSERT INTO snapshots VALUES (?,?,?,?,?)", (key, snapshot.root_directory,
                       snapshot.created_at.isoformat(), snapshot.schema_version, snapshot.processing_version))
            db.executemany("INSERT INTO manifest VALUES (?,?,?,?,?,?,?,?,?)", (
                (key, entry.metadata.relative_path.value, entry.metadata.filename,
                 entry.metadata.format.value, entry.metadata.fingerprint.size_bytes,
                 entry.metadata.fingerprint.mtime_ns, entry.outcome.value,
                 entry.document_id.value if entry.document_id is not None else None, entry.reason)
                for entry in snapshot.manifest.entries.values()))
            db.executemany("INSERT INTO documents VALUES (?,?,?,?,?)", (
                (key, identity.value, doc.extracted_text, doc.filename_token_count, doc.content_token_count)
                for identity, doc in snapshot.catalog.documents.items()))
            db.executemany("INSERT INTO positions VALUES (?,?,?,?,?)", (
                (key, field, term, identity.value, position)
                for field, index in (("filename", snapshot.filename_index), ("content", snapshot.content_index))
                for term, postings in index.terms.items() for identity, posting in postings.items()
                for position in posting.positions))
        except (sqlite3.Error, ValueError, MemoryError, OverflowError) as exc:
            self.discard_candidate(snapshot.snapshot_id)
            raise _failure(exc) from exc

    def _require_candidate(self, key):
        self._connection()
        if self._candidate is None or self._candidate.snapshot_id != key:
            raise StorageFailure("Candidato non disponibile")
        return self._candidate

    def validate_candidate(self, snapshot_id):
        candidate = self._require_candidate(snapshot_id)
        try:
            if self._connection().execute("PRAGMA foreign_key_check").fetchone() or self._read(snapshot_id) != candidate:
                raise ValueError("Round-trip candidato non coerente")
            self._validated = True
        except (sqlite3.Error, ValueError, TypeError, MemoryError) as exc:
            self._validated = False
            raise _failure(exc) from exc

    def _commit(self):
        self._connection().execute("COMMIT")

    def activate(self, snapshot_id):
        candidate = self._require_candidate(snapshot_id)
        if not self._validated:
            raise StorageFailure("Candidato non validato")
        previous = self._active.snapshot_id if self._active and self._active.root_directory == candidate.root_directory else None
        try:
            self._connection().execute("INSERT OR REPLACE INTO active VALUES (1,?,?)", (snapshot_id, previous))
            self._commit()
        except (sqlite3.Error, MemoryError) as exc:
            self.discard_candidate(snapshot_id)
            raise _failure(exc) from exc
        self._active = candidate
        self._candidate = None
        self._validated = False
        self._cleanup()

    def discard_candidate(self, snapshot_id):
        if self._candidate is not None and self._candidate.snapshot_id == snapshot_id:
            try:
                if self._connection().in_transaction:
                    self._connection().execute("ROLLBACK")
            except sqlite3.Error as exc:
                raise _failure(exc) from exc
            finally:
                self._candidate = None
                self._validated = False

    @contextmanager
    def acquire(self, snapshot_id=None):
        self._connection()
        key = snapshot_id if snapshot_id is not None else (self._active.snapshot_id if self._active else None)
        try:
            snapshot = self._active if self._active and self._active.snapshot_id == key else self._read(key)
            if self._active is None or snapshot.root_directory != self._active.root_directory:
                raise SnapshotUnavailable("Snapshot di directory non attiva")
            # Lo staging non è una versione acquisibile.
            if self._candidate is not None and key == self._candidate.snapshot_id:
                raise SnapshotUnavailable("Snapshot non pubblicato")
            self._readers[key] = self._readers.get(key, 0) + 1
        except (sqlite3.Error, ValueError, TypeError, MemoryError) as exc:
            raise _failure(exc) from exc
        try:
            yield snapshot
        finally:
            self._readers[key] -= 1
            if not self._readers[key]:
                del self._readers[key]
            self._cleanup()

    def _prune(self):
        db = self._connection()
        row = db.execute("SELECT current, previous FROM active WHERE singleton=1").fetchone()
        keep = set(row or ()) | {key for key, count in self._readers.items() if count}
        with db:
            db.execute("BEGIN IMMEDIATE")
            for (key,) in db.execute("SELECT id FROM snapshots").fetchall():
                if key not in keep:
                    db.execute("DELETE FROM snapshots WHERE id=?", (key,))

    def _cleanup(self):
        if self._candidate is not None:
            return
        try:
            self._prune()
            self.cleanup_diagnostic = None
        except (sqlite3.Error, OSError, MemoryError, StorageFailure):
            self.cleanup_diagnostic = "Pulizia snapshot da riprovare"

    def clear(self):
        db = self._connection()
        if self._candidate is not None or any(self._readers.values()):
            raise StorageFailure("Candidato o letture in corso")
        try:
            with db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("DELETE FROM active")
                db.execute("DELETE FROM snapshots")
            self._active = None
            self.cleanup_diagnostic = None
        except sqlite3.Error as exc:
            raise _failure(exc) from exc

    def close(self):
        if self._db is None:
            return
        if any(self._readers.values()):
            raise StorageFailure("Letture in corso")
        if self._candidate is not None:
            self.discard_candidate(self._candidate.snapshot_id)
        self._db.close()
        self._db = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
