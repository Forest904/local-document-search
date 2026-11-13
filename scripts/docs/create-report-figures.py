"""Figure della relazione: schemi e catture QML reali su dati sintetici isolati.

Eseguire dalla root con backend/.venv/Scripts/python.exe.
Non usa lo storage personale e non modifica il codice dell'applicazione.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_SCALE_FACTOR"] = "1"

from PySide6.QtCore import QRectF, Qt, QUrl
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QImage, QPainter, QPen
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest

from local_document_search_desktop.composition import compose_desktop
from local_document_search_desktop.controller import DesktopController
from local_document_search_desktop.main import create_engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/homework-3/figures"


def wait_for(predicate, timeout=30):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            raise RuntimeError("Timeout nella preparazione della cattura QML")
        QTest.qWait(20)
        time.sleep(0.005)


def diagram(name, height, boxes, arrows):
    image = QImage(1500, height, QImage.Format.Format_RGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    for x1, y1, x2, y2 in arrows:
        painter.setPen(QPen(QColor("#687e8a"), 3))
        painter.drawLine(x1, y1, x2, y2)
        painter.drawLine(x2, y2, x2 - 8, y2 - 12)
        painter.drawLine(x2, y2, x2 + 8, y2 - 12)
    for x, y, w, h, title, body in boxes:
        painter.setPen(QPen(QColor("#c2d2db"), 2))
        painter.setBrush(QColor("#f2f7fa"))
        painter.drawRoundedRect(QRectF(x, y, w, h), 14, 14)
        painter.setPen(QColor("#183d50"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
        painter.drawText(QRectF(x + 24, y + 17, w - 48, 42), Qt.AlignmentFlag.AlignLeft, title)
        painter.setFont(QFont("Segoe UI", 17))
        painter.drawText(QRectF(x + 24, y + 69, w - 48, h - 75), Qt.TextFlag.TextWordWrap, body)
    painter.end()
    assert image.save(str(OUT / name))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication([])
    app.setQuitOnLastWindowClosed(False)
    # Il plugin offscreen non enumera sempre i font di sistema Windows.
    for name in ("segoeui.ttf", "segoeuib.ttf", "consola.ttf"):
        font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name
        if QFontDatabase.addApplicationFont(str(font)) < 0:
            raise RuntimeError(f"Font necessario non disponibile: {font}")
    app.setFont(QFont("Segoe UI", 10))
    diagram("indici.png", 590, [
        (20, 15, 1460, 115, "Documento A: RomaTre.txt", "Contenuto: Roma Tre studia machine deep learning. data data."),
        (20, 180, 700, 150, "Analyzer del nome", "RomaTre → roma (0), tre (1)\nIl suffisso .txt è rimosso prima dell'analisi."),
        (780, 180, 700, 150, "Analyzer del contenuto", "roma (0), tre (1), studia (2), machine (3),\ndeep (4), learning (5), data (6), data (7)"),
        (20, 380, 700, 185, "Indice filename", "roma → A: [0]\ntre → A: [1]\nPosizioni indipendenti da quelle del testo."),
        (780, 380, 700, 185, "Indice content (estratto)", "machine → A: [3]     deep → A: [4]\nlearning → A: [5]     data → A: [6, 7]\nLa frase deep learning verifica 4, 5."),
    ], [(370, 130, 370, 180), (1130, 130, 1130, 180), (370, 330, 370, 380), (1130, 330, 1130, 380)])
    diagram("architettura.png", 530, [
        (20, 15, 700, 115, "CLI Homework", "Console, TXT, indice volatile; nessun Qt."),
        (780, 15, 700, 115, "Luma desktop", "Qt Quick, worker, lettori e preferenze."),
        (20, 185, 1460, 120, "Backend condiviso: application + domain", "Casi d'uso e porte; analyzer, query, indici posizionali e snapshot."),
        (20, 365, 1460, 140, "Infrastruttura: implementazioni delle porte", "Filesystem e reader TXT / MD / PDF; persistenza SQLite nel desktop.\nLe frecce indicano il flusso operativo, non le dipendenze degli import."),
    ], [(370, 130, 370, 185), (1130, 130, 1130, 185), (750, 305, 750, 365)])
    with TemporaryDirectory(prefix="luma-report-") as temporary:
        base = Path(temporary)
        corpus = base / "Documenti-dimostrativi"
        corpus.mkdir()
        (corpus / "RicercaDocumentale.md").write_text(
            "# Ricerca documentale\n\n"
            "Un indice permette di cercare nei documenti senza rileggerli a ogni query.\n\n"
            "## Due campi distinti\n\n"
            "- **Nome**: utile per riconoscere un file.\n"
            "- **Contenuto**: utile per trovare un argomento nel testo.\n\n"
            "## Termini e frasi\n\n"
            "La ricerca di `machine learning` richiede entrambi i termini.\n"
            "La frase `\"deep learning\"` richiede anche posizioni consecutive.\n\n"
            "> Esempio sintetico preparato per la relazione Homework 3.\n",
            encoding="utf-8")
        (corpus / "AppuntiIndici.txt").write_text(
            "La ricerca documentale usa un vocabolario e liste di occorrenze. "
            "Le posizioni consentono di distinguere una frase da parole distanti.", encoding="utf-8")
        (corpus / "Sincronizzazione.md").write_text(
            "# Aggiornamento dei documenti\n\nDurante la ricerca resta disponibile "
            "lo snapshot precedente. Il nuovo indice viene attivato solo dopo la validazione.", encoding="utf-8")
        c = DesktopController(lambda: compose_desktop(base / "storage"), lambda *_: None)
        engine = create_engine(c)
        window = engine.rootObjects()[0]
        window.setWidth(1120)
        window.setHeight(620)
        try:
            c.initialize()
            wait_for(lambda: c.view["canManage"])
            c.savePreferences("it", "light")
            wait_for(lambda: c.view["canManage"])
            c.chooseDirectory(QUrl.fromLocalFile(str(corpus)).toString())
            wait_for(lambda: c.view["searchable"] and not c.view["running"] and c.view["canManage"])
            c.editQuery("ricerca", 7)
            c.search()
            wait_for(lambda: c.response is not None and not c.view["reading"])
            assert c.response.total_matches == 3
            QTest.qWait(500)
            assert window.grabWindow().save(str(OUT / "risultati.png"))
            index = next(i for i, result in enumerate(c.response.results) if result.filename == "RicercaDocumentale.md")
            c.openResult(index)
            wait_for(lambda: c.text_reader.ready)
            c.text_reader.startEditing()
            QTest.qWait(500)
            assert c.text_reader.editing and not c.text_reader.dirty
            assert window.grabWindow().save(str(OUT / "markdown.png"))
        finally:
            c.requestClose()
            wait_for(lambda: c.view["closed"])
            window.close()
        del engine
    composite = QImage(1120, 1320, QImage.Format.Format_RGB32)
    composite.fill(QColor("white"))
    painter = QPainter(composite)
    painter.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
    painter.setPen(QColor("#183d50"))
    for y, label, filename in ((0, "(a) Risultati della ricerca", "risultati.png"),
                               (660, "(b) Documento Markdown in modifica", "markdown.png")):
        painter.drawText(8, y + 28, label)
        painter.drawImage(0, y + 40, QImage(str(OUT / filename)))
    painter.end()
    assert composite.save(str(OUT / "interfaccia.png"))
    print("Figure generate: schemi e due catture QML, tre documenti sintetici, storage temporaneo.")


if __name__ == "__main__":
    main()
