"""Checks release versions and prepares a shareable installer manifest."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts/package"
VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
PUBLIC_MANIFEST_KEYS = (
    "installer_sha256", "installer_version", "iscc_version", "iscc_sha256",
    "payload_manifest_sha256", "revision", "dirty_worktree",
    "installer_source_sha256",
)


def _literal_assignment(path: Path, name: str) -> str:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            if isinstance(value, str):
                return value
    raise ValueError(f"Assegnazione {name} mancante in {path}")


def _one_match(path: Path, pattern: str) -> str:
    matches = re.findall(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Versione mancante o ambigua in {path}")
    return matches[0]


def release_version(root: Path = ROOT) -> str:
    backend = tomllib.loads((root / "backend/pyproject.toml").read_text(encoding="utf-8"))
    frontend = tomllib.loads((root / "frontend/pyproject.toml").read_text(encoding="utf-8"))
    version = backend["project"]["version"]
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Versione non valida: {version}")
    values = {
        "frontend": frontend["project"]["version"],
        "dipendenza backend": _one_match(root / "frontend/pyproject.toml", r"local-document-search==(\d+\.\d+\.\d+)"),
        "builder": _literal_assignment(root / "scripts/package/build.py", "INSTALLER_VERSION"),
        "Inno AppVersion": _one_match(root / "scripts/package/installer.iss", r'^#define AppVersion "(\d+\.\d+\.\d+)"'),
        "Inno output": _one_match(root / "scripts/package/installer.iss", r'^OutputBaseFilename=LocalDocumentSearch-(\d+\.\d+\.\d+)-windows-x64-setup$'),
        "istruzioni": _one_match(root / "scripts/package/ISTRUZIONI.txt", r'^Local Document Search (\d+\.\d+\.\d+)'),
        "termini IT": _one_match(root / "scripts/package/TERMS-IT.txt", r'^Condizioni d.uso di Local Document Search (\d+\.\d+\.\d+)'),
        "termini EN": _one_match(root / "scripts/package/TERMS-EN.txt", r'^Local Document Search (\d+\.\d+\.\d+) Terms of Use'),
    }
    audit = root / "scripts/package/payload_audit.py"
    values["payload audit licenze"] = _one_match(audit, r'^\s*version, license_id = "(\d+\.\d+\.\d+)", "Various; see file"')
    values["payload audit app"] = _one_match(audit, r'"local-document-search", "(\d+\.\d+\.\d+)"')
    for label, found in values.items():
        if found != version:
            raise ValueError(f"Versione incoerente ({label}={found}, backend={version})")
    return version


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def public_manifest(source: Path, destination: Path, *, expected_revision: str,
                    expected_version: str, expected_installer_sha256: str) -> dict:
    original = json.loads(source.read_text(encoding="utf-8"))
    if original["revision"] != expected_revision or original["installer_version"] != expected_version:
        raise ValueError("Revisione o versione del manifest non corrisponde")
    if original["dirty_worktree"] is not False:
        raise ValueError("Manifest da working tree modificato")
    if original["installer_sha256"] != expected_installer_sha256:
        raise ValueError("SHA-256 del manifest non corrisponde all'installer")
    if set(PUBLIC_MANIFEST_KEYS) - original.keys():
        raise ValueError("Campi di provenienza mancanti nel manifest")
    public = {key: original[key] for key in PUBLIC_MANIFEST_KEYS}
    destination.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return public


def verify_installer(dist: Path, *, revision: str, version: str) -> Path:
    name = f"LocalDocumentSearch-{version}-windows-x64-setup.exe"
    installer = dist / name
    expected = sha256(installer)
    checksum = (dist / f"{name}.sha256").read_text(encoding="ascii").strip()
    if checksum != f"{expected}  {name}":
        raise ValueError("SHA-256 esterno non corrisponde all'installer")
    public_path = dist / "public" / f"{name}.manifest.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_manifest(dist / f"{name}.manifest.json", public_path,
                    expected_revision=revision, expected_version=version,
                    expected_installer_sha256=expected)
    return public_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("version", "verify"))
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--revision")
    args = parser.parse_args()
    version = release_version()
    if args.action == "version":
        print(version)
    else:
        if not args.revision or not re.fullmatch(r"[0-9a-f]{40}", args.revision):
            parser.error("--revision deve essere un commit SHA completo")
        print(verify_installer(args.dist, revision=args.revision, version=version))


if __name__ == "__main__":
    main()
