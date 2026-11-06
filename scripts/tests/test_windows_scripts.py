from pathlib import Path
import json
import os
import subprocess
import sys
import time

import pytest


pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Task di sviluppo Windows")
ROOT = Path(__file__).resolve().parents[2]


def powershell(code):
    return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code],
                          cwd=ROOT, text=True, capture_output=True, timeout=30)


def test_process_recognition_does_not_match_unrelated_python():
    result = powershell(r'''
$ErrorActionPreference = 'Stop'
. './scripts/dev/windows-processes.ps1'
$root = (Get-Location).Path
if (-not (Test-DesktopCommand '"C:\path with spaces\pythonw.exe" -m local_document_search_desktop.main' $root)) { throw 'module' }
if (-not (Test-DesktopCommand '"C:\path with spaces\local-document-search-desktop.exe"' $root)) { throw 'launcher' }
$wrapper = Join-Path $root 'scripts/dev/run_desktop.py'
if (-not (Test-DesktopCommand ('pythonw.exe "' + $wrapper + '" --token test') $root)) { throw 'wrapper' }
foreach ($command in @('python.exe unrelated.py', 'python.exe unrelated.py -m local_document_search_desktop.main', 'python.exe -c "print(''local_document_search_desktop.main'')"', 'python.exe -m another_app', 'python.exe -m local_document_search_desktop.main_extra')) {
    if (Test-DesktopCommand $command $root) { throw "Falso positivo: $command" }
}
''')
    assert result.returncode == 0, result.stdout + result.stderr


def test_pid_reuse_is_not_treated_as_original_process():
    result = powershell(r'''
. './scripts/dev/windows-processes.ps1'
$original = [pscustomobject]@{ProcessId=123; CreationDate='first'; CommandLine='python app'}
function Get-CimInstance { [pscustomobject]@{ProcessId=123; CreationDate='second'; CommandLine='python app'} }
if (Get-SameProcess $original) { throw 'PID riutilizzato accettato' }
''')
    assert result.returncode == 0, result.stdout + result.stderr


def test_all_powershell_files_parse():
    result = powershell(r'''
$ErrorActionPreference = 'Stop'
Get-ChildItem scripts/dev/*.ps1 | ForEach-Object {
    $parseErrors = $null
    $tokens = $null
    [void][Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors) { throw ($parseErrors | Out-String) }
}
''')
    assert result.returncode == 0, result.stdout + result.stderr


def test_detached_launch_returns_with_gui_open(tmp_path):
    """Regressione: la GUI non deve mantenere aperte le pipe catturate del task."""
    process = subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(ROOT / "scripts/dev/start-app.ps1"), "-Repository", str(tmp_path), "-Python", sys.executable],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "QT_QPA_PLATFORM": "windows"},
    )
    try:
        output, error = process.communicate(timeout=20)
        assert process.returncode == 0, output + error
        assert "Desktop pronto" in output
        assert (tmp_path / "runtime/desktop-session.json").exists()
    finally:
        record = tmp_path / "runtime/desktop-session.json"
        if record.exists():
            session = json.loads(record.read_text())
            # Chiude esclusivamente la finestra appena creata da questo test.
            result = powershell(
                ". './scripts/dev/windows-processes.ps1'; "
                f"[void][LdsDev.Windows]::Window({int(session['pid'])}, $true)"
            )
            assert result.returncode == 0, result.stderr
            deadline = time.monotonic() + 10
            while record.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            assert not record.exists(), "La sessione di prova non si e chiusa"
        process.communicate(timeout=10)
