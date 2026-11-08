"""Runner isolato V2-02. Il controller usa processi nuovi per ogni fase."""
import argparse
import cProfile
from contextlib import ExitStack
import hashlib
import ctypes
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import random
import pstats
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

from v2_benchmark import MARKERS, QUERIES, expected_paths, verify


def memory():
    if sys.platform != "win32":
        return {"peak_working_set_bytes": None, "peak_private_bytes": None}
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    function = ctypes.WinDLL("psapi").GetProcessMemoryInfo
    function.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    if not function(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return {"peak_working_set_bytes": counters.PeakWorkingSetSize,
            "peak_private_bytes": counters.PeakPagefileUsage}


def percentile95(samples):
    return sorted(samples)[math.ceil(.95 * len(samples)) - 1]


def summary(samples):
    return {"values": samples, "median": statistics.median(samples),
            "p95_nearest_rank": percentile95(samples), "min": min(samples), "max": max(samples)}


def wait_job(app, state, timeout):
    from local_document_search.application.contracts import JobState
    if state.job is None:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = app.job_status.execute(state.job.job_id)
        if status.state == JobState.COMPLETED:
            return status
        if status.state == JobState.FAILED:
            raise RuntimeError(f"Job fallito: {status.error}")
        time.sleep(.02)
    raise TimeoutError("Job oltre il timeout")


def storage_bytes(storage):
    return sum(p.stat().st_size for p in storage.rglob("*") if p.is_file())


def hardware():
    if sys.platform != "win32":
        return {"processor": platform.processor()}
    script = ("[pscustomobject]@{cpu=(Get-CimInstance Win32_Processor).Name;"
              "ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory;"
              "disks=@(Get-PhysicalDisk | Select-Object FriendlyName,MediaType,Size);"
              "battery=@(Get-CimInstance Win32_Battery | Select-Object BatteryStatus,EstimatedChargeRemaining)}"
              " | ConvertTo-Json -Depth 5 -Compress")
    result = json.loads(subprocess.check_output(["powershell", "-NoProfile", "-Command", script], text=True))
    result["power_scheme"] = subprocess.check_output(["powercfg", "/getactivescheme"], text=True).strip()
    return result


def actual_text_bytes(app, manifest):
    from local_document_search.application.contracts import SearchRequest
    page = app.search.execute(SearchRequest("documento", limit=manifest["count"]))
    if page.total_matches != manifest["count"]:
        raise AssertionError("Conteggio documenti diverso")
    return sum(len(app.get_document.execute(r.document_id, page.snapshot_id).extracted_text.encode())
               for r in page.results)


def check_queries(app, manifest):
    from local_document_search.application.contracts import SearchField, SearchRequest, SuggestRequest
    for query, field in QUERIES:
        page = app.search.execute(SearchRequest(query, SearchField(field), limit=manifest["count"]))
        actual = [r.relative_path.value for r in page.results]
        expected = expected_paths(manifest, query, field)
        if actual != expected:
            raise AssertionError(f"Query errata: {field} {query}: {len(actual)} != {len(expected)}")
    for prefix, marker in (("marcatoremed*", MARKERS[1]),
                           ("marcatorerar*", MARKERS[2])):
        page = app.search.execute(SearchRequest(prefix, SearchField.CONTENT,
                                                limit=manifest["count"], allow_prefixes=True))
        if [r.relative_path.value for r in page.results] != expected_paths(manifest, marker, "content"):
            raise AssertionError(f"Prefisso errato: {prefix}")
    if app.suggest.execute(SuggestRequest("marcatoreme", SearchField.CONTENT)).terms != (MARKERS[1],):
        raise AssertionError("Suggerimento errato")


def phase(args):
    from local_document_search.application.contracts import SearchField, SearchRequest, SuggestRequest
    from local_document_search.interfaces.composition import compose_v2_application
    # The controller verifies every source byte before copying the cycle.
    manifest = json.loads((args.corpus / "manifest.json").read_text(encoding="utf-8"))
    storage = args.storage
    if args.phase == "build" and storage.exists():
        raise ValueError("Storage già esistente")
    started = time.perf_counter()
    with compose_v2_application(storage) as app:
        composed = time.perf_counter()
        result = {"phase": args.phase, "compose_seconds": composed - started}
        diagnostics = {}
        stack = ExitStack()
        if getattr(args, "diagnostic", False):
            from local_document_search.infrastructure.readers.registry import DocumentReader
            from local_document_search.domain.snapshots import IndexBuilder
            from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository
            from local_document_search.infrastructure.v2_snapshot_storage import V2SqliteSnapshotRepository
            from local_document_search.domain.queries import QueryEvaluator
            for cls, names, label in (
                (DocumentReader, ("read",), "extraction"),
                (IndexBuilder, ("add",), "index_add"),
                (SqliteSnapshotRepository, ("save_candidate", "validate_candidate", "activate"), "persistence"),
                (SqliteSnapshotRepository, ("load_active",), "load"),
                (V2SqliteSnapshotRepository, ("save_candidate", "validate_candidate", "activate"), "v2_persistence"),
                (V2SqliteSnapshotRepository, ("load_active",), "v2_load"),
                (QueryEvaluator, ("evaluate",), "query_evaluation"),
            ):
                for name in names:
                    original = getattr(cls, name)
                    def timed(self, *a, _original=original, _label=label, **kw):
                        begin = time.perf_counter()
                        try:
                            return _original(self, *a, **kw)
                        finally:
                            diagnostics[_label] = diagnostics.get(_label, 0) + time.perf_counter() - begin
                    stack.enter_context(patch.object(cls, name, timed))
            original_clause = QueryEvaluator._match_clause
            def timed_clause(*a, **kw):
                begin = time.perf_counter()
                try:
                    return original_clause(*a, **kw)
                finally:
                    diagnostics["query_clauses"] = diagnostics.get("query_clauses", 0) + time.perf_counter() - begin
            stack.enter_context(patch.object(QueryEvaluator, "_match_clause", staticmethod(timed_clause)))
        with stack:
            if args.phase == "build":
                state = app.select_directory.execute(str((args.corpus / "source").resolve()))
                wait_job(app, state, args.timeout)
                result["operation_seconds"] = time.perf_counter() - composed
                result["actual_text_bytes"] = actual_text_bytes(app, manifest)
                if not (.99 * manifest["target_text_bytes"] <= result["actual_text_bytes"] <=
                        1.01 * manifest["target_text_bytes"]):
                    raise AssertionError("Testo estratto fuori tolleranza 1%")
                check_queries(app, manifest)
            elif args.phase == "reopen":
                state = app.initialize.execute()
                result["search_ready_seconds"] = time.perf_counter() - started
                if args.parent_start is not None:
                    result["process_to_search_ready_seconds"] = time.perf_counter() - args.parent_start
                sync_start = time.perf_counter()
                wait_job(app, state, args.timeout)
                result["startup_sync_seconds"] = time.perf_counter() - sync_start
                check_queries(app, manifest)
            elif args.phase == "nochange":
                begin = time.perf_counter()
                sync = app.synchronize.execute()
                result["operation_seconds"] = time.perf_counter() - begin
                if sync.changed:
                    raise AssertionError("No-change ha pubblicato un candidato")
            elif args.phase == "incremental":
                begin = time.perf_counter()
                sync = app.synchronize.execute()
                result["operation_seconds"] = time.perf_counter() - begin
                expected = min(100, manifest["count"] // 6)
                if (sync.added, sync.modified, sync.removed) != (expected,) * 3:
                    raise AssertionError(f"Diff errato: {sync}")
            elif args.phase == "queries":
                check_queries(app, manifest)
                requests = [(q, f, SearchRequest(q, SearchField(f), limit=50)) for q, f in QUERIES]
                requests.extend((q, "content", SearchRequest(q, SearchField.CONTENT, limit=50,
                                                                allow_prefixes=True))
                                for q in ("marcatoremed*", "marcatorerar*", "frasecom*"))
                requests.append(("marcatoreme", "suggest", SuggestRequest("marcatoreme", SearchField.CONTENT)))
                for _, _, request in requests:
                    for _ in range(args.warmups):
                        (app.suggest if isinstance(request, SuggestRequest) else app.search).execute(request)
                samples = {(q, f): [] for q, f, _ in requests}
                rng = random.Random(manifest["seed"])
                for _ in range(args.samples):
                    order = requests[:]
                    rng.shuffle(order)
                    for q, f, request in order:
                        begin = time.perf_counter()
                        (app.suggest if isinstance(request, SuggestRequest) else app.search).execute(request)
                        samples[q, f].append(time.perf_counter() - begin)
                result["queries"] = [{"query": q, "field": f, "seconds": values,
                                      "summary": summary(values)} for (q, f), values in samples.items()]
        if diagnostics:
            result["diagnostic_seconds"] = diagnostics
        result["memory"] = memory()
        result["storage_bytes"] = storage_bytes(storage)
    return result


def mutate(corpus, manifest):
    # Controller operates on a per-cycle copy; no source restoration is needed.
    files = manifest["files"]
    n = min(100, len(files) // 6)
    for index, entry in enumerate(files[:n]):
        path = corpus / "source" / entry["path"]
        if path.suffix == ".pdf":
            from m9_corpus import pdf_bytes
            path.write_bytes(pdf_bytes("marcatoreincrementale modifica"))
        else:
            path.write_text("marcatoreincrementale modifica\n", encoding="utf-8")
    for entry in files[n:2*n]:
        (corpus / "source" / entry["path"]).unlink()
    from m9_corpus import pdf_bytes
    for index in range(n):
        suffix = ("txt", "md", "pdf")[index % 3]
        path = corpus / "source" / f"cartella{index % 20:02d}/aggiunto{index:05d}.{suffix}"
        data = pdf_bytes("marcatoreincrementale aggiunto") if suffix == "pdf" else b"marcatoreincrementale aggiunto\n"
        path.write_bytes(data)
    return n


def run(args):
    import shutil
    import tempfile
    if args.cycles < 1 or args.samples < 1 or args.warmups < 0 or args.timeout <= 0:
        raise ValueError("cycles/samples/timeout positivi e warmups non negativo richiesti")
    manifest = verify(args.corpus)
    if args.output.exists():
        raise ValueError("Output già esistente")
    args.output.mkdir(parents=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    report = {"status": "INCOMPLETE", "revision": revision, "dirty": dirty,
              "platform": platform.platform(), "python": sys.version,
              "hardware": hardware(),
              "dependencies": {name: importlib.metadata.version(name) for name in ("pypdf", "markdown-it-py")},
              "corpus_id": hashlib.sha256((args.corpus / "manifest.json").read_bytes()).hexdigest(),
              "experiment_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                    for name in ("v2_benchmark.py", "run_v2_benchmark.py", "m9_corpus.py")},
              "corpus": {k: v for k, v in manifest.items() if k != "files"},
              "cache": "OS cache not cleared; new process per phase", "cycles": []}
    report_path = args.output / "report.json"
    def save():
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    save()
    temporary_storage = Path(tempfile.mkdtemp(prefix="lds-v2-benchmark-"))
    try:
        for cycle in range(args.cycles):
            root = args.output / f"cycle-{cycle + 1}"
            shutil.copytree(args.corpus, root / "corpus")
            storage = temporary_storage / f"cycle-{cycle + 1}"
            events = []
            report["cycles"].append(events)
            for stage in ("build", "reopen", "nochange", "queries", "incremental"):
                if stage == "incremental":
                    mutate(root / "corpus", manifest)
                result_path = root / f"{stage}.json"
                command = [sys.executable, __file__, "_phase", stage, str(root / "corpus"),
                           str(storage), str(result_path), "--timeout", str(args.timeout),
                           "--samples", str(args.samples), "--warmups", str(args.warmups)]
                elapsed = time.perf_counter()
                command.extend(["--parent-start", str(elapsed)])
                completed = subprocess.run(command, capture_output=True, text=True,
                                           timeout=args.timeout + 120)
                if completed.returncode:
                    raise RuntimeError(f"{stage}: {completed.stderr[-2000:]}")
                event = json.loads(result_path.read_text(encoding="utf-8"))
                event["process_seconds"] = time.perf_counter() - elapsed
                events.append(event)
                save()
        report["status"] = "PASS"
    except BaseException as exc:
        report["error"] = repr(exc)
        raise
    finally:
        save()
        shutil.rmtree(temporary_storage)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    execute = sub.add_parser("run")
    execute.add_argument("corpus", type=Path)
    execute.add_argument("output", type=Path)
    execute.add_argument("--cycles", type=int, default=3)
    execute.add_argument("--samples", type=int, default=100)
    execute.add_argument("--warmups", type=int, default=5)
    execute.add_argument("--timeout", type=int, default=3600)
    child = sub.add_parser("_phase")
    child.add_argument("phase", choices=("build", "reopen", "nochange", "queries", "incremental"))
    child.add_argument("corpus", type=Path)
    child.add_argument("storage", type=Path)
    child.add_argument("output", type=Path)
    child.add_argument("--timeout", type=int, default=3600)
    child.add_argument("--samples", type=int, default=100)
    child.add_argument("--warmups", type=int, default=5)
    child.add_argument("--parent-start", type=float)
    summary_command = sub.add_parser("summary")
    summary_command.add_argument("report", type=Path)
    diagnostic = sub.add_parser("profile")
    diagnostic.add_argument("corpus", type=Path)
    diagnostic.add_argument("storage", type=Path)
    diagnostic.add_argument("output", type=Path)
    diagnostic.add_argument("--phase", choices=("build", "reopen", "queries"), default="build")
    args = parser.parse_args()
    if args.command == "run":
        print(json.dumps({k: v for k, v in run(args).items() if k != "cycles"}, indent=2))
    elif args.command == "_phase":
        result = phase(args)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif args.command == "profile":
        args.timeout, args.samples, args.warmups = 3600, 5, 1
        args.parent_start = None
        args.diagnostic = True
        profiler = cProfile.Profile()
        profiler.enable()
        result = phase(args)
        profiler.disable()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        profiler.dump_stats(str(args.output.with_suffix(".pstats")))
        with args.output.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(result, indent=2) + "\n")
            pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumulative").print_stats(40)
    else:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if report["status"] != "PASS":
            raise ValueError("Report incompleto")
        for stage in ("build", "reopen", "nochange", "queries", "incremental"):
            events = [next(e for e in cycle if e["phase"] == stage) for cycle in report["cycles"]]
            key = "process_to_search_ready_seconds" if stage == "reopen" and "process_to_search_ready_seconds" in events[0] else ("search_ready_seconds" if stage == "reopen" else "operation_seconds")
            if stage == "queries":
                cases = {(q["query"], q["field"]) for q in events[0]["queries"]}
                print(json.dumps({"phase": stage, "cases": [
                    {"query": query, "field": field,
                     "p95_seconds_by_cycle": [next(q for q in e["queries"] if q["query"] == query
                                                   and q["field"] == field)["summary"]["p95_nearest_rank"]
                                              for e in events]}
                    for query, field in sorted(cases)]}))
            else:
                print(json.dumps({"phase": stage, **summary([e[key] for e in events])}))
            print(json.dumps({"phase": stage, "peak_working_set_bytes":
                              [e["memory"]["peak_working_set_bytes"] for e in events],
                              "peak_private_bytes": [e["memory"]["peak_private_bytes"] for e in events],
                              "storage_bytes": [e["storage_bytes"] for e in events]}))
            if stage == "reopen":
                print(json.dumps({"phase": "startup_sync", **summary(
                    [e["startup_sync_seconds"] for e in events])}))


if __name__ == "__main__":
    main()
