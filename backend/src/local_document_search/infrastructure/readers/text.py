"""UTF-8 rigoroso, BOM iniziale ammesso, newline preservate."""
from pathlib import Path

from local_document_search.application.ports import Extracted, ExtractionFailed, FileCandidate
from local_document_search.domain.documents import CanonicalDocument


class TextReader:
    def read(self, candidate: FileCandidate) -> Extracted | ExtractionFailed:
        path = Path(candidate.root_directory) / candidate.metadata.relative_path.value
        try:
            content = path.read_bytes().decode("utf-8-sig", errors="strict")
            return Extracted(CanonicalDocument(candidate.metadata, content))
        except (OSError, UnicodeError) as exc:
            return ExtractionFailed(f"{candidate.metadata.relative_path.value}: {exc}")
