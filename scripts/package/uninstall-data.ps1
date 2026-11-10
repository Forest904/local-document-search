$ErrorActionPreference = 'Stop'
$dataRoot = Join-Path $env:LOCALAPPDATA 'LocalDocumentSearch\Data'
$expected = [IO.Path]::GetFullPath($dataRoot)
$local = [IO.Path]::GetFullPath($env:LOCALAPPDATA)
if (-not $expected.Equals((Join-Path $local 'LocalDocumentSearch\Data'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected data path' }
# Validate every ancestor before accessing or deleting descendants.
$ancestor = $expected
while ($ancestor) {
    $node = Get-Item -LiteralPath $ancestor -Force -ErrorAction SilentlyContinue
    if ($node -and (($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'Reparse point in path' }
    $ancestor = Split-Path -Parent $ancestor
}
if (-not (Test-Path -LiteralPath $expected)) { exit 0 }
$root = Get-Item -LiteralPath $expected -Force
if (($root.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or -not $root.PSIsContainer) { throw 'Data directory is a reparse point or not a directory' }
Get-ChildItem -LiteralPath $expected -Force -Recurse | ForEach-Object {
    if (($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in data directory' }
}
$lock = [IO.File]::Open((Join-Path $expected 'session.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::ReadWrite)
try {
    $lock.Lock(0, 1)
    try {
        Get-ChildItem -LiteralPath $expected -Force | Where-Object Name -NE 'session.lock' | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
    }
    finally { $lock.Unlock(0, 1) }
} finally { $lock.Dispose() }
Remove-Item -LiteralPath (Join-Path $expected 'session.lock') -Force
Remove-Item -LiteralPath $expected -Force
