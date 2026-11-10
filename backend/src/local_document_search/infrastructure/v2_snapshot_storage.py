"""Storage v2: manifest di snapshot e contenuti immutabili condivisi."""
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from threading import RLock
import zlib

from local_document_search.application.errors import SnapshotUnavailable, StorageFailure
from local_document_search.domain.documents import (
    DocumentDescriptor, DocumentFormat, DocumentId, DocumentMetadata,
    FileFingerprint, IndexedDocument, PdfPageSpan, RelativePath,
)
from local_document_search.domain.index import PositionalIndex, Posting
from local_document_search.domain.snapshots import (
    DocumentCatalog, EntryOutcome, FileEntry, IndexManifest, IndexSnapshot,
)
from .sqlite_snapshot_storage import _failure, storage_directory


SCHEMA = """
CREATE TABLE snapshots(id TEXT PRIMARY KEY, root TEXT NOT NULL, created TEXT NOT NULL,
    schema_version TEXT NOT NULL, processing_version TEXT NOT NULL);
CREATE TABLE versions(id TEXT PRIMARY KEY, text TEXT NOT NULL, filename_count INTEGER NOT NULL,
    content_count INTEGER NOT NULL, filename_blob BLOB NOT NULL, content_blob BLOB NOT NULL,
    pdf_pages TEXT);
CREATE TABLE manifest(snapshot TEXT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    path TEXT NOT NULL, filename TEXT NOT NULL, format TEXT NOT NULL, size INTEGER NOT NULL,
    mtime INTEGER NOT NULL, outcome TEXT NOT NULL, document_id INTEGER, reason TEXT,
    version TEXT REFERENCES versions(id), PRIMARY KEY(snapshot,path));
CREATE TABLE active(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    current TEXT REFERENCES snapshots(id), previous TEXT REFERENCES snapshots(id));
PRAGMA user_version=3;
"""

SCHEMA_VERSION = "3"
PROCESSING_VERSION = "1"


def _encode_pages(pages):
    return json.dumps([[span.start, span.end] for span in pages], separators=(",", ":")) if pages is not None else None


def _decode_pages(value):
    if value is None:
        return None
    try:
        pairs = json.loads(value)
        if not isinstance(pairs, list) or any(not isinstance(p, list) or len(p) != 2 for p in pairs):
            raise ValueError("Mappa PDF non valida")
        return tuple(PdfPageSpan(*p) for p in pairs)
    except (ValueError, TypeError) as exc:
        raise StorageFailure("Mappa PDF danneggiata") from exc


def _encode(postings):
    values = [[term, list(posting.positions)] for term, posting in sorted(postings.items())]
    return zlib.compress(json.dumps(values, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8"), level=1)


def _decode(blob, expected_count):
    try:
        values = json.loads(zlib.decompress(blob).decode("utf-8"))
        if not isinstance(values, list) or any(
                not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], str)
                or not isinstance(item[1], list) for item in values):
            raise ValueError("Blocco posting non valido")
        postings = {term: Posting(tuple(positions)) for term, positions in values}
        if len(postings) != len(values) or sum(len(p.positions) for p in postings.values()) != expected_count:
            raise ValueError("Conteggio posting non coerente")
        return postings
    except (zlib.error, UnicodeError, ValueError, TypeError, KeyError) as exc:
        raise StorageFailure("Blocco posting danneggiato") from exc


def _digest_record(digest, record):
    for value in record:
        if value is None:
            digest.update(b"N")
            continue
        if isinstance(value, bytes):
            kind, data = b"B", value
        elif isinstance(value, int):
            kind, data = b"I", str(value).encode("ascii")
        else:
            kind, data = b"S", value.encode("utf-8")
        digest.update(kind)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)


