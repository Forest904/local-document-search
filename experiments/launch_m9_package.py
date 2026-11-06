"""Avvia lo ZIP estratto con ambiente isolato e misura il solo processo compilato."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time


def isolated_environment(original, workspace):
    """Windows tratta i nomi senza case; non modificare l'ambiente dell'account."""
    environment = {key.upper(): value for key, value in original.items()}
    for key in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM",
                "QT_QPA_PLATFORM_PLUGIN_PATH", "QML2_IMPORT_PATH", "QML_IMPORT_PATH"):
        environment.pop(key, None)
    environment["PATH"] = str(Path(environment["SYSTEMROOT"]) / "System32")
    environment["LOCALAPPDATA"] = str(workspace / "appdata")
    return environment


def launch(executable, workspace):
    executable, workspace = executable.resolve(), workspace.resolve()
    if not executable.is_file():
        raise ValueError("Eseguibile assente")
    workspace.mkdir(parents=True, exist_ok=True)
    environment = isolated_environment(os.environ, workspace)
    report_path = workspace / f"process-{time.time_ns()}.json"
    started = time.perf_counter()
    process = subprocess.Popen([str(executable)], cwd=workspace, env=environment,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    report = {"kind": "compiled-process", "pid": process.pid, "executable": str(executable),
              "localappdata": environment["LOCALAPPDATA"], "sample_interval_seconds": 0.1,
              "peak_working_set_bytes": 0, "peak_pagefile_bytes": 0}
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"PID {process.pid}; report {report_path}", flush=True)

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x410, False, process.pid)
    if not handle:
        process.wait()
        raise ctypes.WinError()
    memory = ctypes.WinDLL("psapi").GetProcessMemoryInfo
    memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    try:
        while process.poll() is None:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if memory(handle, ctypes.byref(counters), counters.cb):
                report["peak_working_set_bytes"] = max(report["peak_working_set_bytes"], counters.PeakWorkingSetSize)
                report["peak_pagefile_bytes"] = max(report["peak_pagefile_bytes"], counters.PeakPagefileUsage)
            time.sleep(0.1)
    finally:
        kernel.CloseHandle(handle)
    report.update(exit_code=process.returncode, session_seconds=time.perf_counter() - started)
    report["limits"] = "Durata intera sessione incluse attese umane; non tempo di build/query. Picco campionato ogni 100 ms."
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return process.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    raise SystemExit(launch(args.executable, args.workspace))
