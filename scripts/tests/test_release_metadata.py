"""Release gate: coherent versions and public provenance without local paths."""

import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/package"))
import release_metadata


def test_version_gate_rejects_inconsistent_frontend(tmp_path):
    names = (
        "backend/pyproject.toml", "frontend/pyproject.toml", "scripts/package/build.py",
        "scripts/package/installer.iss", "scripts/package/ISTRUZIONI.txt",
        "scripts/package/TERMS-IT.txt", "scripts/package/TERMS-EN.txt",
        "scripts/package/payload_audit.py",
    )
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    assert release_metadata.release_version(tmp_path) == "0.2.2"
    frontend = tmp_path / "frontend/pyproject.toml"
    frontend.write_text(frontend.read_text(encoding="utf-8").replace(
        'version = "0.2.2"', 'version = "0.2.0"', 1), encoding="utf-8")
    with pytest.raises(ValueError, match="Versione incoerente"):
        release_metadata.release_version(tmp_path)


def test_public_manifest_preserves_identity_without_private_paths(tmp_path):
    name = "LocalDocumentSearch-0.2.0-windows-x64-setup.exe"
    installer = tmp_path / name
    installer.write_bytes(b"synthetic installer")
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    (tmp_path / f"{name}.sha256").write_text(f"{digest}  {name}\n", encoding="ascii")
    private = {
        "installer_sha256": digest, "installer_version": "0.2.0",
        "iscc_version": "6.7.3", "iscc_sha256": "a" * 64,
        "payload_manifest_sha256": "b" * 64, "revision": "c" * 40,
        "dirty_worktree": False, "installer_source_sha256": {"build.py": "d" * 64},
        "iscc_path": "C:/Users/test/ISCC.exe", "command": ["C:/Users/test/ISCC.exe"],
    }
    source = tmp_path / f"{name}.manifest.json"
    source.write_text(json.dumps(private), encoding="utf-8")
    public_path = release_metadata.verify_installer(tmp_path, revision="c" * 40, version="0.2.0")
    public = json.loads(public_path.read_text(encoding="utf-8"))
    assert public["installer_sha256"] == digest
    assert public["revision"] == "c" * 40
    assert "iscc_path" not in public and "command" not in public
    assert "C:/Users" not in public_path.read_text(encoding="utf-8")
    (tmp_path / f"{name}.sha256").write_text("0" * 64 + f"  {name}\n", encoding="ascii")
    with pytest.raises(ValueError, match="SHA-256 esterno"):
        release_metadata.verify_installer(tmp_path, revision="c" * 40, version="0.2.0")
