"""Soglie e ordinamento della correzione di parole isolate."""
from local_document_search.domain.documents import DocumentId
from local_document_search.domain.index import PositionalIndex, Posting
from local_document_search.domain.spelling import best_candidate, edit_distance


def index(*terms):
    return PositionalIndex({term: {DocumentId(1): Posting((0,))} for term in terms})


def test_edit_distance_and_candidate_boundaries():
    assert edit_distance("cat", "act", 2) == 2
    assert edit_distance("famos", "famous", 2) == 1
    assert edit_distance("enterprenuers", "entrepreneurs", 2) > 2
    words = index("famous", "form", "café", "alpha")
    assert best_candidate("famos", (words,)).term == "famous"
    assert best_candidate("cafe", (words,)).term == "café"
    assert best_candidate("famous", (words,)) is None
    assert best_candidate("x123", (words,)) is None
    assert best_candidate("al", (words,)) is None


def test_same_candidate_across_fields_and_lexical_tie():
    first = index("bake", "cake")
    second = index("cake")
    assert best_candidate("dake", (first, second)).term == "bake"
    assert best_candidate("cakt", (first, second)).term == "cake"
