"""T08: controlli del carico sintetico e del runner ridotto."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


EXPERIMENTS = Path(__file__).resolve().parents[3] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))
import v2_benchmark as benchmark
from run_v2_benchmark import percentile95


def test_corpus_reproducible_and_detects_damage(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    first = benchmark.generate(a, "smoke")
    assert first == benchmark.generate(b, "smoke")
    assert benchmark.verify(a) == first
    assert first["expected_text_bytes"] >= .99 * first["target_text_bytes"]
    assert {Path(e["path"]).suffix for e in first["files"]} == {".txt", ".md", ".pdf"}
    target = a / "source" / first["files"][0]["path"]
    target.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Hash diverso"):
        benchmark.verify(a)
    target.unlink()
    with pytest.raises(ValueError, match="mancanti"):
        benchmark.verify(a)


def test_expected_paths_are_independent_of_search(tmp_path):
    manifest = benchmark.generate(tmp_path / "corpus", "smoke")
    assert len(benchmark.expected_paths(manifest, "marcatoremedio", "content")) == 2
    assert benchmark.expected_paths(manifest, "documento marcatoreuniversale", "both") == []
    assert percentile95(list(range(1, 101))) == 95


def test_smoke_runner_complete(tmp_path):
    corpus = tmp_path / "corpus"
    benchmark.generate(corpus, "smoke")
    result = tmp_path / "result"
    completed = subprocess.run([sys.executable, str(EXPERIMENTS / "run_v2_benchmark.py"),
                                "run", str(corpus), str(result), "--cycles", "1",
                                "--samples", "3", "--warmups", "1"],
                               capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    report = json.loads((result / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    phases = {event["phase"]: event for event in report["cycles"][0]}
    assert set(phases) == {"build", "reopen", "nochange", "queries", "incremental"}
    assert abs(phases["build"]["actual_text_bytes"] / 24_000 - 1) <= .01
    assert len(phases["queries"]["queries"]) == len(benchmark.QUERIES) + 6
    assert {(item["query"], item["field"]) for item in phases["queries"]["queries"]} >= {
        ("marcatoremed*", "content"), ("marcatorerar*", "content"),
        ("frasecom*", "content"), ("marcatoreme", "suggest"),
    }
    assert phases["reopen"]["process_to_search_ready_seconds"] > 0
    assert not (result / "cycle-1" / "storage").exists()
    assert phases["incremental"]["storage_bytes"] > 0


def test_runner_refuses_tampered_corpus(tmp_path):
    corpus = tmp_path / "corpus"
    manifest = benchmark.generate(corpus, "smoke")
    (corpus / "source" / manifest["files"][0]["path"]).write_bytes(b"tampered")
    result = tmp_path / "result"
    completed = subprocess.run([sys.executable, str(EXPERIMENTS / "run_v2_benchmark.py"),
                                "run", str(corpus), str(result), "--cycles", "1"],
                               capture_output=True, text=True, timeout=60)
    assert completed.returncode != 0
    assert not result.exists()


def test_runner_does_not_pass_without_cycles(tmp_path):
    corpus = tmp_path / "corpus"
    benchmark.generate(corpus, "smoke")
    result = tmp_path / "result"
    completed = subprocess.run([sys.executable, str(EXPERIMENTS / "run_v2_benchmark.py"),
                                "run", str(corpus), str(result), "--cycles", "0"],
                               capture_output=True, text=True, timeout=60)
    assert completed.returncode != 0
    assert not result.exists()
