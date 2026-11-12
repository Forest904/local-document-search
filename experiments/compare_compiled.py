"""Run the local compiled V2-02 comparison, alternating versions by cycle."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from run_v2_benchmark import evaluate_budgets


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conditions():
    battery = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Battery | Select-Object BatteryStatus,EstimatedChargeRemaining | ConvertTo-Json -Compress"],
        text=True).strip()
    power = subprocess.check_output(["powercfg", "/getactivescheme"], text=True).strip()
    return {"battery": json.loads(battery) if battery else None, "power_scheme": power,
            "cache": "OS cache not cleared"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("executable_021", type=Path)
    parser.add_argument("executable_022", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output già esistente")
    args.output.mkdir(parents=True)
    sequence = ("021", "022", "022", "021", "021", "022")
    executables = {"021": args.executable_021.resolve(),
                   "022": args.executable_022.resolve()}
    reports = {version: [] for version in executables}
    records = []
    for index, version in enumerate(sequence, 1):
        executable = executables[version]
        output = args.output / f"run-{index}-{version}"
        storage = Path(os.environ["TEMP"]) / f"lds-v2-compare-{os.getpid()}-{index}"
        before = conditions()
        if before["battery"] and before["battery"]["BatteryStatus"] == 1:
            raise RuntimeError("Alimentazione scollegata: confronto interrotto")
        started = time.time()
        completed = subprocess.run(
            [str(executable), "--diagnostic", str(args.corpus.resolve()),
             str(output.resolve()), "--storage-root", str(storage),
             "--cycles", "1", "--samples", "100", "--warmups", "5"],
            capture_output=True, text=True)
        record = {"index": index, "version": version, "executable": str(executable),
                  "executable_sha256": sha256(executable), "started": started,
                  "finished": time.time(), "conditions_before": before,
                  "conditions_after": conditions(), "returncode": completed.returncode,
                  "stderr": completed.stderr[-2000:], "report": str(output / "report.json")}
        records.append(record)
        (args.output / "sequence.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        if not (output / "report.json").is_file():
            raise RuntimeError(f"Report mancante: {record}")
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        if completed.returncode or report["status"] != "PASS":
            raise RuntimeError(f"Ciclo fallito: {record}, {report.get('error')}")
        reports[version].append(report)
    for version, items in reports.items():
        combined = {key: value for key, value in items[0].items() if key not in ("cycles", "budgets", "budget_status")}
        if any(item["revision"] != combined["revision"] or item["corpus_id"] != combined["corpus_id"]
               for item in items):
            raise ValueError("Revisioni o corpus discordanti")
        combined["cycles"] = [item["cycles"][0] for item in items]
        combined["budgets"], combined["budget_status"] = evaluate_budgets(combined)
        (args.output / f"combined-{version}.json").write_text(
            json.dumps(combined, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
