"""Gate della build release e diagnostica del pacchetto."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/package"))
sys.path.insert(0, str(ROOT / "experiments"))
import build
import run_v2_benchmark as benchmark


def test_release_requires_clean_revision(monkeypatch):
    monkeypatch.setattr(build, "run", lambda *args, **kwargs: argparse.Namespace(stdout=" M frontend/x\n"))
    with pytest.raises(RuntimeError, match="working tree modificato"):
        build.clean_revision()


def test_microsoft_redist_notice_uses_selected_visual_studio(tmp_path):
    notice = tmp_path / "Enterprise/Licenses/1033/Redist.txt"
    notice.parent.mkdir(parents=True)
    notice.write_text("synthetic redistributable list", encoding="utf-8")
    assert build.redist_notice(tmp_path / "Enterprise") == notice
    with pytest.raises(RuntimeError, match="Elenco redistribuibili Microsoft mancante"):
        build.redist_notice(tmp_path / "BuildTools")


def test_packaged_diagnostic_rejects_modified_payload_before_output(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(benchmark, "verify", lambda _: {"count": 1})
    names = ("run_v2_benchmark.py", "v2_benchmark.py", "m9_corpus.py")
    payload = {"revision": "a" * 40, "dirty_worktree": False,
               "files_sha256": {f"diagnostics/{name}": hashlib.sha256(
                   (Path(benchmark.__file__).parent / name).read_bytes()).hexdigest() for name in names}}
    payload["files_sha256"]["diagnostics/v2_benchmark.py"] = "0" * 64
    manifest = tmp_path / "BUILD-MANIFEST.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    args = argparse.Namespace(corpus=corpus, output=tmp_path / "output",
                              storage_root=tmp_path / "storage", payload_manifest=manifest,
                              cycles=1, samples=1, warmups=0, timeout=1)
    with pytest.raises(ValueError, match="Diagnostica alterata"):
        benchmark.run(args)
    assert not args.output.exists()


def test_packaged_diagnostic_rejects_personal_storage(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    monkeypatch.setattr(benchmark, "verify", lambda _: {"count": 1})
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    manifest = tmp_path / "BUILD-MANIFEST.json"
    manifest.write_text('{"revision":"abc","dirty_worktree":false}', encoding="utf-8")
    args = argparse.Namespace(corpus=corpus, output=tmp_path / "output",
                              storage_root=tmp_path / "LocalDocumentSearchV2", payload_manifest=manifest,
                              cycles=1, samples=1, warmups=0, timeout=1)
    with pytest.raises(ValueError, match="Storage personale"):
        benchmark.run(args)
