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
import urllib.request



ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from payload_audit import full_file_inventory, qt_file_inventory, trim_qt
INSTALLER_VERSION = "0.2.1"
NAME = f"LocalDocumentSearch-{INSTALLER_VERSION}-windows-x64"
INNO_VERSION = "6.7.3"
INNO_SHA256 = "0a8757031b33777e4c9cbffee40f11a5062b36d25cbe144c1db73b6102b80ad7"


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
                "PySide6/QtGui.pyd", "PySide6/QtQml.pyd", "PySide6/QtQuick.pyd",
                "PySide6/QtQuickControls2.pyd", "PySide6/QtPdf.pyd",
                "local_document_search_desktop/qml/Main.qml",
                "PySide6/qt-plugins/platforms/qwindows.dll", "ISTRUZIONI.txt",
                "BUILD-MANIFEST.json", "THIRD_PARTY_NOTICES.txt", "licenses/Python.txt",
                "TERMS-IT.txt", "TERMS-EN.txt", "diagnostics/run_v2_benchmark.py",
                "diagnostics/v2_benchmark.py", "diagnostics/m9_corpus.py"]
    resources = ROOT / "frontend/src/local_document_search_desktop"
    required.extend("local_document_search_desktop/" + path.relative_to(resources).as_posix()
                    for subdirectory in ("qml", "assets")
                    for path in (resources / subdirectory).rglob("*") if path.is_file())
    missing = [name for name in required if not (folder / name).is_file()]
    if missing:
        raise RuntimeError(f"Pacchetto incompleto: {missing}")
    forbidden = [p for p in folder.rglob("*")
                 if p.suffix.lower() in {".sqlite", ".sqlite3", ".db"}
                 or p.name in {".env", ".git", "__pycache__"}]
    if forbidden:
        raise RuntimeError(f"Dati non distribuibili: {forbidden}")


def remove_unused_qt_modules(folder):
    """Rimuove addon non importati dalla UI; opera solo nello staging di build."""
    banned = ("qt6webengine", "qt6multimedia", "qtwebengine", "qtmultimedia")
    explicit = []
    for path in explicit:
        if path.is_dir():
            safe_clean(path)
        elif path.is_file():
            path.unlink()
    for path in sorted(folder.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if not path.exists() or path.is_symlink():
            continue
        if not path.name.lower().startswith(banned):
            continue
        if not path.resolve().is_relative_to((ROOT / "build/package").resolve()):
            raise RuntimeError(f"Qt fuori dallo staging: {path}")
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()


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


def redist_notice(visual_studio):
    root = Path(visual_studio)
    redist = root / "Licenses/1033/Redist.txt"
    if not redist.is_file():
        raise RuntimeError(f"Elenco redistribuibili Microsoft mancante: {redist}")
    return redist


def collect_licenses(folder, visual_studio):
    destination = folder / "licenses"
    destination.mkdir(exist_ok=True)
    packages = ["markdown-it-py", "mdurl", "pypdf", "PySide6", "PySide6_Essentials", "PySide6_Pdf", "shiboken6", "Nuitka"]
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
    shutil.copy2(redist_notice(visual_studio), destination / "Microsoft-Visual-Studio-2022-Redist.txt")
    shutil.copytree(HERE / "licenses", destination / "upstream", dirs_exist_ok=True)
    shutil.copy2(HERE / "THIRD_PARTY_NOTICES.txt", folder)


def collect_qt_sources(folder):
    """Scarica gli archivi upstream bloccati e li incorpora nel payload."""
    entries = json.loads((HERE / "licenses/SOURCES.json").read_text(encoding="utf-8"))
    cache = ROOT / "build/qt-sources"
    cache.mkdir(parents=True, exist_ok=True)
    output = folder / "sources"
    output.mkdir(exist_ok=True)
    recorded = {}
    for component, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        name = entry["url"].rsplit("/", 1)[-1]
        cached = cache / name
        if not cached.is_file() or sha256(cached) != entry["sha256"]:
            temporary = cached.with_suffix(cached.suffix + ".tmp")
            print(f"Scarico sorgenti {component}: {entry['url']}", flush=True)
            for attempt in range(8):
                offset = temporary.stat().st_size if temporary.exists() else 0
                request = urllib.request.Request(entry["url"], headers={"Range": f"bytes={offset}-"} if offset else {})
                try:
                    with urllib.request.urlopen(request, timeout=180) as source:
                        if offset and source.status != 206:
                            temporary.unlink()
                            continue
                        with temporary.open("ab" if offset else "wb") as target:
                            shutil.copyfileobj(source, target, length=1024 * 1024)
                    break
                except (TimeoutError, OSError) as error:
                    if attempt == 7:
                        raise RuntimeError(f"Download sorgenti fallito: {component}") from error
            if sha256(temporary) != entry["sha256"]:
                temporary.unlink()
                raise RuntimeError(f"Hash sorgenti non valido: {component}")
            temporary.replace(cached)
        shutil.copy2(cached, output / name)
        recorded[component] = {"file": f"sources/{name}", "sha256": entry["sha256"],
                               "url": entry["url"]}
    return recorded


def payload_components(folder):
    names = [p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()]
    qt = sorted(name for name in names if name.lower().endswith((".dll", ".pyd"))
                and (name.startswith("PySide6/") or "qt" in name.lower()))
    microsoft = sorted(name for name in names if name.lower().startswith(("vcruntime", "msvcp", "concrt"))
                       and name.lower().endswith(".dll"))
    return {"python": {"version": "3.12.2", "license": "licenses/Python.txt",
                       "files": sorted(name for name in names if name.lower().startswith("python") and name.lower().endswith(".dll"))},
            "qt": {"version": metadata.version("PySide6"), "license": "licenses/upstream/LGPL-3.0.txt",
                   "files": qt},
            "microsoft_runtime": {"files": microsoft},
            "python_packages": {name: metadata.version(name) for name in
                ("markdown-it-py", "mdurl", "pypdf", "PySide6", "PySide6_Essentials", "PySide6_Pdf", "shiboken6")}}


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
            "installation_path": instance["installationPath"],
            "msvc_installed": sorted(p.name for p in vc.iterdir() if p.is_dir()),
            "x64_compilers": [{"path": str(p), "sha256": sha256(p)} for p in compilers]}


