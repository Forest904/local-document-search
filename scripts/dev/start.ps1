param(
    [string]$Python = '',
    [ValidateRange(1, 600)][int]$CloseTimeoutSeconds = 30
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$hash = [Security.Cryptography.SHA256]::Create()
try {
    $key = [BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($repo.ToLowerInvariant()))).Replace('-', '')
} finally { $hash.Dispose() }
$mutex = [Threading.Mutex]::new($false, "Local\LocalDocumentSearch.Dev.$key")
$owned = $false
try {
    try { $owned = $mutex.WaitOne(0) }
    catch [Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { throw 'Un altro task di avvio e gia in corso per questo repository.' }
    $interpreter = & "$PSScriptRoot/environment.ps1" -Repository $repo -Python $Python
    & "$PSScriptRoot/stop-app.ps1" -Repository $repo -TimeoutSeconds $CloseTimeoutSeconds
    & $interpreter "$PSScriptRoot/dependencies.py" --repository $repo
    if ($LASTEXITCODE -ne 0) { throw 'Preparazione dipendenze fallita. Avvio annullato.' }
    & "$PSScriptRoot/start-app.ps1" -Repository $repo -Python $interpreter
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
} finally {
    if ($owned) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
