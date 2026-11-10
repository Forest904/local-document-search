"""Query interpretate, con testo preservato per analyzer distinti."""
from dataclasses import dataclass
from enum import StrEnum
import re
import unicodedata

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


@dataclass(frozen=True)
class PrefixClause:
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Prefisso vuoto")


@dataclass(frozen=True)
class SuffixClause:
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Suffisso vuoto")


type QueryClause = TermsClause | PhraseClause | PrefixClause | SuffixClause


@dataclass(frozen=True)
class SearchQuery:
    clauses: tuple[QueryClause, ...]
    field: SearchField = SearchField.BOTH

    def __post_init__(self) -> None:
        object.__setattr__(self, "clauses", tuple(self.clauses))
        if not self.clauses or not all(
            isinstance(c, (TermsClause, PhraseClause, PrefixClause, SuffixClause)) for c in self.clauses
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
        clauses = tuple(tuple(token.term for token in analyzer.analyze(clause.text))
                        for clause in query.clauses)
        if any(not terms for terms in clauses):
            raise ValueError("Clausola senza token ricercabili")
        if any(isinstance(clause, (PrefixClause, SuffixClause)) and
               (len(terms) != 1 or len(terms[0]) < 2)
               for clause, terms in zip(query.clauses, clauses)):
            raise ValueError("Wildcard: un solo token di almeno due caratteri")
        analyzed[field] = clauses
    return analyzed


class QueryParser:
    def parse(self, text: str, field: SearchField = SearchField.BOTH,
              allow_wildcards: bool = False) -> SearchQuery:
        if text.count('"') % 2:
            raise ValueError("Virgolette sbilanciate")
        clauses: list[QueryClause] = []
        for i, part in enumerate(text.split('"')):
            if i % 2:
                if allow_wildcards and "*" in part:
                    raise ValueError("Wildcard non ammessa in frase")
                clauses.append(PhraseClause(part))
            elif part.strip():
                if not allow_wildcards or "*" not in part:
                    clauses.append(TermsClause(part))
                else:
                    for word in re.findall(r"\S+", part):
                        if "*" in word:
                            if word.count("*") != 1 or not (word.startswith("*") or word.endswith("*")):
                                raise ValueError("Sintassi wildcard non valida")
                            value = word[1:] if word.startswith("*") else word[:-1]
                            if not all(unicodedata.category(char)[0] in {"L", "N", "M"}
                                       for char in value):
                                raise ValueError("Sintassi wildcard non valida")
                            clauses.append(SuffixClause(value) if word.startswith("*") else PrefixClause(value))
                        else:
                            clauses.append(TermsClause(word))
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
    def matched_ids_by_field(self, query: SearchQuery,
                             snapshot: IndexSnapshot) -> dict[SearchField, set[DocumentId]]:
        return self._matched_ids_by_field(query, snapshot)

    def score(self, query: SearchQuery, snapshot: IndexSnapshot, document_id: DocumentId,
              matched_fields: frozenset[SearchField]) -> tuple[int, int]:
        """Priorità al nome e frequenza delle posizioni distinte nei campi completi."""
        analyzed = _analyze(query)
        positions_by_field = []
        for field in (SearchField.FILENAME, SearchField.CONTENT):
            if field not in matched_fields:
                continue
            index = snapshot.filename_index if field is SearchField.FILENAME else snapshot.content_index
            positions = set()
            for clause, terms in zip(query.clauses, analyzed[field]):
                if isinstance(clause, (PrefixClause, SuffixClause)):
                    for term in self._expand(index, clause, terms[0], 257):
                        posting = index.terms[term].get(document_id)
                        if posting:
                            positions.update(posting.positions)
                elif isinstance(clause, PhraseClause):
                    postings = [index.terms.get(term, {}).get(document_id) for term in terms]
                    if all(postings):
                        starts = set(postings[0].positions)
                        for offset, posting in enumerate(postings[1:], 1):
                            starts.intersection_update(position - offset for position in posting.positions)
                        for start in starts:
                            positions.update(range(start, start + len(terms)))
                else:
                    for term in terms:
                        posting = index.terms.get(term, {}).get(document_id)
                        if posting:
                            positions.update(posting.positions)
            positions_by_field.append(len(positions))
        return (int(SearchField.FILENAME in matched_fields), sum(positions_by_field))

    def evaluate(self, query: SearchQuery, snapshot: IndexSnapshot) -> tuple[SearchMatch, ...]:
        by_field = self._matched_ids_by_field(query, snapshot)
        return tuple(self._make_match(key, by_field) for key in snapshot.ordered_document_ids
                     if any(key in ids for ids in by_field.values()))

    def evaluate_page(self, query: SearchQuery, snapshot: IndexSnapshot,
                      offset: int, limit: int) -> tuple[tuple[SearchMatch, ...], int]:
        by_field = self._matched_ids_by_field(query, snapshot)
        total = len(set().union(*by_field.values()))
        if offset >= total:
            return (), total
        page = []
        skipped = 0
        for key in snapshot.ordered_document_ids:
            if not any(key in ids for ids in by_field.values()):
                continue
            if skipped < offset:
                skipped += 1
                continue
            page.append(self._make_match(key, by_field))
            if len(page) == limit:
                break
        return tuple(page), total

    @staticmethod
    def _make_match(key: DocumentId, by_field: dict[SearchField, set[DocumentId]]) -> SearchMatch:
        return SearchMatch(key, frozenset(field for field, ids in by_field.items() if key in ids))

    def _matched_ids_by_field(self, query: SearchQuery,
                              snapshot: IndexSnapshot) -> dict[SearchField, set[DocumentId]]:
        if not isinstance(snapshot, IndexSnapshot):
            raise ValueError("La ricerca richiede uno snapshot immutabile")
        analyzed = _analyze(query)
        expansions = {}
        for field, clauses in analyzed.items():
            index = snapshot.filename_index if field is SearchField.FILENAME else snapshot.content_index
            for position, (clause, terms) in enumerate(zip(query.clauses, clauses)):
                if isinstance(clause, (PrefixClause, SuffixClause)):
                    values = self._expand(index, clause, terms[0], 257)
                    if len(values) > 256:
                        raise ValueError("Wildcard con oltre 256 espansioni")
                    expansions[field, position] = values
        matches: dict[SearchField, set[DocumentId]] = {}
        for field, clauses in analyzed.items():
            index = snapshot.filename_index if field is SearchField.FILENAME else snapshot.content_index
            candidates: set[DocumentId] | None = None
            for position, (clause, terms) in enumerate(zip(query.clauses, clauses)):
                if isinstance(clause, (PrefixClause, SuffixClause)):
                    found = set().union(*(index.terms[term] for term in expansions[field, position]))
                else:
                    found = self._match_clause(index, terms, isinstance(clause, PhraseClause))
                candidates = found if candidates is None else candidates & found
                if not candidates:
                    break
            matches[field] = candidates or set()
        return matches

    @staticmethod
    def _expand(index: PositionalIndex, clause: QueryClause, term: str,
                limit: int) -> tuple[str, ...]:
        if isinstance(clause, SuffixClause):
            return index.terms_with_suffix(term, limit)
        return index.terms_with_prefix(term, limit)

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
