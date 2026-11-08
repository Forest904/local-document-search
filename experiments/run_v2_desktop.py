"""Probe Qt Quick dal sorgente: ricerca/apertura durante rebuild, non benchmark T08.

Usare un corpus sintetico esistente; non modifica i documenti sorgente.
Output, storage isolato e catture restano sotto la directory di risultati indicata.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
from tempfile import TemporaryDirectory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--query", default="marcatoreuniversale")
    parser.add_argument("--scale", default="1")
    args = parser.parse_args()
    os.environ["QT_SCALE_FACTOR"] = args.scale
    from PySide6 import __version__ as qt_version
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QGuiApplication
    from local_document_search_desktop.controller import DesktopController
    from local_document_search_desktop.composition import compose_desktop
    from local_document_search_desktop.main import create_engine

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QGuiApplication([])
    storage = TemporaryDirectory(prefix="lds-v2-06-probe-")
    c = DesktopController(lambda: compose_desktop(Path(storage.name)), lambda *_: None)
    engine = create_engine(c)
    if not engine.rootObjects():
        raise RuntimeError("QML non caricato")
    window = engine.rootObjects()[0]
    report = {"platform": platform.platform(), "python": sys.version,
              "qt": qt_version, "scale": args.scale, "source": str(args.source.resolve()),
              "query": args.query, "search_open_cycles_during_rebuild": 0,
              "max_event_gap_ms": 0, "max_event_gap_while_rebuild_ms": 0,
              "passed": False}
    stage, last, started = "initialize", time.perf_counter(), time.perf_counter()
    rebuild_seen = False
    screenshots = [("it", "light"), ("it", "dark"), ("en", "light"), ("en", "dark")]
    capture_at = None

    def tick():
        nonlocal stage, last, rebuild_seen, capture_at
        now = time.perf_counter()
        report["max_event_gap_ms"] = max(report["max_event_gap_ms"], (now - last) * 1000)
        if stage in ("rebuild", "load_search", "load_open"):
            report["max_event_gap_while_rebuild_ms"] = max(
                report["max_event_gap_while_rebuild_ms"], (now - last) * 1000)
        last = now
        if now - started > 900:
            report["error"] = "Timeout"
            c.requestClose()
            return
        if c.message_key and c.message_key not in ("ACCEPTED",):
            report["error"] = c.message_key
            c.requestClose()
            return
        v = c.view
        if stage == "initialize":
            c.initialize()
            stage = "select"
        elif stage == "select" and v["canManage"]:
            c.chooseDirectory(QUrl.fromLocalFile(str(args.source.resolve())).toString())
            stage = "build"
        elif stage == "build" and v["searchable"] and not v["running"]:
            report["build_ready_s"] = now - started
            c.editQuery(args.query, len(args.query))
            c.search()
            stage = "first_search"
        elif stage == "first_search" and c.response:
            if not c.response.results:
                report["error"] = "Query senza risultati"
                c.requestClose()
                return
            report["total_matches"] = c.response.total_matches
            c.openResult(0)
            stage = "first_open"
        elif stage == "first_open" and c.selected and v["canManage"]:
            c.action("rebuild")
            stage = "rebuild"
        elif stage == "rebuild":
            rebuild_seen |= v["running"]
            if v["running"] and not v["reading"]:
                c.search()
                stage = "load_search"
            elif rebuild_seen and not v["running"] and v["canManage"]:
                stage = "capture"
        elif stage == "load_search" and not v["reading"] and c.response:
            c.openResult(0)
            stage = "load_open"
        elif stage == "load_open" and not v["reading"]:
            if c.selected and v["running"]:
                report["search_open_cycles_during_rebuild"] += 1
            stage = "rebuild"
        elif stage == "capture" and v["canManage"] and not v["reading"]:
            if screenshots:
                language, theme = screenshots[0]
                c.savePreferences(language, theme)
                capture_at = now + 0.3
                stage = "capture_wait"
            else:
                report["passed"] = report["search_open_cycles_during_rebuild"] > 0
                report["elapsed_s"] = now - started
                c.requestClose()
                stage = "closing"
        elif stage == "capture_wait" and now >= capture_at and v["canManage"]:
            language, theme = screenshots.pop(0)
            window.grabWindow().save(str(output / f"{language}-{theme}.png"))
            stage = "capture"

    timer = QTimer()
    timer.setInterval(25)
    timer.timeout.connect(tick)
    timer.start()
    c.closeReady.connect(app.quit)
    app.exec()
    storage.cleanup()
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
