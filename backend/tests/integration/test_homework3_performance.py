"""Pilot piccolo: correttezza, timeout e output pubblico senza dati personali."""
import json
from pathlib import Path
import sys

import pytest

from test_homework3_evaluation import draft_queries, evaluation, make_corpus

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "experiments"))
try:
    import homework3_performance as pilot
finally:
    sys.path.pop(0)


def frozen_fixture(tmp_path, count=61):
    root = tmp_path / "corpus"
    make_corpus(root, count)
    frozen = tmp_path / "frozen.json"
    evaluation.freeze_lexical(root, draft_queries(tmp_path), frozen)
    return frozen


def test_pilot_full_retrieval_and_public_summary(tmp_path, monkeypatch):
    frozen = frozen_fixture(tmp_path)
    monkeypatch.setattr(pilot, "hardware", lambda: {})
    report = pilot.run(frozen, tmp_path / "run")
    assert report["complete"] and report["correct"] and not report["timeout"]
    assert len(report["samples"]) == 240
    assert report["integrity_after"]
    public = pilot.summarize(report)
    assert public["queries"][10]["index"]["n"] == 3
    assert public["by_field"]["content"]["scan"]["n"] == 45
    encoded = json.dumps(public)
    assert "alpha" not in encoded and "doc000" not in encoded
    assert str(tmp_path) not in encoded and "query\"" not in encoded
    with pytest.raises(FileExistsError):
        pilot.run(frozen, tmp_path / "run")


def test_scan_reopens_files_per_query(tmp_path, monkeypatch):
    (tmp_path / "doc.txt").write_text("alpha", encoding="utf-8")
    original = Path.read_text
    reads = []
    def read(path, *args, **kwargs):
        reads.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read)
    query = dict(id="Q", field="content", query="alpha")
    assert pilot.scan(tmp_path, [query])["Q"] == ["doc.txt"]
    (tmp_path / "doc.txt").write_text("beta", encoding="utf-8")
    assert pilot.scan(tmp_path, [query])["Q"] == []
    assert len(reads) == 2


def test_timeout_preserves_samples(tmp_path, monkeypatch):
    frozen = frozen_fixture(tmp_path, 1)
    monkeypatch.setattr(pilot, "hardware", lambda: {})
    elapsed = [0]
    original = pilot.retrieve
    def retrieve(*args):
        result = original(*args)
        elapsed[0] = 601
        return result
    monkeypatch.setattr(pilot, "retrieve", retrieve)
    report = pilot.run(frozen, tmp_path / "run", clock=lambda: elapsed[0])
    assert report["timeout"] and not report["complete"]
    assert len(report["samples"]) == 1 and len(report["missing"]) == 239
    assert len((tmp_path / "run/samples.jsonl").read_text().splitlines()) == 1
    assert report["integrity_after"]


def test_mismatch_retained_and_statistics(tmp_path, monkeypatch):
    frozen = frozen_fixture(tmp_path, 1)
    monkeypatch.setattr(pilot, "hardware", lambda: {})
    monkeypatch.setattr(pilot, "retrieve", lambda *args: ["unexpected.txt"])
    report = pilot.run(frozen, tmp_path / "run")
    assert report["complete"] and not report["correct"]
    assert report["samples"][0]["false_positives"] == ["unexpected.txt"]
    for sample in report["samples"]:
        sample["seconds"] = sample["pass"] * (2 if sample["method"] == "scan" else 1)
    public = pilot.summarize(report)
    assert public["queries"][0]["index"] == dict(n=3, median=2, min=1, max=3)
    assert public["queries"][0]["scan_over_index"] == 2
    assert public["by_field"]["content"]["ratios"]["median"] == 2
    assert pilot.stats([]) == dict(n=0, median=None, min=None, max=None)


def test_query_error_is_reported(tmp_path, monkeypatch):
    frozen = frozen_fixture(tmp_path, 1)
    monkeypatch.setattr(pilot, "hardware", lambda: {})
    def fail(*args):
        raise RuntimeError("local private detail")
    monkeypatch.setattr(pilot, "retrieve", fail)
    report = pilot.run(frozen, tmp_path / "run")
    assert not report["complete"] and not report["correct"]
    assert len(report["missing"]) == 239
    assert "local private detail" not in json.dumps(pilot.summarize(report))
