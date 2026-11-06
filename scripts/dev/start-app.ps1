param([Parameter(Mandatory)][string]$Repository, [Parameter(Mandatory)][string]$Python)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. "$PSScriptRoot/windows-processes.ps1"

$runtime = Join-Path $Repository 'runtime'
[void][IO.Directory]::CreateDirectory($runtime)
$sessionFile = Join-Path $runtime 'desktop-session.json'
$token = [Guid]::NewGuid().ToString('N')
$wrapper = Join-Path $PSScriptRoot 'run_desktop.py'
$errorLog = Join-Path $runtime 'desktop-stderr.log'
$launcherId = & $Python $wrapper --session-file $sessionFile --token $token --spawn
if ($LASTEXITCODE -ne 0) { throw "Avvio fallito. Diagnostica locale: $errorLog" }
$launcher = Get-Process -Id ([int]$launcherId) -ErrorAction SilentlyContinue
if (-not $launcher) { throw "Processo desktop terminato durante l'avvio. Controlla $errorLog" }

$deadline = [DateTime]::UtcNow.AddSeconds(30)
do {
    if (Test-Path -LiteralPath $sessionFile) {
        try { $record = Get-Content -LiteralPath $sessionFile -Raw | ConvertFrom-Json }
        catch { $record = $null }
        if ($record -and $record.token -eq $token -and [LdsDev.Windows]::Window($record.pid, $false)) {
            Write-Host "Desktop pronto (PID $($record.pid)); backend integrato nello stesso processo."
            Write-Host 'Premi Continua nella finestra per aprire la sessione persistente.'
            return
        }
    }
    $launcher.Refresh()
    if ($launcher.HasExited) { throw "Avvio fallito. Diagnostica locale: $errorLog" }
    Start-Sleep -Milliseconds 100
} while ([DateTime]::UtcNow -lt $deadline)
throw "La finestra non e pronta dopo 30 secondi. Controlla $errorLog; il processo potrebbe essere ancora in avvio."
