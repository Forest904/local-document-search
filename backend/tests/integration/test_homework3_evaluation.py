"""Esempi manuali per oracolo e metriche sperimentali."""
import importlib.util
from collections import Counter
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


def load(name):
    path = Path(__file__).resolve().parents[3] / "experiments" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load("homework3_scan")
metrics = load("homework3_metrics")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "experiments"))
try:
    evaluation = load("homework3_evaluate")
    relevance = load("homework3_relevance")
    summary = load("homework3_summary")
finally:
    sys.path.pop(0)


def test_unicode_filename_and_extension():
    assert oracle.tokens("HTTPServer2026Caffè", True) == ["http", "server", "2026", "caffè"]
    assert oracle.tokens("caffe\u0300 l’acqua") == ["caffè", "l", "acqua"]
    assert not oracle.matches("Report.txt", "", "txt", "filename")


def test_whole_field_and_phrase():
    assert not oracle.matches("machine.txt", "deep learning", 'machine "deep learning"', "both")
    assert oracle.matches("x.txt", "machine deep learning", 'machine "deep learning"', "both")
    assert not oracle.matches("x.txt", "data mining data", '"data data"', "content")
    assert oracle.matches("x.txt", "data data", '"data data"', "content")


@pytest.mark.parametrize("query", ["", '"abc', '""', "!!!"])
def test_invalid_query(query):
    with pytest.raises(ValueError):
        oracle.matches("x.txt", "abc", query, "both")


def test_metrics_manual():
    row = metrics.score({1, 2}, {2, 3})
    assert (row["tp"], row["fp"], row["fn"]) == (1, 1, 1)
    assert row["f1"] == 0.5
    empty = metrics.score([], [])
    assert empty["precision"] is None and empty["exact"]
    summary = metrics.aggregate([row, empty])
    assert summary["valid_cases"] == dict(precision=1, recall=1, f1=1)
    assert summary["exact_set_fraction"] == 0.5


def test_clause_boundaries_and_combining_marks():
    assert oracle.tokens("a\u0338B", True) == ["a\u0338", "b"]
    assert oracle.matches("x.txt", "abc", "abc !!!", "content")
    with pytest.raises(ValueError):
        oracle.matches("x.txt", "abc", 'abc "!!!"', "content")
    assert oracle.source_name(".txt") == ""
    assert oracle.source_name("a.csv") == "a.csv"
    assert oracle.tokens("OR NOT") == ["or", "not"]


@pytest.mark.parametrize("wanted,actual,precision,recall,f1", [
    ([], [1], 0, None, 0), ([1], [], None, 0, 0), ([], [], None, None, None),
])
def test_zero_denominators(wanted, actual, precision, recall, f1):
    row = metrics.score(wanted, actual)
    assert (row["precision"], row["recall"], row["f1"]) == (precision, recall, f1)


def test_micro_is_computed_from_counts():
    result = metrics.aggregate([metrics.score([1], [2, 3]), metrics.score([1, 2, 3], [1])])
    assert result["micro"] == dict(tp=1, fp=2, fn=3, precision=1/3, recall=1/4, f1=2/7)


def make_corpus(root, count=61, real=False):
    entries = []
    for i in range(count):
        name = f"doc{i:03}.txt"
        data = b"alpha beta alpha\n"
        (root / "txt").mkdir(parents=True, exist_ok=True)
        (root / "txt" / name).write_bytes(data)
        row = dict(path=name, bytes=len(data), sha256=evaluation.digest(data))
        if real:
            fmt = ".pdf" if i < 40 else ".txt" if i < 50 else ".md"
            original = f"originals/doc{i:03}{fmt}"
            (root / "originals").mkdir(exist_ok=True)
            (root / original).write_bytes(data)
            row = dict(path=f"doc{i:03}{fmt}", format=fmt, status="converted",
                       original_path=original, source_sha256=evaluation.digest(data),
                       txt_path="txt/" + name, txt_bytes=len(data), txt_sha256=evaluation.digest(data))
        entries.append(row)
    pairs = [(e["txt_path"], e["txt_sha256"]) if real else (e["path"], e["sha256"]) for e in entries]
    manifest = dict(entries=entries, corpus_id=evaluation.digest(json.dumps(pairs, separators=(",", ":")).encode()))
    if not real:
        manifest["profile"] = "test"
    evaluation.save_new(root / ("metadata/manifest.json" if real else "manifest.json"), manifest)
    return entries


