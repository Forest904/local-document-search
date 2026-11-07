"""T20 e preparazione T21: corpus funzionale separato dai benchmark."""
import hashlib
import os
from pathlib import Path
import sys

import pytest


EXPERIMENTS = Path(__file__).resolve().parents[3] / "experiments"
sys.path.insert(0, str(EXPERIMENTS))
import v2_corpus as corpus


def test_synthetic_reproducible_and_complete(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    manifest, queries = corpus.generate_synthetic(first)
    second_manifest, second_queries = corpus.generate_synthetic(second)
    assert manifest == second_manifest
    assert queries == second_queries
    assert corpus.validate(manifest, queries, first / "source")["passed"]
    for entry in manifest["files"]:
        a = (first / "source" / entry["path"]).read_bytes()
        b = (second / "source" / entry["path"]).read_bytes()
        assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest() == entry["sha256"]


def test_synthetic_detects_missing_and_changed_file(tmp_path):
    manifest, queries = corpus.generate_synthetic(tmp_path / "corpus")
    source = tmp_path / "corpus" / "source"
    target = source / manifest["files"][0]["path"]
    target.write_bytes(b"alterato")
    report = corpus.validate(manifest, queries, source)
    assert not report["passed"] and not report["complete"]
    assert report["problems"][0]["reason"] == "hash diverso"
    target.unlink()
    assert "mancante" in corpus.verify_files(manifest, source)[0]["reason"]


def test_real_manifest_and_missing_ground_truth(tmp_path):
    manifest = corpus.load_manifest()
    assert {item["format"] for item in manifest["files"]} == {"txt", "md", "pdf"}
    assert {item["language"] for item in manifest["files"]} == {"it", "en"}
    assert corpus.main(["validate-real", str(tmp_path)]) == 1


def test_real_query_schema_rejects_wrong_version_and_unknown_path(tmp_path):
    import json
    manifest = corpus.load_manifest()
    case = {"query": "esempio", "field": "content", "expected": ["sconosciuto.txt"], "ambiguities": []}
    path = tmp_path / "queries.json"
    data = {"schema": 1, "corpus_id": "wrong", "queries": [case]}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="versione"):
        corpus.load_queries(path, manifest)
    data["corpus_id"] = corpus.corpus_id(manifest)
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Attesi"):
        corpus.load_queries(path, manifest)


def test_fetch_preserves_invalid_cache_and_rejects_changed_download(tmp_path, monkeypatch):
    from io import BytesIO
    expected = b"approvato"
    entry = {"path": "doc.txt", "url": "https://example.test/doc.txt",
             "sha256": corpus.digest(expected)}
    manifest = {"files": [entry]}
    source = tmp_path / "source"
    source.mkdir()
    target = source / "doc.txt"
    target.write_bytes(b"cache alterata")
    monkeypatch.setattr(corpus, "urlopen", lambda *args, **kwargs: pytest.fail("Rete usata con cache alterata"))
    assert corpus.fetch(manifest, source)[0]["status"] == "invalid-cache"
    assert target.read_bytes() == b"cache alterata"
    target.unlink()
    monkeypatch.setattr(corpus, "urlopen", lambda *args, **kwargs: BytesIO(b"sorgente cambiato"))
    assert corpus.fetch(manifest, source)[0]["status"] == "hash-mismatch"
    assert not target.exists()


@pytest.mark.skipif(not os.environ.get("LDS_V2_REAL_CORPUS"), reason="Suite reale opt-in")
def test_real_corpus_opt_in():
    source = Path(os.environ["LDS_V2_REAL_CORPUS"])
    manifest = corpus.load_manifest()
    queries = corpus.load_queries(corpus.REAL_QUERIES, manifest)
    report = corpus.validate(manifest, queries, source)
    assert report["complete"], report["problems"]
    assert report["passed"], report["cases"]
