"""Confini della pulizia Windows nel nuovo percorso pubblico."""
import os
import json
from pathlib import Path
import subprocess
import sys
import uuid

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
    assert (tmp_path / "output/LocalDocumentSearch-0.2.2-windows-x64-setup.exe").is_file()


def test_silent_install_keeps_registered_destination(tmp_path):
    import winreg

    compiler = Path(os.environ["LOCALAPPDATA"]) / "Programs/Inno Setup 6/ISCC.exe"
    if not compiler.is_file():
        pytest.skip("Inno Setup non disponibile")
    package = tmp_path / "package"
    package.mkdir()
    for name in ("TERMS-IT.txt", "TERMS-EN.txt", "prune-upgrade.ps1", "uninstall-data.ps1"):
        (package / name).write_bytes((ROOT / "scripts/package" / name).read_bytes())
    source = (ROOT / "scripts/package/installer.iss").read_text(encoding="utf-8")
    identifier = str(uuid.uuid4()).upper()
    source = source.replace("C6B25744-98A8-4B23-B4CF-3E45CA29944E", identifier)
    source = source.replace("{localappdata}\\Programs\\LocalDocumentSearchV2",
                            str(tmp_path / "no-legacy-install"))
    prune = (package / "prune-upgrade.ps1").read_text(encoding="utf-8")
    (package / "prune-upgrade.ps1").write_text(
        prune.replace("C6B25744-98A8-4B23-B4CF-3E45CA29944E", identifier), encoding="utf-8")
    source = source.replace(
        "{#SourcePath}\\..\\..\\frontend\\src\\local_document_search_desktop\\assets\\luma.ico",
        str(ROOT / "frontend/src/local_document_search_desktop/assets/luma.ico"))
    (package / "installer.iss").write_text(source, encoding="utf-8")
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "LocalDocumentSearch.exe").write_bytes(b"synthetic, do not launch")
    (payload / "BUILD-MANIFEST.json").write_text(json.dumps({"files_sha256": {"keep.txt": "a" * 64}}))
    build = subprocess.run(
        [str(compiler), f"/DPayloadDir={payload}", f"/DOutputDir={tmp_path / 'output'}",
         str(package / "installer.iss")], capture_output=True, text=True, timeout=60)
    assert build.returncode == 0, build.stdout + build.stderr
    installer = tmp_path / "output/LocalDocumentSearch-0.2.2-windows-x64-setup.exe"
    destination = tmp_path / "Custom é folder/LocalDocumentSearch"
    wrong = tmp_path / "other/LocalDocumentSearch"
    registry_key = f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{{identifier}}}_is1"
    try:
        occupied = tmp_path / "occupied"
        occupied.mkdir()
        (occupied / "personal.txt").write_text("keep")
        blocked = subprocess.run(
            [str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NOICONS", f"/DIR={occupied}"],
            capture_output=True, text=True, timeout=60)
        assert blocked.returncode != 0
        assert (occupied / "personal.txt").read_text() == "keep"
        install = subprocess.run(
            [str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NOICONS", f"/DIR={destination}",
             f"/LOG={tmp_path / 'install.log'}"],
            capture_output=True, text=True, timeout=60)
        assert install.returncode == 0, (tmp_path / "install.log").read_text(errors="replace")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key) as key:
            assert Path(winreg.QueryValueEx(key, "InstallLocation")[0]) == destination
        reinstall = subprocess.run(
            [str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NOICONS", f"/DIR={destination}",
             f"/LOG={tmp_path / 'reinstall.log'}"],
            capture_output=True, text=True, timeout=60)
        assert reinstall.returncode == 0, (tmp_path / "reinstall.log").read_text(errors="replace")
        refused = subprocess.run(
            [str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NOICONS", f"/DIR={wrong}",
             f"/LOG={tmp_path / 'refused.log'}"],
            capture_output=True, text=True, timeout=60)
        assert refused.returncode != 0
        assert "An update must use the installed folder" in (tmp_path / "refused.log").read_text()
        assert not wrong.exists()
    finally:
        uninstaller = destination / "unins000.exe"
        if uninstaller.is_file():
            subprocess.run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES"],
                           capture_output=True, text=True, timeout=60)


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
    import winreg
    root = tmp_path / ("Programs/LocalDocumentSearch" if valid_root else "unrelated")
    root.mkdir(parents=True)
    obsolete = root / "obsolete.txt"
    obsolete.write_bytes(b"synthetic")
    import hashlib
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"files_sha256": {
        "obsolete.txt": hashlib.sha256(b"synthetic").hexdigest()}}))
    (root / "BUILD-MANIFEST.json").write_text(json.dumps({"files_sha256": {"keep.txt": "unused"}}))
    registry_key = f"Software\\LocalDocumentSearchTests\\{uuid.uuid4()}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_key) as key:
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ,
                          str(tmp_path / "Programs/LocalDocumentSearch"))
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(ROOT / "scripts/package/prune-upgrade.ps1"),
             "-InstallRoot", str(root), "-PreviousManifest", str(previous),
             "-RegistryKey", registry_key],
            env={**os.environ, "LOCALAPPDATA": str(tmp_path)}, capture_output=True, text=True, timeout=30)
    finally:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_key)
    assert (result.returncode == 0) == valid_root, result.stderr
    assert obsolete.exists() != valid_root


@pytest.mark.parametrize("folder", ["Programs/LocalDocumentSearch", "Custom Folder/LocalDocumentSearch", "Dati é/LocalDocumentSearch"])
def test_upgrade_cleanup_custom_folder_preserves_unowned_files(tmp_path, folder):
    import hashlib
    import winreg

    root = tmp_path / folder
    root.mkdir(parents=True)
    obsolete = root / "obsolete.txt"
    changed = root / "changed.txt"
    foreign = root / "personal.txt"
    for path in (obsolete, changed, foreign):
        path.write_bytes(b"actual")
    old_hash = hashlib.sha256(b"actual").hexdigest()
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"files_sha256": {
        "obsolete.txt": old_hash,
        "changed.txt": hashlib.sha256(b"original").hexdigest()}}))
    (root / "BUILD-MANIFEST.json").write_text(json.dumps({"files_sha256": {"keep.txt": old_hash}}))
    registry_key = f"Software\\LocalDocumentSearchTests\\{uuid.uuid4()}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_key) as key:
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(root))
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(ROOT / "scripts/package/prune-upgrade.ps1"),
             "-InstallRoot", str(root), "-PreviousManifest", str(previous),
             "-RegistryKey", registry_key],
            capture_output=True, text=True, timeout=30)
    finally:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_key)
    assert result.returncode == 0, result.stderr
    assert not obsolete.exists()
    assert changed.read_bytes() == foreign.read_bytes() == b"actual"


@pytest.mark.parametrize("entry", ["../outside.txt", "C:/outside.txt", "bad:name", "normal.txt"])
def test_upgrade_preflight_checks_manifest(tmp_path, entry):
    import winreg

    root = tmp_path / "install"
    root.mkdir()
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"files_sha256": {entry: "x" * 64}}))
    registry_key = f"Software\\LocalDocumentSearchTests\\{uuid.uuid4()}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_key) as key:
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(root))
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(ROOT / "scripts/package/prune-upgrade.ps1"),
             "-InstallRoot", str(root), "-PreviousManifest", str(previous),
             "-RegistryKey", registry_key, "-ValidateOnly"],
            capture_output=True, text=True, timeout=30)
    finally:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_key)
    assert result.returncode != 0


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