def draft_queries(tmp_path):
    queries = [dict(id=f"Q{i}", field=field, query="alpha")
               for i, field in enumerate(["filename"] * 10 + ["content"] * 15 + ["both"] * 5)]
    path = tmp_path / "draft.json"
    evaluation.save_new(path, dict(author="test fixture", queries=queries, manual_checks=[
        dict(query_id="Q10", document="doc000.txt", expected=True, reason="Testo letterale alpha beta alpha")]))
    return path


def test_freeze_and_full_pagination(tmp_path):
    root = tmp_path / "corpus"
    make_corpus(root)
    draft = draft_queries(tmp_path)
    frozen = tmp_path / "frozen.json"
    evaluation.freeze_lexical(root, draft, frozen)
    report = evaluation.evaluate_lexical(frozen, tmp_path / "report.json")
    assert report["passed"]
    assert report["summary"]["exact_sets"] == 30
    assert len(report["rows"][10]["actual"]) == 61
    with pytest.raises(FileExistsError):
        evaluation.freeze_lexical(root, draft, frozen)
    (root / "txt/doc000.txt").write_text("changed")
    with pytest.raises(ValueError, match="alterato"):
        evaluation.evaluate_lexical(frozen, tmp_path / "bad.json")


def test_frozen_artifact_tampering_and_missing_expected(tmp_path):
    root = tmp_path / "corpus"
    make_corpus(root, 1)
    frozen = tmp_path / "frozen.json"
    data = evaluation.freeze_lexical(root, draft_queries(tmp_path), frozen)
    data["expected"] = {}
    frozen.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="alterato"):
        evaluation.evaluate_lexical(frozen, tmp_path / "bad.json")
    data.pop("artifact_sha256")
    evaluation.seal(tmp_path / "missing.json", data)
    with pytest.raises(ValueError, match="Attesi mancanti"):
        evaluation.evaluate_lexical(tmp_path / "missing.json", tmp_path / "bad.json")


def test_empty_corpus_does_not_hide_invalid_query(tmp_path):
    with pytest.raises(ValueError):
        oracle.scan(tmp_path, [dict(id="bad", query='""', field="content")])


def test_sample_and_unapproved_judgments_gate(tmp_path):
    root = tmp_path / "real"
    entries = make_corpus(root, 60, real=True)
    subjects = {e["path"]: dict(subject="Materia", basis="Fixture sintetica") for e in entries}
    subject_path = tmp_path / "subjects.json"
    evaluation.save_new(subject_path, subjects)
    sample_dir = tmp_path / "sample"
    sample = relevance.prepare_sample(root, subject_path, sample_dir)
    assert Counter(e["format"] for e in sample["entries"]) == relevance.QUOTAS
    assert len({e["document_id"] for e in sample["entries"]}) == 60
    assert relevance.select(entries, subjects) == relevance.select(list(reversed(entries)), subjects)
    needs = [dict(id=f"N{i}", query="alpha", field="content", need="Esempio",
                  criterion="Presenza di spiegazione", include="Caso", exclude="Solo titolo") for i in range(10)]
    draft = tmp_path / "needs.json"
    evaluation.save_new(draft, dict(sample_sha256=sample["artifact_sha256"], needs=needs))
    approval_path = tmp_path / "approval.json"
    record = dict(decision="approved", role="user", author="synthetic test user", date="test",
                  evidence="synthetic fixture, not a real approval", target_sha256=evaluation.digest(draft.read_bytes()))
    evaluation.save_new(approval_path, record)
    needs_path = tmp_path / "needs-frozen.json"
    relevance.freeze_needs(sample_dir / "sample.json", draft, approval_path, needs_path)
    batches = tmp_path / "batches"
    relevance.prepare_batches(sample_dir / "sample.json", needs_path, batches)
    with pytest.raises(ValueError, match="incompleto"):
        relevance.freeze_judgments(sample_dir / "sample.json", needs_path, batches,
                                   approval_path, tmp_path / "judgments.json")
    for file in sorted(batches.glob("*.json")):
        batch = evaluation.read_json(file)
        for row in batch["judgments"]:
            row.update(relevant=True, state="reviewed", reason="Synthetic alpha", reference="line 1",
                       original_review="synthetic text fixture", reviewer="test")
        file.write_text(json.dumps(batch))
    with pytest.raises(ValueError, match="approvazione"):
        relevance.freeze_judgments(sample_dir / "sample.json", needs_path, batches,
                                   approval_path, tmp_path / "judgments.json")
    rows = [evaluation.read_json(p) for p in sorted(batches.glob("*.json"))]
    record["target_sha256"] = evaluation.identity(rows)
    approval_path.write_text(json.dumps(record))
    judgments = tmp_path / "judgments.json"
    relevance.freeze_judgments(sample_dir / "sample.json", needs_path, batches, approval_path, judgments)
    report = relevance.evaluate_relevance(sample_dir / "sample.json", needs_path, judgments, tmp_path / "report.json")
    assert report["summary"]["exact_sets"] == 10
    (sample_dir / "txt/doc000.txt").write_text("tampered")
    with pytest.raises(ValueError, match="Campione alterato"):
        relevance.check_sample(sample_dir / "sample.json")


