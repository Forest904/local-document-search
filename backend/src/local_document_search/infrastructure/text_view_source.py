"""Lettura limitata del sorgente per il reader desktop, separata dal sync."""
from pathlib import Path
import os
import stat
import tempfile
import difflib

from local_document_search.application.contracts import TextRange
from local_document_search.application.text_view import TextViewDocument, SaveTextResult
from local_document_search.domain.documents import DocumentFormat
from local_document_search.infrastructure.filesystem import _is_link
from .markdown_provenance import project_first_match


MAX_BYTES = 10 * 1024 * 1024
MAX_LINES = 100_000
MAX_LINE_LENGTH = 100_000


class TextViewReadError(Exception):
    """Errore visibile nella pagina, non un errore del job di indicizzazione."""


class TextViewTooLarge(TextViewReadError):
    pass


class TextViewChangedDuringRead(TextViewReadError):
    pass


class TextViewEncodingError(TextViewReadError):
    pass


class TextViewUnavailable(TextViewReadError):
    pass


class TextViewMissing(TextViewReadError):
    pass


class TextViewPermission(TextViewReadError):
    pass


class TextViewUnsafePath(TextViewReadError):
    pass


class TextViewConflict(TextViewReadError):
    pass


def _line_endings(source):
    crlf = source.count("\r\n")
    cr = source.count("\r") - crlf
    lf = source.count("\n") - crlf
    if crlf and not cr and not lf:
        return "crlf"
    if cr and not crlf and not lf:
        return "cr"
    if lf and not crlf and not cr:
        return "lf"
    return "mixed" if crlf or cr or lf else "none"


def _check_lines(source):
    line_count = 1
    length = 0
    offset = 0
    while offset < len(source):
        char = source[offset]
        if char in "\r\n":
            if length > MAX_LINE_LENGTH or line_count >= MAX_LINES:
                raise TextViewTooLarge("Limite di righe superato")
            line_count += 1
            length = 0
            if char == "\r" and offset + 1 < len(source) and source[offset + 1] == "\n":
                offset += 1
        else:
            length += 1
            if length > MAX_LINE_LENGTH:
                raise TextViewTooLarge("Riga troppo lunga")
        offset += 1


