"""Build Windows standalone isolata e archivio con provenienza verificabile."""
import argparse
import configparser
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NAME = "LocalDocumentSearch-0.1.0-windows-x64"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(args, **kwargs):
    print(subprocess.list2cmdline([str(a) for a in args]), flush=True)
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def safe_clean(path):
    resolved = path.resolve()
    if not resolved.is_relative_to((ROOT / "build").resolve()):
        raise ValueError(f"Pulizia fuori da build rifiutata: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def validate_payload(folder):
    required = ["LocalDocumentSearch.exe", "python312.dll", "PySide6/QtCore.pyd",
                "PySide6/QtGui.pyd", "PySide6/QtWidgets.pyd",
                "PySide6/qt-plugins/platforms/qwindows.dll", "ISTRUZIONI.txt",
                "BUILD-MANIFEST.json", "THIRD_PARTY_NOTICES.txt", "licenses/Python.txt"]
    missing = [name for name in required if not (folder / name).is_file()]
    if missing:
        raise RuntimeError(f"Pacchetto incompleto: {missing}")
    forbidden = [p for p in folder.rglob("*")
                 if p.suffix.lower() in {".sqlite", ".sqlite3", ".db"}
                 or p.name in {".env", ".git", "__pycache__"}]
    if forbidden:
        raise RuntimeError(f"Dati non distribuibili: {forbidden}")


def archive(folder, target):
    validate_payload(folder)
    temporary = target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                output.write(path, f"{NAME}/{path.relative_to(folder).as_posix()}")
    with zipfile.ZipFile(temporary) as check:
        if check.testzip() is not None:
            raise RuntimeError("Archivio danneggiato")
    temporary.replace(target)
    target.with_suffix(".zip.sha256").write_text(f"{sha256(target)}  {target.name}\n", encoding="ascii")


def collect_licenses(folder):
    destination = folder / "licenses"
    destination.mkdir(exist_ok=True)
    packages = ["markdown-it-py", "mdurl", "pypdf", "PySide6", "PySide6_Essentials", "shiboken6", "Nuitka"]
    for name in packages:
        dist = metadata.distribution(name)
        output = destination / name
        output.mkdir(exist_ok=True)
        (output / "METADATA.txt").write_text(dist.read_text("METADATA") or "", encoding="utf-8")
        files = [f for f in dist.files or () if any(
            part.lower().startswith(("license", "copying", "copyright", "notice")) for part in f.parts)]
        for number, relative in enumerate(files):
            source = Path(dist.locate_file(relative))
            if source.is_file():
                shutil.copy2(source, output / f"{number:03d}-{source.name}")
    shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", destination / "Python.txt")
    shutil.copytree(HERE / "licenses", destination / "upstream", dirs_exist_ok=True)
    shutil.copy2(HERE / "THIRD_PARTY_NOTICES.txt", folder)


def toolchain():
    locator = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    result = run([locator, "-latest", "-products", "*", "-requires",
                  "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-format", "json"], capture_output=True)
    instances = json.loads(result.stdout.decode("utf-8-sig"))
    if not instances:
        raise RuntimeError("Richiesto Visual Studio 2022 Build Tools con C++ x64")
    instance = instances[0]
    vc = Path(instance["installationPath"]) / "VC/Tools/MSVC"
    compilers = sorted(vc.glob("*/bin/Hostx64/x64/cl.exe"))
    return {"visual_studio": instance["installationVersion"],
            "msvc_installed": sorted(p.name for p in vc.iterdir() if p.is_dir()),
            "x64_compilers": [{"path": str(p), "sha256": sha256(p)} for p in compilers]}


def build():
    if sys.platform != "win32" or sys.version_info[:3] != (3, 12, 2) or platform.machine() != "AMD64":
        raise RuntimeError("Build fissata a CPython 3.12.2 Windows AMD64")
    compiler = toolchain()
    for line in (HERE / "requirements.lock.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, expected = line.split("==")
            if metadata.version(name) != expected:
                raise RuntimeError(f"Versione non bloccata: {name}")
    workspace = ROOT / "build/package"
    safe_clean(workspace)
    workspace.mkdir(parents=True)
    shutil.copy2(HERE / "launcher.py", workspace)
    config = configparser.ConfigParser()
    config.read(HERE / "pysidedeploy.spec", encoding="utf-8")
    config["app"]["project_dir"] = str(workspace)
    config["app"]["exec_directory"] = str(workspace / "output")
    with (workspace / "pysidedeploy.spec").open("w", encoding="utf-8") as output:
        config.write(output)
    command = [Path(sys.executable).with_name("pyside6-deploy.exe"), "-c",
               workspace / "pysidedeploy.spec", "--no-install", "--force", "--keep-deployment-files"]
    with (workspace / "deploy.log").open("w", encoding="utf-8") as log:
        run(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT)
    candidates = list((workspace / "deployment").glob("*.dist"))
    if len(candidates) != 1:
        raise RuntimeError(f"Output standalone inatteso: {candidates}; consultare deploy.log")
    folder = candidates[0]
    shutil.copy2(HERE / "ISTRUZIONI.txt", folder)
    collect_licenses(folder)
    packages = {d.metadata["Name"]: d.version for d in metadata.distributions()}
    revision = run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    sources = {}
    for directory in ("backend/src", "frontend/src", "scripts/package"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                sources[path.relative_to(ROOT).as_posix()] = sha256(path)
    for project in ("backend", "frontend"):
        sources[f"{project}/pyproject.toml"] = sha256(ROOT / project / "pyproject.toml")
    report = workspace / "compilation-report.xml"
    if not report.is_file():
        raise RuntimeError("Report compilatore assente")
    shutil.copy2(report, folder)
    manifest = {"application": NAME, "revision": revision, "dirty_worktree": bool(dirty),
                "python": sys.version, "platform": platform.platform(), "toolchain": compiler,
                "packages": packages, "command": [str(a) for a in command],
                "resolved_spec": (workspace / "pysidedeploy.spec").read_text(encoding="utf-8"),
                "sources_sha256": sources, "lock_sha256": sha256(HERE / "requirements.lock.txt"),
                "files_sha256": {p.relative_to(folder).as_posix(): sha256(p)
                                 for p in sorted(folder.rglob("*")) if p.is_file()}}
    (folder / "BUILD-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    target = ROOT / "dist" / f"{NAME}.zip"
    target.parent.mkdir(exist_ok=True)
    archive(folder, target)
    print(f"ZIP: {target}\nSHA256: {sha256(target)}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside-venv", action="store_true")
    args = parser.parse_args()
    if args.inside_venv:
        build()
        return
    if sys.version_info[:3] != (3, 12, 2) or sys.maxsize <= 2**32:
        raise RuntimeError("Specificare CPython 3.12.2 x64")
    environment = ROOT / "build/package-venv"
    if not environment.exists():
        run([sys.executable, "-m", "venv", environment])
    python = environment / "Scripts/python.exe"
    run([python, "-m", "pip", "install", "--no-deps", "-r", HERE / "requirements.lock.txt"])
    run([python, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "--force-reinstall",
         ROOT / "backend", ROOT / "frontend"])
    run([python, "-m", "pip", "check"])
    run([python, __file__, "--inside-venv"])


if __name__ == "__main__":
    main()
