"""Confini della pulizia Windows nel nuovo percorso pubblico."""
import os
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows installer")


def test_installer_compiles_with_synthetic_payload(tmp_path):
    compiler = Path(os.environ["LOCALAPPDATA"]) / "Programs/Inno Setup 6/ISCC.exe"
    if not compiler.is_file():
        pytest.skip("Inno Setup non disponibile")
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "LocalDocumentSearch.exe").write_bytes(b"synthetic payload, do not install")
    result = subprocess.run(
        [str(compiler), f"/DPayloadDir={payload}", f"/DOutputDir={tmp_path / 'output'}",
         str(ROOT / "scripts/package/installer.iss")],
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "output/LocalDocumentSearch-0.2.0-windows-x64-setup.exe").is_file()


def cleanup(profile):
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(ROOT / "scripts/package/uninstall-data.ps1")],
        env={**os.environ, "LOCALAPPDATA": str(profile)}, capture_output=True, text=True, timeout=30)


def test_uninstall_removes_only_current_data(tmp_path):
    old = tmp_path / "LocalDocumentSearch/control.sqlite3"
    previous = tmp_path / "LocalDocumentSearchV2/control-v2.sqlite3"
    current = tmp_path / "LocalDocumentSearch/Data"
    for marker in (old, previous, current / "control-v2.sqlite3"):
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(b"synthetic")
    result = cleanup(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not current.exists()
    assert old.read_bytes() == previous.read_bytes() == b"synthetic"
    assert cleanup(tmp_path).returncode == 0


@pytest.mark.parametrize("valid_root", [True, False])
def test_upgrade_cleanup_respects_neutral_install_boundary(tmp_path, valid_root):
    root = tmp_path / ("Programs/LocalDocumentSearch" if valid_root else "unrelated")
    root.mkdir(parents=True)
    obsolete = root / "obsolete.txt"
    obsolete.write_bytes(b"synthetic")
    import hashlib
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"files_sha256": {
        "obsolete.txt": hashlib.sha256(b"synthetic").hexdigest()}}))
    (root / "BUILD-MANIFEST.json").write_text(json.dumps({"files_sha256": {"keep.txt": "unused"}}))
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(ROOT / "scripts/package/prune-upgrade.ps1"),
         "-InstallRoot", str(root), "-PreviousManifest", str(previous)],
        env={**os.environ, "LOCALAPPDATA": str(tmp_path)}, capture_output=True, text=True, timeout=30)
    assert (result.returncode == 0) == valid_root, result.stderr
    assert obsolete.exists() != valid_root


@pytest.mark.parametrize("linked_part", ["LocalDocumentSearch", "LocalDocumentSearch/Data"])
def test_cleanup_and_default_storage_refuse_junction_ancestors(tmp_path, monkeypatch, linked_part):
    from local_document_search.application.errors import StorageFailure
    from local_document_search.interfaces.composition import desktop_storage_directory
    profile = tmp_path / "profile"
    target = tmp_path / "outside"
    target.mkdir()
    marker = target / "keep.txt"
    marker.write_bytes(b"preserved")
    link = profile / linked_part
    link.parent.mkdir(parents=True, exist_ok=True)
    code = "New-Item -ItemType Junction -Path $env:TEST_LINK -Target $env:TEST_TARGET | Out-Null"
    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", code],
                            env={**os.environ, "TEST_LINK": str(link), "TEST_TARGET": str(target)},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    try:
        monkeypatch.setenv("LOCALAPPDATA", str(profile))
        with pytest.raises(StorageFailure):
            desktop_storage_directory()
        result = cleanup(profile)
        assert result.returncode != 0
        assert "Reparse point" in result.stderr
        assert marker.read_bytes() == b"preserved"
    finally:
        link.rmdir()  # Removes the junction itself, never its target.
