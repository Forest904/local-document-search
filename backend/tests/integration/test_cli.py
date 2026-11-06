"""Sessioni console reali, pi? gestione diretta dell'interruzione."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from local_document_search.application.contracts import InvalidInput
from local_document_search.domain.queries import SearchField
from local_document_search.interfaces import cli


def run_cli(args, queries=""):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "local_document_search.interfaces.cli", *args],
        input=queries, capture_output=True, text=True, encoding="utf-8", env=env,
    )


@pytest.mark.parametrize("line,field,query", [
    ("nome Roma", SearchField.FILENAME, "Roma"),
    ("contenuto machine \"deep learning\"", SearchField.CONTENT, 'machine "deep learning"'),
    ("entrambi roma", SearchField.BOTH, "roma"),
    ('"nome" roma', SearchField.BOTH, '"nome" roma'),
    ("nomex roma", SearchField.BOTH, "nomex roma"),
    ("roma tre", SearchField.BOTH, "roma tre"),
    ("nome\tRoma", SearchField.FILENAME, "Roma"),
])
def test_prefixes(line, field, query):
    request = cli.parse_input(line)
    assert (request.query, request.field) == (query, field)


@pytest.mark.parametrize("line", ["", " ", "nome", "contenuto ", "entrambi"])
def test_empty_queries_and_prefix_only_are_invalid(line):
    with pytest.raises(InvalidInput):
        cli.parse_input(line)


def test_console_session_prefixes_mixed_queries_and_recovery(tmp_path):
    (tmp_path / "RomaTre.txt").write_text("machine deep learning roma tre", encoding="utf-8")
    (tmp_path / "machine.txt").write_text("deep learning", encoding="utf-8")
    session = run_cli([str(tmp_path)],
                      'nome "roma tre"\ncontenuto machine "deep learning"\n'
                      'entrambi machine "deep learning"\n"\nassente\n')
    assert session.returncode == 0, session.stderr
    assert session.stdout.count("Risultati: 1") == 3
    assert "Risultati: 0" in session.stdout
    assert "machine.txt [" not in session.stdout
    assert "Query non valida" in session.stderr
    assert "indicizzati: 2" in session.stdout


def test_console_prints_every_page(tmp_path):
    for i in range(53):
        (tmp_path / f"{i:03}.txt").write_text("roma", encoding="utf-8")
    session = run_cli([str(tmp_path)], "contenuto roma\n")
    assert session.returncode == 0
    assert "Risultati: 53" in session.stdout
    assert session.stdout.count("[contenuto]") == 53
    assert "052.txt" in session.stdout


def test_console_does_not_start_queries_after_failed_build(tmp_path):
    (tmp_path / "bad.txt").write_bytes(b"\xff")
    session = run_cli([str(tmp_path)], "roma\n")
    assert session.returncode == 1
    assert "bad.txt" in session.stderr
    assert "query>" not in session.stdout


def test_console_argument_errors_and_missing_directory(tmp_path):
    assert run_cli([]).returncode == 2
    assert run_cli([str(tmp_path / "absent")]).returncode == 1
    file = tmp_path / "file.txt"
    file.write_text("test", encoding="utf-8")
    assert run_cli([str(file)]).returncode == 2


def test_console_relative_directory_and_eof(tmp_path):
    relative = os.path.relpath(tmp_path)
    result = run_cli([relative])
    assert result.returncode == 0
    assert "indicizzati: 0" in result.stdout


def test_keyboard_interrupt_returns_130(tmp_path, monkeypatch):
    def interrupt(prompt):
        raise KeyboardInterrupt
    monkeypatch.setattr("builtins.input", interrupt)
    assert cli.main([str(tmp_path)]) == 130


def test_installed_entry_point():
    executable = Path(sys.executable).parent / ("local-document-search.exe" if os.name == "nt" else "local-document-search")
    result = subprocess.run([str(executable), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "directory" in result.stdout


def test_homework_corpus_against_independent_ground_truth():
    import json
    script = Path(__file__).resolve().parents[3] / "experiments" / "run_homework3.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["passed"]
    assert len(report["queries"]) == 10
    assert len(report["regressions"]) == 2
    assert report["indexed"] == 8
