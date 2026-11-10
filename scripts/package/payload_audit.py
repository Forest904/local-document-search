"""Selezione dei moduli Qt runtime e verifica delle loro licenze."""

from collections import deque
from pathlib import Path
import re
import subprocess


QML_IMPORTS = ("QtQuick", "QtQuick.Controls.Basic", "QtQuick.Layouts", "QtQuick.Dialogs", "QtQuick.Pdf")
PYSIDE_MODULES = {"QtCore.pyd", "QtGui.pyd", "QtNetwork.pyd", "QtOpenGL.pyd",
                  "QtQml.pyd", "QtQuick.pyd", "QtQuickControls2.pyd", "QtWidgets.pyd"}
GPL_MODULES = ("qt6graphs", "qt63d", "qt6quicktimeline", "qt6virtualkeyboard", "qt6qmlcompiler")
GPL_QML_DIRS = {"Graphs", "Scene2D", "Scene3D", "Timeline", "VirtualKeyboard"}
QML_PATTERN = re.compile(r"^\s*(?:depends|import|default import)\s+(Qt[A-Za-z0-9_.]+)", re.MULTILINE)
DLL_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+\.dll)\s*$", re.MULTILINE | re.IGNORECASE)


def qml_modules(folder):
    root = folder / "PySide6/qml"
    available = {}
    for qmldir in root.rglob("qmldir"):
        for line in qmldir.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("module "):
                available[line.split()[1]] = qmldir.parent
                break
    selected = set()
    app_qml = folder / "local_document_search_desktop/qml"
    imports = set(QML_IMPORTS)
    for source in app_qml.rglob("*.qml"):
        imports.update(QML_PATTERN.findall(source.read_text(encoding="utf-8")))
    pending = deque(sorted(imports))
    while pending:
        module = pending.popleft()
        if module in selected:
            continue
        directory = available.get(module)
        if directory is None:
            raise RuntimeError(f"Modulo QML richiesto assente: {module}")
        selected.add(module)
        sources = [directory / "qmldir"]
        sources.extend(path for path in directory.rglob("*.qml")
                       if not any(part.startswith("+") or part == "designer"
                                  for part in path.relative_to(directory).parts)
                       and next((parent for parent in (path.parent, *path.parents)
                                 if (parent / "qmldir").is_file()), None) == directory)
        for source in sources:
            if source.is_file():
                for dependency in QML_PATTERN.findall(source.read_text(encoding="utf-8", errors="replace")):
                    if dependency in available and dependency not in selected:
                        pending.append(dependency)
    return available, selected


def binary_dependencies(path, dumpbin):
    result = subprocess.run([str(dumpbin), "/DEPENDENTS", str(path)],
                            check=True, capture_output=True, text=True, errors="replace")
    return {name.lower() for name in DLL_PATTERN.findall(result.stdout)}