class LocalTextViewSource:
    def prepare(self, request):
        path = Path(request.root_directory) / request.relative_path.value
        try:
            current = Path(request.root_directory).absolute()
            if any(_is_link(node.lstat()) for node in (current, *current.parents)):
                raise TextViewUnsafePath("Collegamenti non consentiti")
            for part in Path(request.relative_path.value).parts[:-1]:
                current = current / part
                if _is_link(current.lstat()):
                    raise TextViewUnsafePath("Collegamenti non consentiti")
            info = path.lstat()
            if _is_link(info) or not stat.S_ISREG(info.st_mode):
                raise TextViewUnsafePath("File non regolare o link")
            if info.st_size > MAX_BYTES:
                raise TextViewTooLarge("File oltre 10 MiB")
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_ino, opened.st_dev) != (info.st_ino, info.st_dev):
                    raise TextViewChangedDuringRead("Sorgente cambiata durante la lettura")
                data = stream.read(MAX_BYTES + 1)
                completed = os.fstat(stream.fileno())
            final = path.lstat()
            if len(data) > MAX_BYTES:
                raise TextViewTooLarge("File oltre 10 MiB")
            if (_is_link(final) or not stat.S_ISREG(final.st_mode) or
                    any((value.st_size, value.st_mtime_ns, value.st_ino, value.st_dev) !=
                        (info.st_size, info.st_mtime_ns, info.st_ino, info.st_dev)
                        for value in (opened, completed, final))):
                raise TextViewChangedDuringRead("Sorgente cambiata durante la lettura")
        except (TextViewReadError, MemoryError):
            raise
        except FileNotFoundError as exc:
            raise TextViewMissing("File non disponibile") from exc
        except PermissionError as exc:
            raise TextViewPermission("Permesso negato") from exc
        except OSError as exc:
            raise TextViewUnavailable("File non disponibile") from exc
        try:
            source = data.decode("utf-8-sig", errors="strict")
        except UnicodeError as exc:
            raise TextViewEncodingError("Il file non è UTF-8 valido") from exc
        _check_lines(source)
        target = request.target
        if target is None:
            status = "unavailable"
        elif (target.size_bytes, target.mtime_ns) != (info.st_size, info.st_mtime_ns):
            status = "changed"
        elif target.canonical_range is None:
            status = "filename"
        else:
            status = "ready"
        spans = ()
        if status == "ready":
            interval = target.canonical_range
            if request.format is DocumentFormat.TXT:
                if interval.end <= len(source):
                    spans = (interval,)
            else:
                projected = project_first_match(source, interval.start, interval.end)
                if projected is not None:
                    spans = tuple(TextRange(first, last) for first, last in projected)
            if not spans:
                status = "unavailable"
        return TextViewDocument(source, data.startswith(b"\xef\xbb\xbf"),
                                _line_endings(source), spans, status,
                                (info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino))

    def save(self, request):
        path = Path(request.root_directory) / request.relative_path.value
        current = Path(request.root_directory).absolute()
        try:
            if any(_is_link(node.lstat()) for node in (current, *current.parents)):
                raise TextViewUnsafePath("Collegamenti non consentiti")
            for part in Path(request.relative_path.value).parts[:-1]:
                current /= part
                if _is_link(current.lstat()):
                    raise TextViewUnsafePath("Collegamenti non consentiti")
            if path.suffix.lower() != (".txt" if request.format is DocumentFormat.TXT else ".md"):
                raise TextViewUnsafePath("Formato non corrispondente")
            original_lines = request.original_text.splitlines(keepends=True)
            edited_lines = request.text.splitlines(keepends=True)
            endings = [line[len(line.rstrip("\r\n")):] for line in original_lines if line.endswith(("\r", "\n"))]
            preferred = max(("\r\n", "\n", "\r"), key=lambda ending: (endings.count(ending), -len(ending))) if endings else "\n"
            before = [line.rstrip("\r\n") for line in original_lines]
            after = [line.rstrip("\r\n") for line in edited_lines]
            output = [None] * len(edited_lines)
            for tag, a, b, c, d in difflib.SequenceMatcher(None, before, after).get_opcodes():
                if tag == "equal":
                    output[c:d] = original_lines[a:b]
            for index, line in enumerate(edited_lines):
                if output[index] is None:
                    output[index] = line.rstrip("\r\n") + (preferred if line.endswith("\n") else "")
            source = "".join(output)
            _check_lines(source)
            data = (b"\xef\xbb\xbf" if request.bom else b"") + source.encode("utf-8", errors="strict")
            if len(data) > MAX_BYTES:
                raise TextViewTooLarge("File oltre 10 MiB")
            info = path.lstat()
            version = (info.st_size, info.st_mtime_ns, info.st_dev, info.st_ino)
            if _is_link(info) or not stat.S_ISREG(info.st_mode):
                raise TextViewUnsafePath("File non regolare o link")
            if version != request.source_version:
                raise TextViewConflict("Sorgente modificata esternamente")
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".lds-", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, stat.S_IMODE(info.st_mode))
                latest = path.lstat()
                if (latest.st_size, latest.st_mtime_ns, latest.st_dev, latest.st_ino) != version:
                    raise TextViewConflict("Sorgente modificata esternamente")
                os.replace(temporary, path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            saved = path.stat()
            return SaveTextResult((saved.st_size, saved.st_mtime_ns, saved.st_dev, saved.st_ino), source)
        except (TextViewReadError, UnicodeError, MemoryError):
            raise
        except FileNotFoundError as exc:
            raise TextViewMissing("File non disponibile") from exc
        except PermissionError as exc:
            raise TextViewPermission("Permesso negato") from exc
        except OSError as exc:
            raise TextViewUnavailable("File non disponibile") from exc
