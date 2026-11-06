"""Query interpretate, con testo preservato per analyzer distinti."""
from dataclasses import dataclass
from enum import StrEnum

from .analysis import ContentAnalyzer, FilenameAnalyzer
from .documents import DocumentId
from .index import PositionalIndex
from .snapshots import IndexSnapshot


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


def _analyze(query: SearchQuery) -> dict[SearchField, tuple[tuple[str, ...], ...]]:
    analyzed = {}
    for field, analyzer in (
        (SearchField.FILENAME, FilenameAnalyzer()),
        (SearchField.CONTENT, ContentAnalyzer()),
    ):
        if query.field not in (field, SearchField.BOTH):
            continue
        clauses = tuple(
            tuple(token.term for token in analyzer.analyze(clause.text))
            for clause in query.clauses
        )
        if any(not terms for terms in clauses):
            raise ValueError("Clausola senza token ricercabili")
        analyzed[field] = clauses
    return analyzed


class QueryParser:
    def parse(self, text: str, field: SearchField = SearchField.BOTH) -> SearchQuery:
        if text.count('"') % 2:
            raise ValueError("Virgolette sbilanciate")
        clauses: list[QueryClause] = []
        for i, part in enumerate(text.split('"')):
            if i % 2:
                clauses.append(PhraseClause(part))
            elif part.strip():
                clauses.append(TermsClause(part))
        query = SearchQuery(tuple(clauses), field)
        _analyze(query)
        return query


@dataclass(frozen=True)
class SearchMatch:
    document_id: DocumentId
    matched_fields: frozenset[SearchField]

    def __post_init__(self) -> None:
        object.__setattr__(self, "matched_fields", frozenset(self.matched_fields))
        if not self.matched_fields or any(
            field is not SearchField.FILENAME and field is not SearchField.CONTENT
            for field in self.matched_fields
        ):
            raise ValueError("Sono richiesti campi concreti")


class QueryEvaluator:
    def evaluate(self, query: SearchQuery, snapshot: IndexSnapshot) -> tuple[SearchMatch, ...]:
        if not isinstance(snapshot, IndexSnapshot):
            raise ValueError("La ricerca richiede uno snapshot immutabile")
        analyzed = _analyze(query)
        matches: dict[DocumentId, set[SearchField]] = {}
        for field, clauses in analyzed.items():
            index = snapshot.filename_index if field is SearchField.FILENAME else snapshot.content_index
            candidates: set[DocumentId] | None = None
            for clause, terms in zip(query.clauses, clauses):
                found = self._match_clause(index, terms, isinstance(clause, PhraseClause))
                candidates = found if candidates is None else candidates & found
                if not candidates:
                    break
            for document_id in candidates or ():
                matches.setdefault(document_id, set()).add(field)
        ordered = sorted(
            matches, key=lambda key: snapshot.catalog.documents[key].descriptor.metadata.relative_path.value,
        )
        return tuple(SearchMatch(key, frozenset(matches[key])) for key in ordered)

    @staticmethod
    def _match_clause(index: PositionalIndex, terms: tuple[str, ...], phrase: bool) -> set[DocumentId]:
        postings = [index.terms.get(term, {}) for term in terms]
        candidates = set(min(postings, key=len))
        for posting in postings:
            candidates.intersection_update(posting)
        if not phrase:
            return candidates
        matches = set()
        for document_id in candidates:
            starts = set(postings[0][document_id].positions)
            for offset, posting in enumerate(postings[1:], start=1):
                starts.intersection_update(position - offset for position in posting[document_id].positions)
                if not starts:
                    break
            if starts:
                matches.add(document_id)
        return matches
