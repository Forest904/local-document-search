param([Parameter(Mandatory)][string]$InstallRoot, [Parameter(Mandatory)][string]$PreviousManifest,
      [switch]$ValidateOnly,
      [string]$RegistryKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C6B25744-98A8-4B23-B4CF-3E45CA29944E}_is1')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
$key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($RegistryKey)
if (-not $key) { throw 'Installation registration missing' }
try { $registered = [string]$key.GetValue('InstallLocation') } finally { $key.Dispose() }
if (-not $registered -or -not $root.Equals([IO.Path]::GetFullPath($registered).TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Unexpected install path'
}
# Validate every ancestor before accessing or deleting descendants.
$ancestor = $root
while ($ancestor) {
    $node = Get-Item -LiteralPath $ancestor -Force -ErrorAction SilentlyContinue
    if ($node -and (($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'Reparse point in path' }
    $ancestor = Split-Path -Parent $ancestor
}
$old = Get-Content -LiteralPath $PreviousManifest -Raw | ConvertFrom-Json
if (-not $old.files_sha256) { throw 'Invalid previous manifest' }
foreach ($entry in $old.files_sha256.PSObject.Properties) {
    $relative = $entry.Name
    if ($relative -match '(^/|^\\|\.\.|:)' -or $relative -notmatch '\S' -or
        $entry.Value -notmatch '^[A-Fa-f0-9]{64}$') { throw 'Invalid previous manifest entry' }
    $file = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $file.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escapes install root' }
}
if ($ValidateOnly) { exit 0 }
$new = Get-Content -LiteralPath (Join-Path $root 'BUILD-MANIFEST.json') -Raw | ConvertFrom-Json
if (-not $new.files_sha256) { throw 'Invalid new manifest' }
$newNames = @($new.files_sha256.PSObject.Properties.Name)
foreach ($entry in $old.files_sha256.PSObject.Properties) {
    $relative = $entry.Name
    if ($relative -in $newNames) { continue }
    $file = [IO.Path]::GetFullPath((Join-Path $root $relative))
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
