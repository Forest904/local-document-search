"""Dispatch esplicito per formato attraverso la porta reader esistente."""
from collections.abc import Mapping

from local_document_search.application.ports import (
    DocumentReaderPort, ExtractionFailed, FileCandidate, ReaderResult,
)
from local_document_search.domain.documents import DocumentFormat


class DocumentReader:
    def __init__(self, readers: Mapping[DocumentFormat, DocumentReaderPort]) -> None:
        self._readers = dict(readers)

    def read(self, candidate: FileCandidate) -> ReaderResult:
        reader = self._readers.get(candidate.metadata.format)
        if reader is None:
            return ExtractionFailed(f"Reader non registrato: {candidate.metadata.format}")
        return reader.read(candidate)
