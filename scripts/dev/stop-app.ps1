param([Parameter(Mandatory)][string]$Repository, [ValidateRange(1, 600)][int]$TimeoutSeconds = 30)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. "$PSScriptRoot/windows-processes.ps1"

$processes = @(Get-DesktopProcesses $Repository)
if (-not $processes.Count) {
    Write-Host 'Nessuna sessione desktop precedente.'
    return
}
Write-Host "Chiusura sessione precedente ($($processes.Count) processi identificati)."
$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
do {
    $remaining = @($processes | Where-Object { Get-SameProcess $_ })
    if (-not $remaining.Count) { break }
    foreach ($process in $remaining) {
        # WM_CLOSE percorre closeEvent: attesa job/letture e rilascio lock M7.
        [void][LdsDev.Windows]::Window($process.ProcessId, $true)
    }
    Start-Sleep -Milliseconds 200
} while ([DateTime]::UtcNow -lt $deadline)

foreach ($process in $processes) {
    if (Get-SameProcess $process) {
        Write-Warning "Timeout: arresto forzato del solo processo desktop $($process.ProcessId)."
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}
foreach ($process in $processes) {
    if (Get-SameProcess $process) {
        Wait-Process -Id $process.ProcessId -Timeout 10 -ErrorAction SilentlyContinue
    }
    if (Get-SameProcess $process) { throw "Processo $($process.ProcessId) ancora attivo; riavvio annullato." }
}
