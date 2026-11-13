"""Esporta solo ID anonimi e metriche dai report HW3-02 verificati."""
import argparse
from pathlib import Path
import re

from homework3_evaluate import save_new, unseal


def public_summary(paths, output):
    results = []
    seen = set()
    for path in paths:
        report = unseal(path)
        if report["kind"] not in {"lexical_report", "relevance_report"}:
            raise ValueError("Richiesto un report di valutazione")
        corpus_id = report.get("corpus_id", report.get("sample_id"))
        if not isinstance(corpus_id, str) or not re.fullmatch(r"[a-f0-9]{64}", corpus_id):
            raise ValueError("Identità corpus non valida")
        key = (report["kind"], corpus_id)
        if key in seen:
            raise ValueError("Report duplicati per lo stesso corpus e tipo")
        seen.add(key)
        rows = []
        for row in report["rows"]:
            if not re.fullmatch(r"[QN][0-9]{2}", row["id"]):
                raise ValueError("Il report deve usare ID query anonimi Qxx/Nxx")
            if row["field"] not in {"filename", "content", "both"}:
                raise ValueError("Campo non valido")
            metrics = {k: row["metrics"][k] for k in (
                "tp", "fp", "fn", "precision", "recall", "f1", "exact",
                "false_positives_without_expected")}
            if any(v is not None and type(v) not in (int, float, bool) for v in metrics.values()):
                raise ValueError("Metrica non numerica")
            rows.append({"id": row["id"], "field": row["field"], "metrics": metrics})
        # Ricostruire gli aggregati evita di copiare campi liberi dai report locali.
        from homework3_metrics import aggregate
        results.append({"kind": report["kind"], "corpus_id": corpus_id,
            "report_sha256": report["artifact_sha256"], "query_count": len(rows),
            "rows": rows, "summary": aggregate(row["metrics"] for row in rows),
            "by_field": {field: aggregate(row["metrics"] for row in rows if row["field"] == field)
                         for field in sorted({row["field"] for row in rows})}})
    if not results:
        raise ValueError("Nessun report")
    data = {"schema": 1, "undefined_metric": "null = N/A", "results": results}
    save_new(output, data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    public_summary(args.reports, args.output)
    print("Aggregati esportati senza query, percorsi o giudizi dettagliati")


if __name__ == "__main__":
    main()
