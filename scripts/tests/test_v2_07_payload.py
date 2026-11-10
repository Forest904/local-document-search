"""Regressioni della selezione QML e del vincolo sulle licenze Qt."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "package"))
import payload_audit


def test_optional_styles_and_gpl_plugins_are_not_selected(tmp_path, monkeypatch):
    monkeypatch.setattr(payload_audit, "QML_IMPORTS", ("QtQuick.Controls",))
    root = tmp_path / "PySide6/qml/QtQuick"
    controls = root / "Controls"
    controls.mkdir(parents=True)
    (controls / "qmldir").write_text(
        "module QtQuick.Controls\noptional import QtQuick.Controls.Fusion\n"
        "default import QtQuick.Controls.Basic\n", encoding="utf-8")
    basic = controls / "Basic"
    basic.mkdir()
    (basic / "qmldir").write_text("module QtQuick.Controls.Basic\n", encoding="utf-8")
    fusion = controls / "Fusion"
    fusion.mkdir()
    (fusion / "qmldir").write_text("module QtQuick.Controls.Fusion\n", encoding="utf-8")
    (fusion / "Button.qml").write_text("import QtQuick.Controls.Fusion\n", encoding="utf-8")
    designer = controls / "designer"
    designer.mkdir()
    (designer / "Editor.qml").write_text("import QtQuick.VirtualKeyboard\n", encoding="utf-8")
    (root / "Scene3D").mkdir()
    (root / "Scene3D/qtquickscene3dplugin.dll").write_bytes(b"synthetic")
    available, chosen = payload_audit.qml_modules(tmp_path)
    assert chosen == {"QtQuick.Controls", "QtQuick.Controls.Basic"}
    assert "QtQuick.Controls.Fusion" in available


def test_missing_required_qml_module_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(payload_audit, "QML_IMPORTS", ("QtQuick.Controls",))
    (tmp_path / "PySide6/qml").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="richiesto assente"):
        payload_audit.qml_modules(tmp_path)


def test_qt_inventory_requires_known_module_and_source(tmp_path):
    (tmp_path / "qt6core.dll").write_bytes(b"synthetic")
    with pytest.raises(RuntimeError, match="Sorgente Qt mancante"):
        payload_audit.qt_file_inventory(tmp_path, {})
    sources = {"qtbase": {"file": "sources/qtbase.tar.xz"}}
    inventory = payload_audit.qt_file_inventory(tmp_path, sources)
    assert inventory[0]["source"] == "sources/qtbase.tar.xz"
    (tmp_path / "qt6unknown.dll").write_bytes(b"synthetic")
    with pytest.raises(RuntimeError, match="File Qt non attribuito"):
        payload_audit.qt_file_inventory(tmp_path, sources)


def test_pdf_payload_requires_matching_source(tmp_path):
    (tmp_path / "Qt6Pdf.dll").write_bytes(b"synthetic")
    with pytest.raises(RuntimeError, match="Sorgente Qt mancante"):
        payload_audit.qt_file_inventory(tmp_path, {})
    sources = {"qtwebengine": {"file": "sources/qtwebengine-6.140.0.tar.xz"}}
    record = payload_audit.qt_file_inventory(tmp_path, sources)[0]
    assert record["source"] == "sources/qtwebengine-6.140.0.tar.xz"
    assert record["version"] == "6.140.0"


def test_full_inventory_rejects_unknown_runtime_and_missing_notices(tmp_path):
    (tmp_path / "mystery.dll").write_bytes(b"synthetic")
    with pytest.raises(RuntimeError, match="privo di attribuzione"):
        payload_audit.full_file_inventory(tmp_path, {})
    (tmp_path / "mystery.dll").unlink()
    (tmp_path / "python312.dll").write_bytes(b"synthetic")
    with pytest.raises(RuntimeError, match="Avviso mancante"):
        payload_audit.full_file_inventory(tmp_path, {})
    (tmp_path / "licenses").mkdir()
    (tmp_path / "licenses/Python.txt").write_text("PSF", encoding="utf-8")
    items = payload_audit.full_file_inventory(tmp_path, {})
    assert next(x for x in items if x["file"] == "python312.dll")["component"] == "cpython"


def test_full_inventory_requires_corresponding_qt_source(tmp_path):
    (tmp_path / "qt6core.dll").write_bytes(b"synthetic")
    (tmp_path / "licenses/upstream").mkdir(parents=True)
    (tmp_path / "licenses/upstream/LGPL-3.0.txt").write_text("LGPL", encoding="utf-8")
    sources = {"qtbase": {"file": "sources/qtbase.tar.xz", "url": "https://example.test/qtbase.tar.xz"}}
    with pytest.raises(RuntimeError, match="Sorgente mancante"):
        payload_audit.full_file_inventory(tmp_path, sources)
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources/qtbase.tar.xz").write_bytes(b"synthetic")
    items = payload_audit.full_file_inventory(tmp_path, sources)
    assert next(x for x in items if x["file"] == "qt6core.dll")["source"] == "sources/qtbase.tar.xz"


def test_local_qt_pdf_view_is_attributed_to_qt_source(tmp_path):
    view = tmp_path / "local_document_search_desktop/qml/LocalPdfMultiPageView.qml"
    view.parent.mkdir(parents=True)
    view.write_text("// synthetic Qt view", encoding="utf-8")
    (tmp_path / "THIRD_PARTY_NOTICES.txt").write_text("Qt PDF", encoding="utf-8")
    (tmp_path / "TERMS-IT.txt").write_text("Project", encoding="utf-8")
    (tmp_path / "licenses/upstream").mkdir(parents=True)
    (tmp_path / "licenses/upstream/LGPL-3.0.txt").write_text("LGPL", encoding="utf-8")
    source = tmp_path / "sources/qtwebengine.tar.xz"
    source.parent.mkdir()
    source.write_bytes(b"synthetic")
    sources = {"qtwebengine": {"file": "sources/qtwebengine.tar.xz", "url": "https://example.test/source"}}
    record = next(item for item in payload_audit.full_file_inventory(tmp_path, sources)
                  if item["file"] == "local_document_search_desktop/qml/LocalPdfMultiPageView.qml")
    assert record["component"] == "qtwebengine"
    assert record["source"] == "sources/qtwebengine.tar.xz"
