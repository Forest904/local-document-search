param([Parameter(Mandatory)][string]$Repository, [string]$Python = '')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Test-Python([string]$Executable, [string[]]$Prefix = @()) {
    try {
        & $Executable @Prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) and sys.maxsize > 2**32 else 1)' 2>$null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

$venv = Join-Path $Repository 'backend/.venv'
$interpreter = Join-Path $venv 'Scripts/python.exe'
if (Test-Path -LiteralPath $venv) {
    if (-not (Test-Path -LiteralPath $interpreter) -or -not (Test-Python $interpreter)) {
        throw "Ambiente $venv non valido: serve Python >=3.12 x64. Rinominalo o rimuovilo prima di riprovare."
    }
    Write-Host "Ambiente esistente: $venv"
    return $interpreter
}

$selected = $null
$prefix = @()
if ($Python) {
    if (-not (Test-Python $Python)) { throw 'Il parametro -Python deve indicare Python >=3.12 x64.' }
    $selected = $Python
} else {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($version in @('-3.12', '-3')) {
            if (Test-Python $launcher.Source @($version)) {
                $selected = $launcher.Source
                $prefix = @($version)
                break
            }
        }
    }
    if (-not $selected) {
        foreach ($name in @('python.exe', 'python3.exe')) {
            $candidate = Get-Command $name -ErrorAction SilentlyContinue
            if ($candidate -and (Test-Python $candidate.Source)) {
                $selected = $candidate.Source
                break
            }
        }
    }
}
if (-not $selected) { throw 'Installa Python >=3.12 x64 (consigliato 3.12), oppure passa -Python C:\percorso\python.exe.' }
Write-Host "Creazione ambiente: $venv"
& $selected @prefix -m venv $venv
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $interpreter)) {
    throw "Creazione ambiente fallita: $venv"
}
return $interpreter