class V2SqliteSnapshotRepository:
    """Un writer; le letture acquisiscono snapshot completi e immutabili."""

    def __init__(self, directory, *, database_name="snapshots-v2.sqlite3"):
        self.directory = storage_directory(directory)
        self._lock = RLock()
        self._db = None
        self._active = None
        self._versions = {}
        self._readers = {}
        self._candidate = None
        self._validated = False
        self._candidate_digest = None
        self._previous = None
        self.recovery_needed = False
        self.cleanup_diagnostic = None
        self._cleanup_needed = True
        try:
            if Path(database_name).name != database_name:
                raise StorageFailure("Nome database non valido")
            self.directory.mkdir(parents=True, exist_ok=True)
            database = self.directory / database_name
            if database.exists():
                probe = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
                try:
                    version = probe.execute("PRAGMA user_version").fetchone()[0]
                    tables = probe.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                    if version != 3 and (version != 0 or tables):
                        raise SnapshotUnavailable("Schema v2 incompatibile")
                finally:
                    probe.close()
            self._db = sqlite3.connect(database, isolation_level=None, check_same_thread=False)
            self._db.execute("PRAGMA foreign_keys=ON")
            self._db.execute("PRAGMA journal_mode=DELETE")
            self._db.execute("PRAGMA synchronous=FULL")
            if self._db.execute("PRAGMA user_version").fetchone()[0] == 0:
                self._db.executescript("BEGIN;" + SCHEMA + "COMMIT;")
            if self._db.execute("PRAGMA foreign_key_check").fetchone():
                raise StorageFailure("Riferimenti persistiti non coerenti")
            row = self._db.execute("SELECT current,previous FROM active WHERE singleton=1").fetchone()
            if row:
                self._previous = row[1]
                try:
                    self._active = self._read(row[0])
                    self._versions[row[0]] = self._active
                except (StorageFailure, SnapshotUnavailable):
                    self.recovery_needed = True
            elif self._db.execute("SELECT 1 FROM snapshots LIMIT 1").fetchone():
                raise StorageFailure("Riferimento attivo assente")
            self._cleanup()
        except BaseException as exc:
            if self._db is not None:
                self._db.close()
            if isinstance(exc, (sqlite3.Error, OSError, ValueError, MemoryError)):
                raise _failure(exc) from exc
            raise

    def _read(self, key):
        db = self._db
        row = db.execute("SELECT root,created,schema_version,processing_version FROM snapshots WHERE id=?",
                         (key,)).fetchone()
        if row is None or row[2:] != (SCHEMA_VERSION, PROCESSING_VERSION):
            raise SnapshotUnavailable("Snapshot v2 incompatibile o assente")
        entries, documents = {}, {}
        fields = {"filename": {}, "content": {}}
        for (path, filename, fmt, size, mtime, outcome, doc_id, reason, version,
             text, filename_count, content_count, filename_blob, content_blob, pdf_pages) in db.execute(
                "SELECT m.path,m.filename,m.format,m.size,m.mtime,m.outcome,m.document_id,"
                "m.reason,m.version,v.text,v.filename_count,v.content_count,"
                "v.filename_blob,v.content_blob,v.pdf_pages FROM manifest AS m "
                "LEFT JOIN versions AS v ON v.id=m.version WHERE m.snapshot=?", (key,)):
            metadata = DocumentMetadata(RelativePath(path), filename, DocumentFormat(fmt),
                                        FileFingerprint(size, mtime))
            identity = DocumentId(doc_id) if doc_id is not None else None
            entries[metadata.relative_path] = FileEntry(metadata, EntryOutcome(outcome), identity, reason)
            if identity is None:
                if version is not None:
                    raise StorageFailure("Esclusione con versione persistita")
                continue
            if text is None or identity in documents:
                raise StorageFailure("Versione documento mancante o ripetuta")
            if metadata.format is DocumentFormat.PDF and pdf_pages is None:
                raise StorageFailure("Mappa PDF mancante")
            try:
                documents[identity] = IndexedDocument(DocumentDescriptor(identity, metadata),
                                                      text, filename_count, content_count, _decode_pages(pdf_pages))
            except (ValueError, TypeError) as exc:
                raise StorageFailure("Mappa PDF danneggiata") from exc
            for field, blob, count in (("filename", filename_blob, filename_count),
                                       ("content", content_blob, content_count)):
                for term, posting in _decode(blob, count).items():
                    fields[field].setdefault(term, {})[identity] = posting
        try:
            return IndexSnapshot(key, row[0], datetime.fromisoformat(row[1]), *row[2:],
                                 IndexManifest(entries), DocumentCatalog(documents),
                                 PositionalIndex(fields["filename"]), PositionalIndex(fields["content"]))
        except (ValueError, TypeError) as exc:
            raise StorageFailure("Snapshot v2 danneggiato") from exc

    def load_active(self):
        with self._lock:
            return self._active

    @contextmanager
    def acquire(self, snapshot_id=None):
        with self._lock:
            key = snapshot_id or (self._active.snapshot_id if self._active else None)
            if key not in self._versions and key == self._previous:
                self._versions[key] = self._read(key)
            snapshot = self._versions.get(key)
            if self._active is None or snapshot is None or snapshot.root_directory != self._active.root_directory:
                raise SnapshotUnavailable("Snapshot non disponibile")
            self._readers[key] = self._readers.get(key, 0) + 1
        try:
            yield snapshot
        finally:
            with self._lock:
                self._readers[key] -= 1
                if self._readers[key] == 0:
                    del self._readers[key]
                if key not in (self._active.snapshot_id, self._previous):
                    self._cleanup_needed = True
                    self._cleanup()

    def save_candidate(self, snapshot):
        with self._lock:
            if self._candidate is not None:
                raise StorageFailure("Candidato già presente")
            if (snapshot.schema_version, snapshot.processing_version) != (SCHEMA_VERSION, PROCESSING_VERSION):
                raise SnapshotUnavailable("Versione snapshot incompatibile")
            if any(doc.descriptor.metadata.format is DocumentFormat.PDF and doc.pdf_pages is None
                   for doc in snapshot.catalog.documents.values()):
                raise StorageFailure("Mappa PDF mancante")
            db = self._db
            try:
                db.execute("BEGIN IMMEDIATE")
                self._candidate = snapshot
                self._validated = False
                db.execute("INSERT INTO snapshots VALUES (?,?,?,?,?)",
                           (snapshot.snapshot_id, snapshot.root_directory,
                            snapshot.created_at.isoformat(), SCHEMA_VERSION, PROCESSING_VERSION))
                old_versions = {}
                if self._active and self._active.root_directory == snapshot.root_directory:
                    old_versions = {p: (v, s, m) for p, v, s, m in db.execute(
                        "SELECT path,version,size,mtime FROM manifest WHERE snapshot=?",
                        (self._active.snapshot_id,))}
                changed = {}
                manifest_rows = []
                for path, entry in snapshot.manifest.entries.items():
                    version = None
                    if entry.document_id is not None:
                        old = old_versions.get(path.value)
                        if (old and old[0] is not None and old[1:] == (
                                entry.metadata.fingerprint.size_bytes,
                                entry.metadata.fingerprint.mtime_ns)
                                and self._active.manifest.entries[path].document_id == entry.document_id
                                and self._active.catalog.documents[entry.document_id]
                                == snapshot.catalog.documents[entry.document_id]):
                            version = old[0]
                        else:
                            version = f"{snapshot.snapshot_id}:{entry.document_id.value}"
                            changed[entry.document_id] = version
                    manifest_rows.append((
                        snapshot.snapshot_id, path.value, entry.metadata.filename,
                        entry.metadata.format.value, entry.metadata.fingerprint.size_bytes,
                        entry.metadata.fingerprint.mtime_ns, entry.outcome.value,
                        entry.document_id.value if entry.document_id else None, entry.reason, version))
                postings = {identity: [{}, {}] for identity in changed}
                for field_number, index in enumerate((snapshot.filename_index, snapshot.content_index)):
                    for term, docs in index.terms.items():
                        for identity, posting in docs.items():
                            if identity in postings:
                                postings[identity][field_number][term] = posting
                digest = hashlib.sha256()
                for row_values in sorted(manifest_rows, key=lambda row: row[1]):
                    _digest_record(digest, row_values)
                for identity, version in sorted(changed.items(), key=lambda item: item[1]):
                    doc = snapshot.catalog.documents[identity]
                    version_row = (
                        version, doc.extracted_text, doc.filename_token_count,
                        doc.content_token_count, _encode(postings[identity][0]),
                        _encode(postings[identity][1]), _encode_pages(doc.pdf_pages))
                    db.execute("INSERT INTO versions VALUES (?,?,?,?,?,?,?)", version_row)
                    _digest_record(digest, version_row)
                    del postings[identity]
                db.executemany("INSERT INTO manifest VALUES (?,?,?,?,?,?,?,?,?,?)", manifest_rows)
                self._candidate_digest = digest.digest()
            except (sqlite3.Error, ValueError, MemoryError, TypeError) as exc:
                self.discard_candidate(snapshot.snapshot_id)
                raise _failure(exc) from exc

    def validate_candidate(self, snapshot_id):
        with self._lock:
            if self._candidate is None or self._candidate.snapshot_id != snapshot_id:
                raise StorageFailure("Candidato assente")
            if self._db.execute("PRAGMA foreign_key_check").fetchone():
                raise StorageFailure("Candidato non coerente")
            digest = hashlib.sha256()
            for row_values in self._db.execute(
                    "SELECT snapshot,path,filename,format,size,mtime,outcome,document_id,reason,version "
                    "FROM manifest WHERE snapshot=? ORDER BY path", (snapshot_id,)):
                _digest_record(digest, row_values)
            for row_values in self._db.execute(
                    "SELECT id,text,filename_count,content_count,filename_blob,content_blob,pdf_pages "
                    "FROM versions WHERE id LIKE ? ORDER BY id", (snapshot_id + ":%",)):
                _digest_record(digest, row_values)
            if digest.digest() != self._candidate_digest:
                raise StorageFailure("Round-trip candidato non coerente")
            self._validated = True

    def activate(self, snapshot_id):
        with self._lock:
            candidate = self._candidate
            if candidate is None or candidate.snapshot_id != snapshot_id or not self._validated:
                raise StorageFailure("Candidato non validato")
            previous = (self._active.snapshot_id if self._active and
                        self._active.root_directory == candidate.root_directory else None)
            try:
                self._db.execute("INSERT OR REPLACE INTO active VALUES (1,?,?)", (snapshot_id, previous))
                self._commit()
            except sqlite3.Error as exc:
                self.discard_candidate(snapshot_id)
                raise _failure(exc) from exc
            self._active = candidate
            self._versions[snapshot_id] = candidate
            self._previous = previous
            self._candidate = None
            self._validated = False
            self._candidate_digest = None
            self._cleanup_needed = True
            self.recovery_needed = False
            self._cleanup()

    def _commit(self):
        self._db.execute("COMMIT")

    def discard_candidate(self, snapshot_id):
        with self._lock:
            if self._candidate is not None and self._candidate.snapshot_id == snapshot_id:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
                self._candidate = None
                self._validated = False
                self._candidate_digest = None

    def _cleanup(self):
        if self._candidate is not None or self.recovery_needed or not self._cleanup_needed:
            return
        try:
            keep = {self._active.snapshot_id if self._active else None, self._previous, *self._readers}
            self._db.execute("BEGIN IMMEDIATE")
            for (key,) in self._db.execute("SELECT id FROM snapshots").fetchall():
                if key not in keep:
                    self._db.execute("DELETE FROM snapshots WHERE id=?", (key,))
            self._db.execute("DELETE FROM versions WHERE id NOT IN "
                             "(SELECT DISTINCT version FROM manifest WHERE version IS NOT NULL)")
            self._db.execute("COMMIT")
            self._versions = {k: v for k, v in self._versions.items() if k in keep}
            self.cleanup_diagnostic = None
            self._cleanup_needed = False
        except sqlite3.Error:
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            self.cleanup_diagnostic = "Pulizia snapshot v2 da riprovare"

    def clear(self):
        with self._lock:
            if self._candidate or self._readers:
                raise StorageFailure("Candidato o letture in corso")
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute("DELETE FROM active")
                self._db.execute("DELETE FROM snapshots")
                self._db.execute("DELETE FROM versions")
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
            self._active = None
            self._previous = None
            self._versions.clear()
            self.recovery_needed = False

    def recover_previous(self, expected_root):
        with self._lock:
            if not self.recovery_needed or self._previous is None or self._candidate is not None:
                raise SnapshotUnavailable("Precedente da recuperare non disponibile")
            recovered = self._read(self._previous)
            current_root = self._db.execute(
                "SELECT root FROM snapshots WHERE id=(SELECT current FROM active WHERE singleton=1)"
            ).fetchone()
            if (recovered.root_directory != expected_root or current_root is None
                    or current_root[0] != expected_root):
                raise SnapshotUnavailable("Directory del precedente non coerente")
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute("UPDATE active SET current=?,previous=NULL WHERE singleton=1",
                                 (self._previous,))
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
            self._active = recovered
            self._versions[recovered.snapshot_id] = recovered
            self._previous = None
            self.recovery_needed = False
            self._cleanup_needed = True
            self._cleanup()
            return recovered.snapshot_id

    def close(self):
        with self._lock:
            if self._readers:
                raise StorageFailure("Letture in corso")
            if self._candidate:
                self.discard_candidate(self._candidate.snapshot_id)
            self._db.close()