def installer_compiler():
    candidates = [Path(os.environ["LDS_ISCC"])] if os.environ.get("LDS_ISCC") else [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Inno Setup 6/ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6/ISCC.exe",
    ]
    found = [path for path in candidates if path.is_file()]
    if len(found) != 1:
        raise RuntimeError("Compilatore Inno Setup 6.7.3 non trovato; impostare LDS_ISCC")
    compiler = found[0]
    digest = sha256(compiler)
    if digest != INNO_SHA256:
        raise RuntimeError(f"ISCC.exe non corrisponde al lock: {digest}")
    return compiler


def build_installer(folder, manifest):
    compiler = installer_compiler()
    target_dir = ROOT / "dist"
    required_bytes = sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())
    required_bytes += sum((HERE / name).stat().st_size for name in
                          ("uninstall-data.ps1", "prune-upgrade.ps1"))
    args = [compiler, f"/DPayloadDir={folder}", f"/DOutputDir={target_dir}",
            f"/DRequiredBytes={required_bytes}",
            HERE / "installer.iss"]
    run(args)
    target = target_dir / f"LocalDocumentSearch-{INSTALLER_VERSION}-windows-x64-setup.exe"
    if not target.is_file():
        raise RuntimeError("Installer non prodotto")
    record = {"installer_sha256": sha256(target), "installer_version": INSTALLER_VERSION,
              "iscc_version": INNO_VERSION, "iscc_sha256": sha256(compiler),
              "iscc_path": str(compiler), "command": [str(arg) for arg in args],
              "payload_manifest_sha256": sha256(folder / "BUILD-MANIFEST.json"),
              "revision": manifest["revision"], "dirty_worktree": manifest["dirty_worktree"],
              "installer_source_sha256": {name: sha256(HERE / name) for name in
                  ("installer.iss", "uninstall-data.ps1", "prune-upgrade.ps1", "build.py")}}
    (target_dir / f"{target.name}.manifest.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (target_dir / f"{target.name}.sha256").write_text(
        f"{record['installer_sha256']}  {target.name}\n", encoding="ascii")
    print(f"Installer: {target}\nSHA256: {record['installer_sha256']}", flush=True)


