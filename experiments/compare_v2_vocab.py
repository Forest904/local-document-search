"""Confronto riproducibile delle strutture del vocabolario V2-03."""
import argparse
from bisect import bisect_left
import json
from heapq import nsmallest
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

from v2_benchmark import VOCABULARY


def balanced(values):
    if not values:
        return None
    mid = len(values) // 2
    return values[mid], balanced(values[:mid]), balanced(values[mid + 1:])


def tree_find(node, value):
    while node is not None:
        key, left, right = node
        if key == value:
            return True
        node = left if value < key else right
    return False


def tree_prefix(node, prefix):
    if node is None:
        return 0
    key, left, right = node
    if key < prefix:
        return tree_prefix(right, prefix)
    if key >= prefix + chr(0x10ffff):
        return tree_prefix(left, prefix)
    return int(key.startswith(prefix)) + tree_prefix(left, prefix) + tree_prefix(right, prefix)


def array_prefix(values, prefix):
    start = bisect_left(values, prefix)
    end = bisect_left(values, prefix + chr(0x10ffff))
    return end - start


def suffix_candidates(reversed_values, suffix):
    key = suffix[::-1]
    start = bisect_left(reversed_values, key)
    end = bisect_left(reversed_values, key + chr(0x10ffff))
    return (value[::-1] for value in reversed_values[start:end])


def measure(operation, repeat=100):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter_ns()
        operation()
        samples.append(time.perf_counter_ns() - start)
    return round(statistics.median(samples) / 1_000, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = {term: None for term in VOCABULARY}
    values = tuple(sorted(source))
    tree = balanced(values)
    probes = ("termine00000", "termine12345", "missing")
    prefixes = ("termine12345", "termine12", "termine", "missing")
    results = {"schema": 1, "python": sys.version, "vocabulary_size": len(values),
               "unit": "median microseconds per operation", "structures": {}}
    for name, build, exact, prefix in (
        ("dictionary", lambda: dict(source), lambda term: term in source,
         lambda p: sum(term.startswith(p) for term in source)),
        ("sorted_tuple", lambda: tuple(sorted(source)), lambda term: term in source,
         lambda p: array_prefix(values, p)),
        ("balanced_tree", lambda: balanced(values), lambda term: tree_find(tree, term),
         lambda p: tree_prefix(tree, p)),
    ):
        tracemalloc.start()
        instance = build()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        del instance
        results["structures"][name] = {
            "build_us": measure(build, 10), "incremental_peak_bytes": peak,
            "exact_us": {p: measure(lambda p=p: exact(p)) for p in probes},
            "prefix_us": {p: measure(lambda p=p: prefix(p)) for p in prefixes},
            "reopen_rebuild_us": measure(build, 10),
        }
    reversed_values = tuple(sorted(value[::-1] for value in values))
    tracemalloc.start()
    rebuilt = tuple(sorted(value[::-1] for value in values))
    _, reverse_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del rebuilt
    def reverse_lookup(suffix):
        key = suffix[::-1]
        start = bisect_left(reversed_values, key)
        end = bisect_left(reversed_values, key + chr(0x10ffff))
        return sum(1 for _ in range(start, end))
    results["suffix"] = {
        "incremental_peak_bytes": reverse_peak,
        "build_us": measure(lambda: tuple(sorted(value[::-1] for value in values)), 10),
        "reopen_rebuild_us": measure(lambda: tuple(sorted(value[::-1] for value in values)), 10),
        "lookup_us": {suffix: {"reversed": measure(lambda s=suffix: reverse_lookup(s)),
                                "scan": measure(lambda s=suffix: sum(v.endswith(s) for v in values))}
                      for suffix in ("12345", "45", "5")},
        "suggest_us": {suffix: measure(lambda s=suffix: nsmallest(10, suffix_candidates(reversed_values, s)))
                       for suffix in ("12345", "45", "5")},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
