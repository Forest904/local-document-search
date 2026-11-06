"""Posting e indici immutabili; IndexBuilder in snapshots costruisce il draft."""
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from .documents import DocumentId, require_nonnegative


@dataclass(frozen=True)
class Posting:
    positions: tuple[int, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", tuple(self.positions))
        if not self.positions:
            raise ValueError("Posting vuoto")
        for position in self.positions:
            require_nonnegative(position, "position")
        if any(a >= b for a, b in zip(self.positions, self.positions[1:])):
            raise ValueError("Posizioni non strettamente crescenti")


@dataclass(frozen=True)
class PositionalIndex:
    terms: Mapping[str, Mapping[DocumentId, Posting]]

    def __post_init__(self) -> None:
        frozen = {}
        for term, postings in self.terms.items():
            if not term.strip() or not postings:
                raise ValueError("Termine o lista posting vuoti")
            frozen[term] = MappingProxyType(dict(postings))
        object.__setattr__(self, "terms", MappingProxyType(frozen))
