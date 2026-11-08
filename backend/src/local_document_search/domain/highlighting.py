"""Mappe dei token indicizzati verso intervalli del testo acquisito."""
from dataclasses import dataclass
import re
import unicodedata

from .analysis import ContentAnalyzer, FilenameAnalyzer
from .queries import PhraseClause, PrefixClause, SearchQuery, SearchField, _analyze


@dataclass(frozen=True)
class TokenSpan:
    term: str
    start: int
    end: int


def token_spans(text: str, *, filename: bool = False) -> tuple[TokenSpan, ...]:
    if text.isascii() and not filename:
        return tuple(TokenSpan(match.group().lower(), match.start(), match.end())
                     for match in re.finditer(r"[A-Za-z0-9]+", text))
    # Le unità comprendono i segni combinanti: NFC/casefold mantengono la
    # corrispondenza con i caratteri originali anche quando cambiano lunghezza.
    units: list[tuple[str, int, int]] = []
    for offset, char in enumerate(text):
        if unicodedata.category(char).startswith("M") and units:
            value, start, _ = units[-1]
            units[-1] = (value + char, start, offset + 1)
        else:
            units.append((char, offset, offset + 1))
    folded: list[tuple[str, int, int]] = []
    for i, (unit, start, end) in enumerate(units):
        char = unicodedata.normalize("NFC", unit)[0]
        previous = unicodedata.normalize("NFC", units[i - 1][0])[0] if i else ""
        following = unicodedata.normalize("NFC", units[i + 1][0])[0] if i + 1 < len(units) else ""
        if filename and previous and (
            (previous.islower() and char.isupper()) or
            (previous.isupper() and char.isupper() and following.islower()) or
            (previous.isalpha() and char.isnumeric()) or
            (previous.isnumeric() and char.isalpha())
        ):
            folded.append((" ", start, start))
        value = unicodedata.normalize("NFC", unicodedata.normalize("NFC", unit).casefold())
        folded.extend((piece, start, end) for piece in value)
    result = []
    chars = []
    first = last = 0
    for char, start, end in folded + [(" ", len(text), len(text))]:
        category = unicodedata.category(char)[0]
        if category in {"L", "N"} or (category == "M" and chars):
            if not chars:
                first = start
            chars.append(char)
            last = end
        elif chars:
            result.append(TokenSpan("".join(chars), first, last))
            chars = []
    analyzer = FilenameAnalyzer() if filename else ContentAnalyzer()
    # Qualsiasi variazione Unicode non modellata va rilevata, mai evidenziata
    # su coordinate sbagliate.
    if tuple(span.term for span in result) != tuple(token.term for token in analyzer.analyze(text)):
        raise ValueError("Mappatura Unicode incoerente con l'analyzer")
    return tuple(result)


def matching_ranges(query: SearchQuery, field: SearchField,
                    spans: tuple[TokenSpan, ...]) -> tuple[tuple[int, int], ...]:
    clauses = _analyze(query)[field]
    ranges = []
    for clause, terms in zip(query.clauses, clauses):
        width = len(terms)
        for index in range(len(spans) - width + 1):
            sequence = tuple(span.term for span in spans[index:index + width])
            if isinstance(clause, PrefixClause):
                found = sequence[0].startswith(terms[0])
            elif isinstance(clause, PhraseClause):
                found = sequence == terms
            else:
                found = False
            if found:
                if isinstance(clause, PhraseClause):
                    ranges.append((spans[index].start, spans[index + width - 1].end))
                elif isinstance(clause, PrefixClause):
                    ranges.append((spans[index].start, spans[index].end))
                else:
                    pass
        if not isinstance(clause, (PrefixClause, PhraseClause)):
            ranges.extend((span.start, span.end) for span in spans if span.term in terms)
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return tuple(merged)
