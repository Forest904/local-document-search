"""Testo Markdown dai token CommonMark, senza rendering o accessi esterni."""
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from local_document_search.application.ports import Extracted, ExtractionFailed, FileCandidate
from local_document_search.domain.documents import CanonicalDocument


def _without_front_matter(source: str) -> str:
    lines = source.splitlines(keepends=True)
    if lines and lines[0].rstrip("\r\n") == "---":
        for index, line in enumerate(lines[1:], 1):
            if line.rstrip("\r\n") == "---":
                return "".join(lines[index + 1:])
    return source


def _text(tokens: list[Token]) -> str:
    parts = []
    for token in tokens:
        if token.type in ("text", "code_inline"):
            parts.append(token.content)
        elif token.type in ("inline", "image"):
            parts.append(_text(token.children or []))
        elif token.block or token.type in ("softbreak", "hardbreak", "html_inline"):
            parts.append("\n")
    return "".join(parts)


class MarkdownReader:
    def __init__(self) -> None:
        self._parser = MarkdownIt("commonmark").enable("table")

    def read(self, candidate: FileCandidate) -> Extracted | ExtractionFailed:
        path = Path(candidate.root_directory) / candidate.metadata.relative_path.value
        try:
            source = path.read_bytes().decode("utf-8-sig", errors="strict")
            content = _text(self._parser.parse(_without_front_matter(source)))
            return Extracted(CanonicalDocument(candidate.metadata, content))
        except MemoryError:
            raise
        except Exception as exc:
            return ExtractionFailed(f"{candidate.metadata.relative_path.value}: {exc}")
