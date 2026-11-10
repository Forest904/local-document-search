"""Testo PDF in ordine di pagina, senza OCR né richiesta di password."""
from pathlib import Path

from pypdf import PdfReader as Parser

from local_document_search.application.ports import (
    Extracted, Excluded, ExtractionFailed, FileCandidate, ReaderResult,
)
from local_document_search.domain.documents import CanonicalDocument, PdfPageSpan


class PdfReader:
    def read(self, candidate: FileCandidate) -> ReaderResult:
        path = Path(candidate.root_directory) / candidate.metadata.relative_path.value
        try:
            with path.open("rb") as stream:
                reader = Parser(stream)
                if reader.is_encrypted and not reader.decrypt(""):
                    return ExtractionFailed(f"{candidate.metadata.relative_path.value}: password necessaria")
                parts = [page.extract_text() or "" for page in reader.pages]
                content = "\n".join(parts)
            if not content.strip():
                return Excluded("PDF senza testo estraibile non-whitespace")
            pages = []
            offset = 0
            for part in parts:
                pages.append(PdfPageSpan(offset, offset + len(part)))
                offset += len(part) + 1
            return Extracted(CanonicalDocument(candidate.metadata, content, tuple(pages)))
        except MemoryError:
            raise
        except Exception as exc:
            return ExtractionFailed(f"{candidate.metadata.relative_path.value}: {exc}")
