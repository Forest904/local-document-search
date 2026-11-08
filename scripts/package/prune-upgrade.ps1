param([Parameter(Mandatory)][string]$InstallRoot, [Parameter(Mandatory)][string]$PreviousManifest)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
$expected = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\LocalDocumentSearchV2')).TrimEnd('\')
if (-not $root.Equals($expected, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected install path' }
if (((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse install root' }
$old = Get-Content -LiteralPath $PreviousManifest -Raw | ConvertFrom-Json
$new = Get-Content -LiteralPath (Join-Path $root 'BUILD-MANIFEST.json') -Raw | ConvertFrom-Json
if (-not $old.files_sha256 -or -not $new.files_sha256) { throw 'Invalid manifest' }
$newNames = @($new.files_sha256.PSObject.Properties.Name)
foreach ($entry in $old.files_sha256.PSObject.Properties) {
    $relative = $entry.Name
    if ($relative -in $newNames) { continue }
    if ($relative -match '(^/|^\\|\.\.|:)') { throw 'Invalid manifest path' }
    $file = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $file.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escapes install root' }
    $parent = Split-Path -Parent $file
    while (-not $parent.Equals($root, [StringComparison]::OrdinalIgnoreCase)) {
        $node = Get-Item -LiteralPath $parent -Force -ErrorAction SilentlyContinue
        if ($node -and (($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'Reparse point in install path' }
        $parent = Split-Path -Parent $parent
    }
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { continue }
    $item = Get-Item -LiteralPath $file -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in payload' }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.Value) { continue }
    Remove-Item -LiteralPath $file -Force
}
