"""Misure backend M9 su storage isolato; non misura il processo Qt compilato."""
import argparse
import ctypes
from dataclasses import asdict
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

from local_document_search.application.contracts import JobState, SearchField, SearchRequest
from local_document_search.interfaces.composition import compose_persistent_application


def peak_memory():
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    get_memory = ctypes.WinDLL("psapi").GetProcessMemoryInfo
    get_memory.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    if not get_memory(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return {"peak_working_set_bytes": counters.PeakWorkingSetSize,
            "peak_pagefile_bytes": counters.PeakPagefileUsage}


def wait_job(app, state):
    if state.job is None:
        return
    deadline = time.monotonic() + 600
    next_log = 0
    while time.monotonic() < deadline:
        status = app.job_status.execute(state.job.job_id)
        if time.monotonic() >= next_log:
            print(f"{status.phase}: {status.files_completed}/{status.files_total}", flush=True)
            next_log = time.monotonic() + 20
        if status.state == JobState.COMPLETED:
            return status
        if status.state == JobState.FAILED:
            raise RuntimeError(f"Job fallito: {status.error}")
        time.sleep(0.01)
    raise TimeoutError("Job oltre 600 secondi")


def measure(operation):
    start = time.perf_counter()
    value = operation()
    return value, time.perf_counter() - start


def hardware():
    command = ("[pscustomobject]@{cpu=(Get-CimInstance Win32_Processor).Name; "
               "ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory} | ConvertTo-Json")
    return json.loads(subprocess.check_output(["powershell", "-NoProfile", "-Command", command], text=True))


def run(corpus, storage):
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    if storage.exists():
        raise ValueError("Lo storage di benchmark deve essere nuovo")
    source = corpus / "source"
    result = {"kind": "backend-source", "python": sys.version, "platform": platform.platform(),
              "hardware": hardware(), "seed": manifest["seed"], "count": manifest["count"],
              "source_bytes": manifest["source_bytes"], "queries": []}
    with compose_persistent_application(storage) as app:
        def initial():
            return wait_job(app, app.select_directory.execute(str(source.resolve())))
        status, result["initial_build_seconds"] = measure(initial)
        result["initial_job"] = asdict(status)
        original = app.status.execute().active_snapshot_id
        extracted_bytes = 0
        page = app.search.execute(SearchRequest("corpus", limit=manifest["count"]))
        for item in page.results:
            detail = app.get_document.execute(item.document_id, page.snapshot_id)
            extracted_bytes += len(detail.extracted_text.encode("utf-8"))
        result["extracted_utf8_bytes"] = extracted_bytes
        for query in manifest["queries"]:
            request = SearchRequest(query["query"], SearchField(query["field"]), limit=manifest["count"])
            response = app.search.execute(request)
            actual = [item.relative_path.value for item in response.results]
            if actual != query["expected"]:
                raise AssertionError(f"Query differente dalle attese: {query['query']}")
            samples = [measure(lambda: app.search.execute(request))[1] for _ in range(5)]
            result["queries"].append({"query": query["query"], "field": query["field"],
                                      "matches": response.total_matches, "seconds": samples,
                                      "median_seconds": statistics.median(samples)})
        sync, result["no_change_seconds"] = measure(app.synchronize.execute)
        assert not sync.changed and sync.snapshot_id == original
    def reopen():
        app = compose_persistent_application(storage)
        state = app.initialize.execute()
        return app, state
    (app, state), result["reopen_load_seconds"] = measure(reopen)
    with app:
        _, result["startup_sync_remaining_seconds"] = measure(lambda: wait_job(app, state))
        assert app.status.execute().active_snapshot_id == original
        added = source / "aggiunto.txt"
        modified = source / manifest["files"][0]["path"]
        removed = source / manifest["files"][1]["path"]
        saved_modified, saved_removed = modified.read_bytes(), removed.read_bytes()
        try:
            added.write_text("incrementale nuovo", encoding="utf-8")
            modified.write_text("incrementale cambiato", encoding="utf-8")
            removed.unlink()
            sync, result["incremental_seconds"] = measure(app.synchronize.execute)
            result["incremental"] = asdict(sync)
            assert (sync.added, sync.modified, sync.removed) == (1, 1, 1)
            assert app.search.execute(SearchRequest("incrementale")).total_matches == 2
        finally:
            added.unlink(missing_ok=True)
            modified.write_bytes(saved_modified)
            removed.write_bytes(saved_removed)
    result.update(peak_memory())
    result["limits"] = ["Picco memoria dell'intero processo backend, non per fase",
                        "Riapertura nello stesso processo e cache OS calda",
                        "Tempi complessivi: estrazione/analisi/commit non separati",
                        "Query dopo warm-up, 5 ripetizioni; nessuna soglia approvata"]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("storage", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.corpus.resolve(), args.storage.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
