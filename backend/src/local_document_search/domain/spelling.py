"""Candidati ortografici dal vocabolario dello snapshot."""
from dataclasses import dataclass
import unicodedata

from .index import PositionalIndex, character_bigrams


@dataclass(frozen=True)
class Candidate:
    term: str
    distance: int
    jaccard: float


def edit_distance(left: str, right: str, maximum: int) -> int:
    if abs(len(left) - len(right)) > maximum:
        return maximum + 1
    previous = list(range(len(right) + 1))
    for row, char in enumerate(left, 1):
        current = [row]
        for column, other in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (char != other)))
        if min(current) > maximum:
            return maximum + 1
        previous = current
    return previous[-1]


def alphabetic(term: str) -> bool:
    return bool(term) and all(unicodedata.category(char)[0] in {"L", "M"} for char in term)


def best_candidate(term: str, indexes: tuple[PositionalIndex, ...]) -> Candidate | None:
    if len(term) < 3 or not alphabetic(term):
        return None
    if any(term in index.terms for index in indexes):
        return None
    grams = set(character_bigrams(term))
    candidates: set[str] = set()
    for index in indexes:
        for gram in grams:
            candidates.update(index.bigram_terms.get(gram, ()))
    maximum = 1 if len(term) <= 4 else 2
    best = None
    best_key = None
    for candidate in candidates:
        if not alphabetic(candidate) or abs(len(candidate) - len(term)) > maximum:
            continue
        candidate_grams = set(character_bigrams(candidate))
        # BOTH può contenere lo stesso termine in entrambi gli indici.
        shared = len(grams & candidate_grams)
        jaccard = shared / len(grams | candidate_grams)
        if jaccard < 0.20:
            continue
        distance = edit_distance(term, candidate, maximum)
        if distance > maximum:
            continue
        key = (distance, -jaccard, candidate)
        if best_key is None or key < best_key:
            best_key = key
            best = Candidate(candidate, distance, jaccard)
    return best
