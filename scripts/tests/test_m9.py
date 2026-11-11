"""Regressioni del corpus e dell'archivio distribuito M9."""
import importlib.util
import os
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


corpus = module("m9_corpus", "experiments/m9_corpus.py")
packaging = module("m9_package", "scripts/package/build.py")


def test_corpus_reproducible_and_queries(tmp_path):
    from local_document_search.interfaces.composition import compose_cli
    from local_document_search.application.contracts import SearchRequest, SearchField
    first = corpus.generate(tmp_path / "first", count=9, text_bytes=300)
    second = corpus.generate(tmp_path / "second", count=9, text_bytes=300)
    assert first == second
    assert {Path(f["path"]).suffix for f in first["files"]} == {".txt", ".md", ".pdf"}
    app = compose_cli(str(tmp_path / "first/source"))
    built = app.build.execute(app.root_directory)
    assert built.indexed == 9 and built.excluded == 0
    for query in first["queries"]:
        response = app.search.execute(SearchRequest(query["query"], SearchField(query["field"])))
        assert [item.relative_path.value for item in response.results] == query["expected"]
    with pytest.raises(ValueError):
        corpus.generate(tmp_path / "first", count=9, text_bytes=300)


def test_error_fixtures_are_separate(tmp_path):
    from pypdf import PdfReader
    from io import BytesIO
    errors = corpus.error_fixtures(tmp_path / "errors")
    assert PdfReader(errors / "protected.pdf").is_encrypted
    assert not PdfReader(errors / "no-text.pdf").pages[0].extract_text().strip()
    assert PdfReader(BytesIO(corpus.pdf_bytes("alfa beta"))).pages[0].extract_text().strip() == "alfa beta"
    with pytest.raises(UnicodeDecodeError):
        (errors / "invalid.txt").read_text(encoding="utf-8")


def payload(tmp_path):
    folder = tmp_path / "payload"
    resources = ROOT / "frontend/src/local_document_search_desktop"
    resource_names = ["local_document_search_desktop/" + path.relative_to(resources).as_posix()
                      for subdir in ("qml", "assets") for path in (resources / subdir).rglob("*") if path.is_file()]
    for name in ["LocalDocumentSearch.exe", "python312.dll", "PySide6/QtCore.pyd",
                 "PySide6/QtGui.pyd", "PySide6/QtQml.pyd", "PySide6/QtQuick.pyd",
                 "PySide6/QtQuickControls2.pyd", "PySide6/QtPdf.pyd",
                 "local_document_search_desktop/qml/Main.qml",
                 "PySide6/qt-plugins/platforms/qwindows.dll", "ISTRUZIONI.txt",
                 "BUILD-MANIFEST.json", "THIRD_PARTY_NOTICES.txt", "licenses/Python.txt",
                 "TERMS-IT.txt", "TERMS-EN.txt", "diagnostics/run_v2_benchmark.py",
                 "diagnostics/v2_benchmark.py", "diagnostics/m9_corpus.py", *resource_names]:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic")
    return folder


def test_archive_preserves_layout_and_checksum(tmp_path):
    folder = payload(tmp_path)
    target = tmp_path / "app.zip"
    packaging.archive(folder, target)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert archive.read(f"{packaging.NAME}/PySide6/qt-plugins/platforms/qwindows.dll") == b"synthetic"
    assert target.with_suffix(".zip.sha256").read_text().startswith(packaging.sha256(target))


def test_incomplete_or_private_payload_is_rejected(tmp_path):
    folder = payload(tmp_path)
    database = folder / "personal.sqlite3"
    database.write_bytes(b"private")
    with pytest.raises(RuntimeError, match="Dati non distribuibili"):
        packaging.archive(folder, tmp_path / "bad.zip")
    database.unlink()
    (folder / "python312.dll").unlink()
    with pytest.raises(RuntimeError, match="Pacchetto incompleto"):
        packaging.archive(folder, tmp_path / "bad.zip")
    assert not (tmp_path / "bad.zip").exists()


def test_payload_inventory_describes_files_not_build_tools(tmp_path):
    folder = payload(tmp_path)
    (folder / "PySide6/Qt6Core.dll").write_bytes(b"synthetic")
    components = packaging.payload_components(folder)
    assert "PySide6/Qt6Core.dll" in components["qt"]["files"]
    assert "Nuitka" not in components["python_packages"]
    assert "python312.dll" in components["python"]["files"]


def test_unused_qt_addons_removed_from_staging_only(tmp_path, monkeypatch):
    monkeypatch.setattr(packaging, "ROOT", tmp_path)
    folder = tmp_path / "build/package/payload"
    (folder / "PySide6/qml/QtWebEngine").mkdir(parents=True)
    (folder / "PySide6/qml/QtWebEngine/plugin.dll").write_bytes(b"unused")
    (folder / "qt6pdf.dll").write_bytes(b"unused")
    (folder / "qt6quick.dll").write_bytes(b"needed")
    packaging.remove_unused_qt_modules(folder)
    assert not (folder / "PySide6/qml/QtWebEngine").exists()
    assert (folder / "qt6pdf.dll").exists()
    assert (folder / "qt6quick.dll").read_bytes() == b"needed"


def test_clean_refuses_outside_build(tmp_path):
    protected = tmp_path / "keep.txt"
    protected.write_text("keep")
    with pytest.raises(ValueError):
        packaging.safe_clean(tmp_path)
    assert protected.read_text() == "keep"


def test_package_launch_isolates_environment_without_changing_parent(tmp_path):
    launcher = module("m9_launcher", "experiments/launch_m9_package.py")
    original = {"SystemRoot": "C:/Windows", "Path": "C:/python;C:/Qt",
                "PythonPath": "C:/source", "Qt_Plugin_Path": "C:/Qt/plugins",
                "LOCALAPPDATA": "C:/personal", "VIRTUAL_ENV": "C:/venv"}
    isolated = launcher.isolated_environment(original, tmp_path)
    assert isolated["PATH"] == str(Path("C:/Windows") / "System32")
    assert isolated["LOCALAPPDATA"] == str(tmp_path / "appdata")
    assert not {"PYTHONPATH", "QT_PLUGIN_PATH", "VIRTUAL_ENV"} & isolated.keys()
    assert original["LOCALAPPDATA"] == "C:/personal" and original["PythonPath"] == "C:/source"


@pytest.mark.skipif(os.name != "nt", reason="Contatori memoria Win32 del benchmark M9")
def test_benchmark_checks_queries_sync_and_restores_sources(tmp_path):
    runner = module("m9_runner", "experiments/run_m9.py")
    manifest = corpus.generate(tmp_path / "corpus", count=6, text_bytes=200)
    result = runner.run(tmp_path / "corpus", tmp_path / "storage")
    assert result["incremental"]["added"] == result["incremental"]["modified"] == result["incremental"]["removed"] == 1
    assert result["peak_working_set_bytes"] > 0
    for entry in manifest["files"]:
        assert packaging.sha256(tmp_path / "corpus/source" / entry["path"]) == entry["sha256"]
