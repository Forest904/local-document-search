"""Discovery multiformato ordinata senza attraversare link o reparse point."""
import os
from pathlib import Path
import stat

from local_document_search.application.contracts import InvalidInput
from local_document_search.application.errors import SourceUnavailable
from local_document_search.application.ports import FileCandidate
from local_document_search.domain.documents import (
    DocumentFormat, DocumentMetadata, FileFingerprint, RelativePath,
)


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def resolve_directory(directory: str) -> str:
    if not directory.strip():
        raise InvalidInput("Directory vuota")
    try:
        path = Path(directory).absolute()
        # Prima di resolve(), che nasconderebbe i link.
        if any(_is_link(part.lstat()) for part in (path, *path.parents)):
            raise InvalidInput("La directory non può attraversare link o reparse point")
        if not path.is_dir():
            raise InvalidInput("Il percorso non è una directory")
        return str(path.resolve(strict=True))
    except (OSError, ValueError) as exc:
        if isinstance(exc, InvalidInput):
            raise
        raise SourceUnavailable(f"Directory non disponibile: {directory}: {exc}") from exc


class DocumentFileDiscovery:
    formats = {f".{format.value}": format for format in DocumentFormat}

    def discover(self, root_directory: str) -> tuple[FileCandidate, ...]:
        root = Path(resolve_directory(root_directory))
        candidates = []
        pending = [root]
        try:
            while pending:
                with os.scandir(pending.pop()) as entries:
                    for entry in entries:
                        info = entry.stat(follow_symlinks=False)
                        if _is_link(info):
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            pending.append(Path(entry.path))
                        elif stat.S_ISREG(info.st_mode) and Path(entry.name).suffix.lower() in self.formats:
                            relative = Path(entry.path).relative_to(root).as_posix()
                            metadata = DocumentMetadata(
                                RelativePath(relative), entry.name, self.formats[Path(entry.name).suffix.lower()],
                                FileFingerprint(info.st_size, info.st_mtime_ns),
                            )
                            candidates.append(FileCandidate(str(root), metadata))
        except (OSError, ValueError) as exc:
            raise SourceUnavailable(f"Scansione fallita: {exc}") from exc
        return tuple(sorted(candidates, key=lambda item: item.metadata.relative_path.value))


class TextFileDiscovery(DocumentFileDiscovery):
    """Discovery TXT conservata per gli utilizzatori Homework 3."""
    formats = {".txt": DocumentFormat.TXT}
