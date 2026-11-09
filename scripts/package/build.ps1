param([string]$Python = '', [switch]$Release)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $Python) { $Python = Join-Path $repository 'backend/.venv/Scripts/python.exe' }
if ($Release) {
    & $Python (Join-Path $PSScriptRoot 'build.py') --release
} else {
    & $Python (Join-Path $PSScriptRoot 'build.py')
}
if ($LASTEXITCODE -ne 0) { throw "Packaging fallito (exit $LASTEXITCODE)." }
