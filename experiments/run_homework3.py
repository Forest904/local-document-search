"""Corpus sintetico deterministico e misure della CLI reale, senza dati personali.

Dalla radice: backend/.venv/Scripts/python experiments/run_homework3.py
Il JSON su stdout può essere conservato in experiments/results/ (ignorata da Git).
"""
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from tempfile import TemporaryDirectory


CORPUS = {
    "RomaTre.txt": "Roma Tre studia machine deep learning. data data.\n",
    "sub/RomaNote.txt": "Roma antica ospita tre scuole. machine learning.\n",
    "MachineLearning.txt": "modelli statistici\n",
    "machine.txt": "deep learning\n",
    "DataNotes.txt": "data mining data\n",
    "sub/DeepLearning.txt": "deep learning machine\n",
    "Empty.txt": "",
    "Unicode2026.TXT": "L'acqua e il caffè.\n",
}
# Ground truth derivata leggendo il corpus, non dal motore.
QUERIES = [
    ("nome roma", ["RomaTre.txt", "sub/RomaNote.txt"]),
    ("contenuto inesistente", []),
    ("contenuto machine learning", ["RomaTre.txt", "sub/DeepLearning.txt", "sub/RomaNote.txt"]),
    ("contenuto learning machine", ["RomaTre.txt", "sub/DeepLearning.txt", "sub/RomaNote.txt"]),
    ('contenuto "deep learning"', ["RomaTre.txt", "machine.txt", "sub/DeepLearning.txt"]),
    ('contenuto "roma tre"', ["RomaTre.txt"]),
    ('nome "roma tre"', ["RomaTre.txt"]),
    ("contenuto ROMA", ["RomaTre.txt", "sub/RomaNote.txt"]),
    ('contenuto "data data"', ["RomaTre.txt"]),
    ("contenuto learning", ["RomaTre.txt", "machine.txt", "sub/DeepLearning.txt", "sub/RomaNote.txt"]),
]
REGRESSIONS = [
    ('entrambi machine "deep learning"', ["RomaTre.txt", "sub/DeepLearning.txt"]),
    ('machine "deep learning"', ["RomaTre.txt", "sub/DeepLearning.txt"]),
]


def run() -> dict:
    with TemporaryDirectory(prefix="lds-homework3-") as directory:
        root = Path(directory)
        for name, text in CORPUS.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
        cases = QUERIES + REGRESSIONS
        completed = subprocess.run(
            [sys.executable, "-m", "local_document_search.interfaces.cli", str(root)],
            input="\n".join(query for query, _ in cases) + "\n",
            capture_output=True, text=True, encoding="utf-8",
            env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True,
        )
        if completed.stderr:
            raise RuntimeError(completed.stderr)
        header = re.search(
            r"File scoperti: (\d+); indicizzati: (\d+); esclusi: (\d+); byte: (\d+); tempo build: ([0-9.]+) s",
            completed.stdout,
        )
        if header is None:
            raise RuntimeError("Statistiche build mancanti")
        chunks = completed.stdout.split("query> ")[1:-1]
        if len(chunks) != len(cases):
            raise RuntimeError("Numero risposte CLI inatteso")
        rows = []
        for (query, expected), chunk in zip(cases, chunks):
            actual = re.findall(r"^  (.+) \[.+\]$", chunk, re.MULTILINE)
            total = int(re.search(r"Risultati: (\d+)", chunk).group(1))
            rows.append(dict(query=query, expected=expected, actual=actual, total=total,
                             passed=actual == expected and total == len(expected)))
        return dict(
            corpus_version=1, platform=platform.platform(), python=platform.python_version(),
            processor=platform.processor(), discovered=int(header[1]), indexed=int(header[2]),
            excluded=int(header[3]), processed_bytes=int(header[4]), elapsed=float(header[5]),
            measurement="Build iniziale completo nella CLI; un'esecuzione, cache OS non controllata",
            queries=rows[:10], regressions=rows[10:],
            passed=all(row["passed"] for row in rows), transcript=completed.stdout,
        )


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
