"""Pilot HW3-03: un processo, build volatile e recupero completo, solo opt-in."""
import argparse
import json
import platform
from pathlib import Path
import statistics
import subprocess
from time import perf_counter

from homework3_evaluate import (check_corpus, digest, environment, retrieve,
                                save_new, unseal, validate_queries)
from homework3_scan import scan


def hardware():
    result = dict(cpu=platform.processor() or None, ram_bytes=None, power=None)
    if platform.system() == "Windows":
        script = ('[pscustomobject]@{cpu=(Get-CimInstance Win32_Processor).Name;'
                  'ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory;'
                  'power=@(Get-CimInstance Win32_Battery | Select-Object '
                  'BatteryStatus,EstimatedChargeRemaining)} | ConvertTo-Json -Compress')
        try:
            raw = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                                 capture_output=True, text=True, check=True, timeout=15)
            result.update(json.loads(raw.stdout))
        except (subprocess.SubprocessError, ValueError, OSError):
            pass
    result["power_note"] = "Stato batteria osservato; vuoto/null = alimentazione non rilevabile"
    return result


def stats(values):
    return dict(n=len(values), median=statistics.median(values) if values else None,
                min=min(values) if values else None, max=max(values) if values else None)


def summarize(report):
    """Whitelist pubblica: nessuna query, percorso, testo o eccezione locale."""
    rows = []
    for query in report["queries"]:
        samples = [s for s in report["samples"] if s["id"] == query["id"]
                   and s["pass"] > 0 and s.get("seconds") is not None]
        row = dict(id=query["id"], field=query["field"])
        for method in ("index", "scan"):
            row[method] = stats([s["seconds"] for s in samples if s["method"] == method])
        a, b = row["index"]["median"], row["scan"]["median"]
        row["scan_over_index"] = b / a if a and b is not None else None
        rows.append(row)
    fields = {}
    for field in sorted({q["field"] for q in rows}):
        fields[field] = {method: stats([s["seconds"] for s in report["samples"]
            if s["field"] == field and s["pass"] > 0 and s["method"] == method
            and s.get("seconds") is not None]) for method in ("index", "scan")}
        fields[field]["ratios"] = stats([r["scan_over_index"] for r in rows
            if r["field"] == field and r["scan_over_index"] is not None])
    return {**{k: report[k] for k in ("corpus_id", "frozen_sha256", "build_seconds",
            "complete", "correct", "timeout", "elapsed_seconds", "missing",
            "integrity_after", "hardware")}, "queries": rows, "by_field": fields,
            "comparisons": len(report["samples"]),
            "exact_comparisons": sum(s.get("exact") is True for s in report["samples"]),
            "environment": {k: report["environment"][k]
                            for k in ("utc", "python", "platform", "revision", "tools")},
            "working_tree_dirty": bool(report["environment"]["working_tree"]),
            "units": "seconds", "cache": "OS non svuotata; nessuna cache applicativa scan"}


def run(frozen_path, output, budget=600, clock=perf_counter):
    from local_document_search.interfaces.composition import compose_cli

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    start = clock()
    frozen = unseal(frozen_path, "lexical_frozen")
    queries = frozen["draft"]["queries"]
    validate_queries(queries)
    if set(frozen["expected"]) != {q["id"] for q in queries}:
        raise ValueError("Attesi mancanti")
    check_corpus(frozen["corpus"])
    report = dict(corpus_id=frozen["corpus"]["corpus_id"],
                  frozen_sha256=frozen["artifact_sha256"], environment=environment(),
                  hardware=hardware(), queries=queries, samples=[], build_seconds=None,
                  complete=False, correct=None, timeout=False, integrity_after=False,
                  budget_seconds=budget, errors=[])
    root = Path(frozen["corpus"]["root"]) / "txt"
    schedule = [(p, q, m) for p in range(4) for q in queries
                for m in (("index", "scan") if p % 2 == 0 else ("scan", "index"))]
    save_new(output / "setup.json", dict(report, schedule=[
        dict(pass_number=p, id=q["id"], method=m) for p, q, m in schedule]))
    try:
        if clock() - start < budget:
            app = compose_cli(str(root.absolute()))
            if clock() - start < budget:
                before = clock()
                build = app.build.execute(app.root_directory)
                report["build_seconds"] = clock() - before
                save_new(output / "build.json", dict(seconds=report["build_seconds"],
                    indexed=build.indexed, discovered=build.discovered, excluded=build.excluded))
                count = len(frozen["corpus"]["files"])
                if build.indexed != count or build.discovered != count or build.excluded:
                    raise ValueError("Build non corrispondente al corpus")
                with (output / "samples.jsonl").open("x", encoding="utf-8") as log:
                    for p, query, method in schedule:
                        if clock() - start >= budget:
                            break
                        sample = dict(id=query["id"], field=query["field"],
                                      method=method, seconds=None, **{"pass": p})
                        before = clock()
                        try:
                            actual = (retrieve(app, query, build.snapshot_id) if method == "index"
                                      else scan(root, [query])[query["id"]])
                            sample["seconds"] = clock() - before
                            wanted = set(frozen["expected"][query["id"]])
                            sample.update(exact=set(actual) == wanted,
                                false_positives=sorted(set(actual) - wanted),
                                false_negatives=sorted(wanted - set(actual)))
                        except Exception as exc:
                            sample.update(error=repr(exc), exact=False,
                                          failed_elapsed_seconds=clock() - before)
                        sample["elapsed_seconds"] = clock() - start
                        report["samples"].append(sample)
                        log.write(json.dumps(sample, ensure_ascii=True) + "\n")
                        log.flush()
                        if "error" in sample:
                            break
    except Exception as exc:
        report["errors"].append(repr(exc))
    finally:
        report["elapsed_seconds"] = clock() - start
        report["timeout"] = report["elapsed_seconds"] >= budget
        try:
            check_corpus(frozen["corpus"])
            report["integrity_after"] = True
        except Exception as exc:
            report["errors"].append(repr(exc))
        done = {(s["pass"], s["id"], s["method"]) for s in report["samples"]}
        report["missing"] = [dict(pass_number=p, id=q["id"], method=m)
                             for p, q, m in schedule if (p, q["id"], m) not in done]
        report["complete"] = (not report["missing"] and not report["errors"]
                              and all("error" not in s for s in report["samples"]))
        report["correct"] = (all(s["exact"] for s in report["samples"])
                             if report["samples"] else None)
        save_new(output / "report.json", report)
        public = summarize(report)
        public["report_sha256"] = digest((output / "report.json").read_bytes())
        save_new(output / "summary.json", public)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frozen", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = run(args.frozen, args.output)
    print(json.dumps({k: report[k] for k in
                     ("complete", "correct", "timeout", "elapsed_seconds", "build_seconds")}))
    return 0 if report["complete"] and report["correct"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
