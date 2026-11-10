param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$source = Join-Path $repo 'docs/homework-3/REPORT.md'
$work = Join-Path $repo 'build/homework-3'
$destination = Join-Path $repo 'output/pdf/homework-3-report.pdf'

foreach ($program in @('pandoc', 'xelatex')) {
    if (-not (Get-Command $program -ErrorAction SilentlyContinue)) {
        throw "Comando mancante: $program. Installare Pandoc e MiKTeX (XeLaTeX) e aggiungerli al PATH."
    }
}
New-Item -ItemType Directory -Force $work, (Split-Path $destination) | Out-Null

Push-Location $work
try {
    & pandoc $source --standalone --from markdown+yaml_metadata_block --to latex --output 'homework-3-report.tex' --pdf-engine=xelatex -V 'documentclass=article' -V 'papersize=a4' -V 'fontsize=11pt' -V 'geometry:margin=23mm' -V 'mainfont=Latin Modern Roman' -V 'monofont=Latin Modern Mono' -V 'colorlinks=true' -V 'linkcolor=blue' -V 'urlcolor=blue' -V 'linestretch=1.12'
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