def trim_qt(folder, dumpbin):
    """Conserva gli import QML e la chiusura delle dipendenze PE."""
    qml_root = folder / "PySide6/qml"
    available, selected = qml_modules(folder)
    chosen_dirs = {available[name] for name in selected}
    module_dirs = {path.parent for path in qml_root.rglob("qmldir")}
    for path in sorted(qml_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            owner = next((parent for parent in (path.parent, *path.parents)
                          if parent in module_dirs), None)
            relative_parts = path.relative_to(qml_root).parts
            if (owner not in chosen_dirs or path.suffix == ".qmltypes"
                    or any(part in GPL_QML_DIRS or part == "designer" or part.startswith("+")
                           for part in relative_parts)):
                path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    plugin_root = folder / "PySide6/qt-plugins"
    required_plugins = {plugin_root / "platforms/qwindows.dll",
                        plugin_root / "imageformats/qsvg.dll",
                        plugin_root / "imageformats/qico.dll",
                        plugin_root / "iconengines/qsvgicon.dll"}
    for path in sorted(plugin_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file() and path not in required_plugins:
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    pyside = folder / "PySide6"
    for path in pyside.glob("Qt*.pyd"):
        if path.name not in PYSIDE_MODULES:
            path.unlink()
    binaries = [path for path in folder.rglob("*") if path.suffix.lower() in {".dll", ".pyd", ".exe"}]
    by_name = {path.name.lower(): path for path in binaries if path.parent == folder}
    for path in binaries:
        by_name.setdefault(path.name.lower(), path)
    seeds = [folder / "LocalDocumentSearch.exe", *required_plugins,
             *(pyside / name for name in sorted(PYSIDE_MODULES)),
             *qml_root.rglob("*.dll")]
    pending = deque(path for path in seeds if path.is_file())
    retained = set()
    while pending:
        path = pending.popleft()
        if path in retained:
            continue
        retained.add(path)
        for name in binary_dependencies(path, dumpbin):
            dependency = by_name.get(name)
            if dependency is None and name.startswith("qt6"):
                raise RuntimeError(f"Dipendenza Qt mancante: {path.name} → {name}")
            if dependency is not None and dependency not in retained:
                pending.append(dependency)
    for path in folder.glob("Qt6*.dll"):
        if path not in retained:
            path.unlink()
    remaining = {path.name.lower() for path in folder.rglob("*") if path.is_file()}
    gpl = sorted(name for name in remaining if name.startswith(GPL_MODULES))
    if gpl:
        raise RuntimeError(f"Moduli Qt solo GPL nel payload: {gpl}")
    return {"qml_modules": sorted(selected), "qt_dlls": sorted(
        path.name for path in retained if path.name.lower().startswith("qt6") and path.is_file())}


def qt_file_inventory(folder, sources):
    """Attribuisce ogni binario Qt distribuito a un archivio sorgente."""
    mapping = {
        "qt6pdf": "qtwebengine",
        "qt6svg": "qtsvg", "qt6statemachine": "qtscxml",
        "qt6shadertools": "qtshadertools",
        "qt6quick": "qtdeclarative", "qt6qml": "qtdeclarative",
        "qt6labs": "qtdeclarative", "qt6network": "qtbase",
        "qt6opengl": "qtbase", "qt6widgets": "qtbase", "qt6gui": "qtbase", "qt6core": "qtbase",
        "qt6sql": "qtbase",
    }
    result = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(folder).as_posix()
        name = path.name.lower()
        component = None
        if name.startswith("qt6") and path.suffix.lower() == ".dll":
            component = next((source for prefix, source in mapping.items()
                              if name.startswith(prefix)), None)
        elif relative == "PySide6/qt-plugins/platforms/qwindows.dll":
            component = "qtbase"
        elif relative.startswith("PySide6/") and path.suffix.lower() in {".dll", ".pyd"}:
            component = "qtwebengine" if "/qml/QtQuick/Pdf/" in relative else "pyside6" if path.suffix.lower() == ".pyd" else (
                "qtdeclarative" if "/qml/" in relative else "qtbase")
        elif name.startswith(("pyside6", "shiboken6")) and path.suffix.lower() == ".dll":
            component = "pyside6"
        if component is None and (name.startswith("qt6") or name.startswith(("pyside6", "shiboken6"))):
            raise RuntimeError(f"File Qt non attribuito: {relative}")
        if component:
            if component not in sources:
                raise RuntimeError(f"Sorgente Qt mancante: {relative} → {component}")
            result.append({"file": relative, "version": "6.140.0" if component == "qtwebengine" else "6.12.0", "license": "LGPL-3.0",
                           "notice": "THIRD_PARTY_NOTICES.txt", "source": sources[component]["file"]})
    return result


def full_file_inventory(folder, qt_sources):
    """Descrive ogni file distribuito; un file nuovo richiede attribuzione esplicita."""
    qt_binaries = {entry["file"]: entry for entry in qt_file_inventory(folder, qt_sources)}
    records = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name == "BUILD-MANIFEST.json":
            continue
        name = path.relative_to(folder).as_posix()
        low = path.name.lower()
        component = version = license_id = notice = provenance = source = None
        if name in qt_binaries or name.startswith("PySide6/qml/"):
            if name in qt_binaries:
                entry = qt_binaries[name]
                source = entry["source"]
                component = next(key for key, value in qt_sources.items() if value["file"] == source)
            else:
                component = "qtwebengine" if name.startswith("PySide6/qml/QtQuick/Pdf/") else "qtdeclarative"
                source = qt_sources[component]["file"]
            # Plugin Qt della piattaforma proviene da QtBase, non da PySide.
            if name == "PySide6/qt-plugins/platforms/qwindows.dll":
                component = "qtbase"
                source = qt_sources[component]["file"]
            version, license_id = ("6.140.0" if component == "qtwebengine" else "6.12.0"), "LGPL-3.0"
            notice, provenance = "licenses/upstream/LGPL-3.0.txt", ("PySide6_Pdf 6.12.0.140 wheel" if component == "qtwebengine" else "PySide6_Essentials 6.12.0 wheel")
        elif name.startswith("PySide6/") or name in ("pyside6.abi3.dll", "pyside6qml.abi3.dll"):
            component, version, license_id = "pyside6", "6.12.0", "LGPL-3.0"
            notice, provenance, source = "licenses/upstream/LGPL-3.0.txt", "PySide6 6.12.0 wheel", qt_sources["pyside6"]["file"]
        elif (name.startswith("shiboken6/") and low.startswith("msvcp")) or low.startswith(("msvcp", "vcruntime")):
            component, version, license_id = "microsoft-vc-runtime", "14.44.35211.0", "Microsoft proprietary redistributable"
            notice, provenance, source = "licenses/Microsoft-Visual-Studio-2022-Redist.txt", "Visual Studio 2022 Build Tools", None
        elif name.startswith("shiboken6/") or low.startswith("shiboken6"):
            component, version, license_id = "shiboken6", "6.12.0", "LGPL-3.0"
            notice, provenance, source = "licenses/upstream/LGPL-3.0.txt", "shiboken6 6.12.0 wheel", qt_sources["pyside6"]["file"]
        elif low in ("libcrypto-3.dll", "libssl-3.dll"):
            component, version, license_id = "openssl", "3.0.13", "Apache-2.0"
            notice, provenance, source = "licenses/upstream/OpenSSL-3.0.13.txt", "CPython 3.12.2 Windows runtime", "https://github.com/openssl/openssl/tree/openssl-3.0.13"
        elif low == "libffi-8.dll":
            component, version, license_id = "libffi", "3.4.4", "MIT-like"
            notice, provenance, source = "licenses/Python.txt", "CPython 3.12.2 Windows runtime", "https://github.com/libffi/libffi/tree/v3.4.4"
        elif low == "sqlite3.dll":
            component, version, license_id = "sqlite", "3.43.1", "Public-Domain"
            notice, provenance, source = "THIRD_PARTY_NOTICES.txt", "CPython 3.12.2 Windows runtime", "https://www.sqlite.org/2023/sqlite-autoconf-3430100.tar.gz"
        elif low == "opengl32sw.dll":
            component, version, license_id = "mesa-llvmpipe", "11.2.2", "MIT AND BSL-1.0"
            notice, provenance, source = "licenses/upstream/Mesa-llvmpipe-NOTICE.txt", "PySide6_Essentials 6.12.0 wheel", qt_sources["mesa"]["file"]
        elif (low.startswith("python") and low.endswith(".dll")) or low.endswith(".pyd"):
            component, version, license_id = "cpython", "3.12.2", "PSF-2.0"
            notice, provenance, source = "licenses/Python.txt", "CPython 3.12.2 Windows runtime", "https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz"
        elif name.startswith("sources/"):
            matches = [key for key, value in qt_sources.items() if value["file"] == name]
            if len(matches) != 1:
                raise RuntimeError(f"Archivio sorgente non attribuito: {name}")
            component = matches[0]
            if component == "mesa":
                version, license_id, notice = "11.2.2", "MIT AND BSL-1.0", "licenses/upstream/Mesa-llvmpipe-NOTICE.txt"
            else:
                version, license_id, notice = "6.12.0", "LGPL-3.0", "licenses/upstream/LGPL-3.0.txt"
            provenance = qt_sources[component]["url"]
            source = name
        elif name.startswith("licenses/"):
            component = "legal-notice"
            version, license_id = "0.2.0", "Various; see file"
            notice, provenance, source = name, "Build inputs and installed package metadata", name
        elif name == "LocalDocumentSearch.exe" or name.startswith(("local_document_search_desktop/", "diagnostics/")) or name in {
                "ISTRUZIONI.txt", "QT_REPLACEMENT.txt", "TERMS-IT.txt", "TERMS-EN.txt",
                "THIRD_PARTY_NOTICES.txt", "compilation-report.xml"}:
            component, version, license_id = "local-document-search", "0.2.0", "Project terms; Nuitka runtime exception for EXE"
            notice, provenance, source = "TERMS-IT.txt", "Project sources and Nuitka 4.1.1 build", "backend/src; frontend/src; scripts/package; experiments"
        if component is None:
            raise RuntimeError(f"File runtime privo di attribuzione: {name}")
        if notice and not (folder / notice).is_file():
            raise RuntimeError(f"Avviso mancante per {name}: {notice}")
        if source and source.startswith("sources/") and not (folder / source).is_file():
            raise RuntimeError(f"Sorgente mancante per {name}: {source}")
        records.append({"file": name, "component": component, "version": version,
                        "provenance": provenance, "license": license_id,
                        "notice": notice, "source": source})
    return records