def clean_revision():
    status = run(["git", "status", "--porcelain", "--untracked-files=all"],
                 cwd=ROOT, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("Build release rifiutata: working tree modificato")


def build(*, release=False):
    if release:
        clean_revision()
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
    shutil.copytree(ROOT / "frontend/src/local_document_search_desktop/qml",
                    workspace / "local_document_search_desktop/qml")
    shutil.copytree(ROOT / "frontend/src/local_document_search_desktop/assets",
                    workspace / "local_document_search_desktop/assets")
    config = configparser.ConfigParser()
    config.read(HERE / "pysidedeploy.spec", encoding="utf-8")
    config["qt"]["qml_files"] = ",".join(
        path.relative_to(workspace).as_posix()
        for path in sorted((workspace / "local_document_search_desktop/qml").rglob("*.qml")))
    config["app"]["project_dir"] = str(workspace)
    config["app"]["exec_directory"] = str(workspace / "output")
    with (workspace / "pysidedeploy.spec").open("w", encoding="utf-8") as output:
        config.write(output)
    command = [Path(sys.executable).with_name("pyside6-deploy.exe"), "-c",
               workspace / "pysidedeploy.spec", "--no-install", "--force", "--keep-deployment-files"]
    with (workspace / "deploy.log").open("w", encoding="utf-8") as log:
        environment = dict(os.environ)
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
        run(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT, env=environment)
    candidates = list((workspace / "deployment").glob("*.dist"))
    if len(candidates) != 1:
        raise RuntimeError(f"Output standalone inatteso: {candidates}; consultare deploy.log")
    folder = candidates[0]
    # Nuitka non include sempre il binding Python QtPdf importato nel worker.
    import importlib.util
    pdf_binding = importlib.util.find_spec("PySide6.QtPdf")
    if pdf_binding is None or not pdf_binding.origin:
        raise RuntimeError("Binding PySide6.QtPdf non disponibile nell'ambiente bloccato")
    shutil.copy2(pdf_binding.origin, folder / "PySide6/QtPdf.pyd")
    for resource in ("qml", "assets"):
        shutil.copytree(workspace / "local_document_search_desktop" / resource,
                        folder / "local_document_search_desktop" / resource, dirs_exist_ok=True)
    diagnostics = folder / "diagnostics"
    diagnostics.mkdir()
    for name in ("run_v2_benchmark.py", "v2_benchmark.py", "m9_corpus.py"):
        shutil.copy2(ROOT / "experiments" / name, diagnostics / name)
    remove_unused_qt_modules(folder)
    dumpbin = next(Path(compiler["x64_compilers"][0]["path"]).parent.glob("dumpbin.exe"))
    qt_audit = trim_qt(folder, dumpbin)
    shutil.copy2(HERE / "ISTRUZIONI.txt", folder)
    shutil.copy2(HERE / "TERMS-IT.txt", folder)
    shutil.copy2(HERE / "TERMS-EN.txt", folder)
    shutil.copy2(HERE / "QT_REPLACEMENT.txt", folder)
    collect_licenses(folder, compiler["installation_path"])
    qt_sources = collect_qt_sources(folder)
    report = workspace / "compilation-report.xml"
    if not report.is_file():
        raise RuntimeError("Report compilatore assente")
    shutil.copy2(report, folder)
    qt_files = qt_file_inventory(folder, qt_sources)
    file_inventory = full_file_inventory(folder, qt_sources)
    if len(file_inventory) != sum(path.is_file() for path in folder.rglob("*")):
        raise RuntimeError("Inventario file incompleto")
    packages = {d.metadata["Name"]: d.version for d in metadata.distributions()}
    revision = run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    sources = {}
    for directory in ("backend/src", "frontend/src", "scripts/package"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                sources[path.relative_to(ROOT).as_posix()] = sha256(path)
    for name in ("run_v2_benchmark.py", "v2_benchmark.py", "m9_corpus.py"):
        sources[f"experiments/{name}"] = sha256(ROOT / "experiments" / name)
    for project in ("backend", "frontend"):
        sources[f"{project}/pyproject.toml"] = sha256(ROOT / project / "pyproject.toml")
    if release and dirty:
        raise RuntimeError("Working tree modificato durante la build release")
    manifest = {"application": NAME, "revision": revision, "dirty_worktree": bool(dirty),
                "python": sys.version, "platform": platform.platform(), "toolchain": compiler,
                "packages": packages, "command": [str(a) for a in command],
                "resolved_spec": (workspace / "pysidedeploy.spec").read_text(encoding="utf-8"),
                "sources_sha256": sources, "lock_sha256": sha256(HERE / "requirements.lock.txt"),
                "payload_components": payload_components(folder), "qt_audit": qt_audit,
                "qt_sources": qt_sources, "qt_file_inventory": qt_files,
                "file_inventory": file_inventory,
                "files_sha256": {p.relative_to(folder).as_posix(): sha256(p)
                                 for p in sorted(folder.rglob("*")) if p.is_file()}}
    (folder / "BUILD-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    target = ROOT / "dist" / f"{NAME}.zip"
    target.parent.mkdir(exist_ok=True)
    archive(folder, target)
    print(f"ZIP: {target}\nSHA256: {sha256(target)}", flush=True)
    build_installer(folder, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside-venv", action="store_true")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    if args.release:
        clean_revision()
    if args.inside_venv:
        build(release=args.release)
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
    run([python, __file__, "--inside-venv", *(["--release"] if args.release else [])])


if __name__ == "__main__":
    main()