def test_scanner_uses_basename_and_strict_utf8(tmp_path):
    folder = tmp_path / "secret"
    folder.mkdir()
    file = folder / "HTTPServer42.TXT"
    file.write_bytes(b"\xef\xbb\xbfalpha beta\n")
    queries = [dict(id="Q01", field="filename", query="secret"),
               dict(id="Q02", field="filename", query='"http server 42"'),
               dict(id="Q03", field="content", query='"alpha beta"')]
    assert oracle.scan(tmp_path, queries) == {"Q01": [], "Q02": ["secret/HTTPServer42.TXT"],
                                             "Q03": ["secret/HTTPServer42.TXT"]}
    file.write_bytes(b"\xff")
    with pytest.raises(UnicodeDecodeError):
        oracle.scan(tmp_path, queries)


@pytest.mark.parametrize("mode", ["snapshot", "total", "duplicate", "empty", "order"])
def test_pagination_rejects_inconsistent_response(mode):
    calls = []
    def execute(request):
        calls.append(request)
        if mode == "empty":
            paths, total = [], 1
        elif mode == "duplicate":
            paths, total = ["a", "a"], 2
        elif mode == "order":
            paths, total = ["b", "a"], 2
        else:
            paths, total = (["a"], 2) if len(calls) == 1 else (["b"], 3)
        return SimpleNamespace(snapshot_id="other" if mode == "snapshot" else "s",
            total_matches=total, results=[SimpleNamespace(relative_path=SimpleNamespace(value=p)) for p in paths])
    with pytest.raises(ValueError):
        evaluation.retrieve(SimpleNamespace(search=SimpleNamespace(execute=execute)),
                            dict(query="alpha", field="content"), "s")


def test_public_summary_does_not_export_private_data(tmp_path):
    local = tmp_path / "local.json"
    evaluation.seal(local, dict(kind="lexical_report", corpus_id="a" * 64,
        query="PRIVATE QUERY", summary={"private": "PRIVATE PATH"},
        rows=[dict(id="Q01", field="content", expected=["PRIVATE PATH"], actual=[],
                   metrics=metrics.score(["PRIVATE PATH"], []))]))
    public = tmp_path / "public.json"
    result = summary.public_summary([local], public)
    assert "PRIVATE" not in public.read_text()
    assert result["results"][0]["summary"]["micro"]["fn"] == 1
    with pytest.raises(ValueError, match="duplicati"):
        summary.public_summary([local, local], tmp_path / "duplicates.json")
    with pytest.raises(FileExistsError):
        summary.public_summary([local], public)


def test_missing_or_agent_approval_rejected():
    for record in ({}, dict(decision="approved", role="agent", target_sha256="x",
                            author="agent", date="test", evidence="self-approved")):
        with pytest.raises(ValueError, match="approvazione"):
            relevance.approval(record, "x")
