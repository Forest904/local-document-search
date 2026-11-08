import os
import time

# Isola i test automatici dall'accessibilità e dalle finestre della sessione utente.
# Impostare QT_QPA_PLATFORM=windows per eseguirli con finestre native.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtTest import QTest
from PySide6.QtGui import QGuiApplication


@pytest.fixture(scope="session")
def qt():
    app = QGuiApplication.instance() or QGuiApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def until(predicate, timeout=8000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate():
        assert time.monotonic() < deadline, "Timeout evento Qt"
        QTest.qWait(10)
        # QTest.qWait può trattenere il GIL: lascia eseguire i worker Python reali.
        time.sleep(0.001)
