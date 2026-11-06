param([string]$Python = '')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $Python) { $Python = Join-Path $repository 'backend/.venv/Scripts/python.exe' }
& $Python (Join-Path $PSScriptRoot 'build.py')
if ($LASTEXITCODE -ne 0) { throw "Packaging fallito (exit $LASTEXITCODE)." }
