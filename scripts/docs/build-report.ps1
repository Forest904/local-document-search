param([string]$MetadataFile)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$source = Join-Path $repo 'docs/homework-3/REPORT.md'
$work = Join-Path $repo 'build/homework-3'
$destination = Join-Path $repo 'output/pdf/homework-3-report.pdf'
$metadataFilter = Join-Path $PSScriptRoot 'report-metadata.lua'
$metadataArguments = @()
if ($MetadataFile) {
    $metadataPath = (Resolve-Path -LiteralPath $MetadataFile).Path
    $metadataArguments = @('--metadata-file', $metadataPath)
}

foreach ($program in @('pandoc', 'xelatex')) {
    if (-not (Get-Command $program -ErrorAction SilentlyContinue)) {
        throw "Comando mancante: $program. Installare Pandoc e MiKTeX (XeLaTeX) e aggiungerli al PATH."
    }
}
New-Item -ItemType Directory -Force $work, (Split-Path $destination) | Out-Null
Copy-Item -LiteralPath (Join-Path (Split-Path $source) 'figures') -Destination $work -Recurse -Force

Push-Location $work
try {
    & pandoc $source @metadataArguments --lua-filter $metadataFilter --standalone --from markdown+yaml_metadata_block --resource-path (Split-Path $source) --to latex --output 'homework-3-report.tex' --pdf-engine=xelatex -V 'documentclass=article' -V 'papersize=a4' -V 'fontsize=11pt' -V 'geometry:margin=20mm' -V 'mainfont=Latin Modern Roman' -V 'monofont=Latin Modern Mono' -V 'colorlinks=true' -V 'linkcolor=teal' -V 'urlcolor=teal' -V 'linestretch=1.06' -V 'float-placement=H'
    if ($LASTEXITCODE -ne 0) { throw "Pandoc non ha generato il LaTeX (codice $LASTEXITCODE)." }

    for ($pass = 1; $pass -le 2; $pass++) {
        $ErrorActionPreference = 'Continue'
        & xelatex -interaction=nonstopmode -halt-on-error -file-line-error 'homework-3-report.tex' *> "xelatex-pass-$pass.log"
        $ErrorActionPreference = 'Stop'
        if ($LASTEXITCODE -ne 0) { throw "XeLaTeX ha fallito al passaggio $pass. Vedere $work/xelatex-pass-$pass.log e homework-3-report.log." }
    }

    $built = Join-Path $work 'homework-3-report.pdf'
    if (-not (Test-Path $built)) { throw 'PDF compilato non trovato.' }
    $staged = "$destination.new"
    Copy-Item -LiteralPath $built -Destination $staged -Force
    Move-Item -LiteralPath $staged -Destination $destination -Force
    Write-Host "PDF generato: $destination"
}
finally { Pop-Location }
