"""Preferenze v2 persistenti, indipendenti da indici e sorgenti."""
import pytest

from local_document_search.application.contracts import InvalidInput
from local_document_search.application.preferences import DesktopPreferences
from local_document_search.interfaces.composition import compose_v2_application, compose_persistent_application


def test_preferences_restart_clear_and_v1_isolation(tmp_path):
    v1, v2 = tmp_path / "v1", tmp_path / "v2"
    with compose_persistent_application(v1):
        pass
    original = {p.name: p.read_bytes() for p in v1.iterdir() if p.suffix == ".sqlite3"}
    with compose_v2_application(v2) as app:
        assert app.get_preferences.execute() == DesktopPreferences("it", "light")
        app.save_preferences.execute(DesktopPreferences("en", "dark"))
        assert app.status.execute().active_snapshot_id is None
    with compose_v2_application(v2) as app:
        assert app.get_preferences.execute() == DesktopPreferences("en", "dark")
        app.clear_local_data.execute()
        assert app.get_preferences.execute() == DesktopPreferences()
    assert {p.name: p.read_bytes() for p in v1.iterdir() if p.suffix == ".sqlite3"} == original


@pytest.mark.parametrize("language,theme", [("fr", "light"), ("it", "auto"), (None, "dark")])
def test_invalid_preferences(language, theme):
    with pytest.raises(InvalidInput):
        DesktopPreferences(language, theme)
