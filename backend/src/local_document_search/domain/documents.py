"""Identità e documenti puri, senza accesso ai sorgenti."""
from dataclasses import dataclass
from enum import StrEnum


def require_nonnegative(value: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} deve essere un intero non negativo")


@dataclass(frozen=True)
class DocumentId:
    value: int

    def __post_init__(self) -> None:
        require_nonnegative(self.value, "document_id")


@dataclass(frozen=True)
class RelativePath:
    value: str

    def __post_init__(self) -> None:
        if any(p in ("", ".", "..") for p in self.value.split("/")) or any(
            c in self.value for c in (chr(92), ":", chr(0))
        ):
            raise ValueError("Percorso relativo richiesto, con separatori /")


class DocumentFormat(StrEnum):
    TXT = "txt"
    MARKDOWN = "md"
    PDF = "pdf"


@dataclass(frozen=True)
class FileFingerprint:
    size_bytes: int
    mtime_ns: int

    def __post_init__(self) -> None:
        require_nonnegative(self.size_bytes, "size_bytes")
        # Timestamp anteriori all'epoch sono validi.
        if type(self.mtime_ns) is not int:
            raise ValueError("mtime_ns deve essere un intero")


@dataclass(frozen=True)
class DocumentMetadata:
    relative_path: RelativePath
    filename: str
    format: DocumentFormat
    fingerprint: FileFingerprint

    def __post_init__(self) -> None:
        if self.filename != self.relative_path.value.rsplit("/", 1)[-1]:
            raise ValueError("filename non coerente con relative_path")
        if not isinstance(self.format, DocumentFormat):
            raise ValueError("Formato non valido")


@dataclass(frozen=True)
class DocumentDescriptor:
    document_id: DocumentId
    metadata: DocumentMetadata


@dataclass(frozen=True)
class PdfPageSpan:
    start: int
    end: int

    def __post_init__(self) -> None:
        require_nonnegative(self.start, "page_start")
        require_nonnegative(self.end, "page_end")
        if self.end < self.start:
            raise ValueError("Intervallo pagina non valido")


def validate_pdf_pages(metadata, content, pages):
    if pages is None:
        return
    if metadata.format is not DocumentFormat.PDF or not pages:
        raise ValueError("Mappa pagine non valida per il formato")
    cursor = 0
    for number, span in enumerate(pages):
        if not isinstance(span, PdfPageSpan) or span.start != cursor or span.end > len(content):
            raise ValueError("Intervalli delle pagine non coerenti")
        cursor = span.end
        if number < len(pages) - 1:
            if cursor >= len(content) or content[cursor] != "\n":
                raise ValueError("Separatore PDF mancante")
            cursor += 1
    if cursor != len(content):
        raise ValueError("Mappa pagine incompleta")


@dataclass(frozen=True)
class CanonicalDocument:
    metadata: DocumentMetadata
    content: str
    pdf_pages: tuple[PdfPageSpan, ...] | None = None

    def __post_init__(self) -> None:
        if self.pdf_pages is not None:
            object.__setattr__(self, "pdf_pages", tuple(self.pdf_pages))
        validate_pdf_pages(self.metadata, self.content, self.pdf_pages)


@dataclass(frozen=True)
class IndexedDocument:
    descriptor: DocumentDescriptor
    extracted_text: str
    filename_token_count: int
    content_token_count: int
    pdf_pages: tuple[PdfPageSpan, ...] | None = None

    def __post_init__(self) -> None:
        require_nonnegative(self.filename_token_count, "filename_token_count")
        require_nonnegative(self.content_token_count, "content_token_count")
        if self.pdf_pages is not None:
            object.__setattr__(self, "pdf_pages", tuple(self.pdf_pages))
        validate_pdf_pages(self.descriptor.metadata, self.extracted_text, self.pdf_pages)
