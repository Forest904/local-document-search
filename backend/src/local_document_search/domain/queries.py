"""Query interpretate, con testo preservato per analyzer distinti."""
from dataclasses import dataclass
from enum import StrEnum


class SearchField(StrEnum):
    FILENAME = "filename"
    CONTENT = "content"
    BOTH = "both"


@dataclass(frozen=True)
class TermsClause:
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Clausola vuota")


@dataclass(frozen=True)
class PhraseClause:
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Frase vuota")


type QueryClause = TermsClause | PhraseClause


@dataclass(frozen=True)
class SearchQuery:
    clauses: tuple[QueryClause, ...]
    field: SearchField = SearchField.BOTH

    def __post_init__(self) -> None:
        object.__setattr__(self, "clauses", tuple(self.clauses))
        if not self.clauses or not all(
            isinstance(c, (TermsClause, PhraseClause)) for c in self.clauses
        ):
            raise ValueError("Sono richieste clausole termini/frasi")
        if not isinstance(self.field, SearchField):
            raise ValueError("Campo non valido")
