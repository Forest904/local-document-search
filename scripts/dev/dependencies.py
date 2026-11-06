"""Verifica reale dell'ambiente; pip viene eseguito solo per riparare o installare."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys
import tomllib
from urllib.parse import unquote

from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import canonicalize_name


def locked_versions(lock):
    return dict(line.strip().split("==", 1) for line in lock.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#"))


def projects(repository):
    return [(repository / name, tomllib.loads((repository / name / "pyproject.toml").read_text(encoding="utf-8")))
            for name in ("backend", "frontend")]


def validate_lock(locked, packages):
    versions = {canonicalize_name(name): version for name, version in locked.items()}
    versions.update({canonicalize_name(data["project"]["name"]): data["project"]["version"]
                     for _, data in packages})
    for _, data in packages:
        for raw in data["project"]["dependencies"] + data["build-system"]["requires"]:
            requirement = Requirement(raw)
            if requirement.marker and not requirement.marker.evaluate():
                continue
            version = versions.get(canonicalize_name(requirement.name))
            if version is None or version not in requirement.specifier:
                raise RuntimeError(f"Lock non allineato a pyproject: {raw}. Aggiornare scripts/dev/requirements.lock.txt.")


def missing_versions(locked):
    missing = []
    for name, expected in locked.items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = None
        if installed != expected:
            missing.append(name)
    return missing


def editable_matches(path, data):
    try:
        dist = metadata.distribution(data["project"]["name"])
        direct = json.loads(dist.read_text("direct_url.json") or "{}")
        return (dist.version == data["project"]["version"]
                and direct.get("dir_info", {}).get("editable") is True
                and unquote(direct.get("url", "")).casefold() == unquote(path.as_uri()).casefold())
    except (metadata.PackageNotFoundError, ValueError):
        return False


def dependency_errors():
    """Controlla anche dipendenze transitive senza invocare pip o accedere alla rete."""
    errors = []
    for dist in metadata.distributions():
        for raw in dist.requires or ():
            requirement = Requirement(raw)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            try:
                actual = metadata.version(requirement.name)
            except metadata.PackageNotFoundError:
                actual = None
            if actual is None or actual not in requirement.specifier:
                errors.append(f"{dist.metadata['Name']} richiede {raw}")
    return errors


def fingerprint(repository, lock):
    digest = hashlib.sha256()
    for value in (str(repository), sys.version, lock.read_text(encoding="utf-8"),
                  *(str(path) + (path / "pyproject.toml").read_text(encoding="utf-8")
                    for path, _ in projects(repository))):
        digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def pip(*args):
    subprocess.run([sys.executable, "-m", "pip", "--disable-pip-version-check", *args], check=True)


def prepare(repository):
    repository = repository.resolve()
    lock = repository / "scripts/dev/requirements.lock.txt"
    packages = projects(repository)
    locked = locked_versions(lock)
    validate_lock(locked, packages)
    stamp = Path(sys.prefix) / ".lds-dependencies.json"
    expected = fingerprint(repository, lock)
    try:
        saved = json.loads(stamp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    missing = missing_versions(locked)
    local_stale = saved.get("fingerprint") != expected or not all(editable_matches(*p) for p in packages)
    if not missing and not local_stale and not dependency_errors():
        print("Dipendenze verificate: gia installate; pip saltato.", flush=True)
        return
    if missing:
        print("Installazione/riparazione dipendenze: " + ", ".join(missing), flush=True)
        pip("install", "--no-deps", "-r", str(lock))
    if local_stale:
        print("Aggiornamento pacchetti editable del repository.", flush=True)
        pip("install", "--no-deps", "--no-build-isolation", "-e", str(repository / "backend"),
            "-e", str(repository / "frontend"))
    pip("check")
    # Nuove distribuzioni installate nello stesso processo: metadata rilegge il filesystem.
    errors = dependency_errors()
    if missing_versions(locked) or not all(editable_matches(*p) for p in packages) or errors:
        raise RuntimeError("Ambiente non coerente: " + "; ".join(errors))
    stamp.write_text(json.dumps({"fingerprint": expected}) + "\n", encoding="utf-8")
    print("Ambiente pronto.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    try:
        prepare(parser.parse_args().repository)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
