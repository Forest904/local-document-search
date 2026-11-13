"""Metriche binarie per le valutazioni Homework 3, senza dipendenze dal prodotto."""


def score(expected, actual):
    expected, actual = set(expected), set(actual)
    tp = len(expected & actual)
    fp = len(actual - expected)
    fn = len(expected - actual)
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        "exact": expected == actual,
        "false_positives_without_expected": fp if not expected else None,
    }


def aggregate(rows):
    rows = list(rows)
    totals = {key: sum(row[key] for row in rows) for key in ("tp", "fp", "fn")}
    tp, fp, fn = (totals[key] for key in ("tp", "fp", "fn"))
    micro = dict(tp=tp, fp=fp, fn=fn,
                 precision=tp / (tp + fp) if tp + fp else None,
                 recall=tp / (tp + fn) if tp + fn else None,
                 f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None)
    macro = {}
    valid = {}
    for key in ("precision", "recall", "f1"):
        values = [row[key] for row in rows if row[key] is not None]
        macro[key] = sum(values) / len(values) if values else None
        valid[key] = len(values)
    return {"micro": micro, "macro": macro, "valid_cases": valid,
            "exact_sets": sum(row["exact"] for row in rows),
            "exact_set_fraction": sum(row["exact"] for row in rows) / len(rows) if rows else None}
