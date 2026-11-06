import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "dev/dependencies.py"
spec = importlib.util.spec_from_file_location("dev_dependencies", SOURCE)
dependencies = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependencies)


@pytest.fixture
def repository(tmp_path):
    for name in ("backend", "frontend"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "pyproject.toml").write_text(
            f'[project]\nname="{name}"\nversion="0.1.0"\ndependencies=["example>=1"]\n'
            '[build-system]\nrequires=[]\n', encoding="utf-8")
    lock = tmp_path / "scripts/dev/requirements.lock.txt"
    lock.parent.mkdir(parents=True)
    lock.write_text("example==1.0\n", encoding="utf-8")
    return tmp_path


def test_missing_and_wrong_versions_are_detected(monkeypatch):
    def version(name):
        if name == "absent":
            raise dependencies.metadata.PackageNotFoundError(name)
        return "1.0"
    monkeypatch.setattr(dependencies.metadata, "version", version)
    assert dependencies.missing_versions({"correct": "1.0", "wrong": "2.0", "absent": "1.0"}) == ["wrong", "absent"]


def test_lock_must_satisfy_projects(repository):
    with pytest.raises(RuntimeError, match="Lock non allineato"):
        dependencies.validate_lock({"example": "0.5"}, dependencies.projects(repository))


def test_editable_from_other_clone_is_not_reused(repository, monkeypatch):
    import json
    path, project = dependencies.projects(repository)[0]
    direct = {"url": path.as_uri(), "dir_info": {"editable": True}}
    dist = SimpleNamespace(version="0.1.0", read_text=lambda _: json.dumps(direct))
    monkeypatch.setattr(dependencies.metadata, "distribution", lambda _: dist)
    assert dependencies.editable_matches(path, project)
    direct["url"] = (repository / "another clone").as_uri()
    assert not dependencies.editable_matches(path, project)


def test_warm_start_skips_pip_but_pyproject_change_refreshes(repository, monkeypatch):
    monkeypatch.setattr(dependencies.sys, "prefix", str(repository))
    monkeypatch.setattr(dependencies, "missing_versions", lambda _: [])
    monkeypatch.setattr(dependencies, "editable_matches", lambda *_: True)
    monkeypatch.setattr(dependencies, "dependency_errors", lambda: [])
    calls = []
    monkeypatch.setattr(dependencies, "pip", lambda *args: calls.append(args))
    dependencies.prepare(repository)
    assert calls[0][0] == "install"
    calls.clear()
    dependencies.prepare(repository)
    assert calls == []
    project = repository / "frontend/pyproject.toml"
    project.write_text(project.read_text() + "# modifica configurazione build\n", encoding="utf-8")
    dependencies.prepare(repository)
    assert calls[0][0] == "install"


def test_warm_start_detects_removed_dependency(repository, monkeypatch):
    monkeypatch.setattr(dependencies.sys, "prefix", str(repository))
    missing = []
    monkeypatch.setattr(dependencies, "missing_versions", lambda _: list(missing))
    monkeypatch.setattr(dependencies, "editable_matches", lambda *_: True)
    monkeypatch.setattr(dependencies, "dependency_errors", lambda: [])
    calls = []
    def pip(*args):
        calls.append(args)
        missing.clear()
    monkeypatch.setattr(dependencies, "pip", pip)
    dependencies.prepare(repository)
    calls.clear()
    missing.append("example")
    dependencies.prepare(repository)
    assert "-r" in calls[0]


def test_failed_validation_does_not_write_stamp(repository, monkeypatch):
    monkeypatch.setattr(dependencies.sys, "prefix", str(repository))
    monkeypatch.setattr(dependencies, "missing_versions", lambda _: [])
    monkeypatch.setattr(dependencies, "editable_matches", lambda *_: True)
    monkeypatch.setattr(dependencies, "dependency_errors", lambda: ["example mancante"])
    monkeypatch.setattr(dependencies, "pip", lambda *_: None)
    with pytest.raises(RuntimeError, match="non coerente"):
        dependencies.prepare(repository)
    assert not (repository / ".lds-dependencies.json").exists()
