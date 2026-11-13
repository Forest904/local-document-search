# Generazione e verifica della relazione

[REPORT.md](REPORT.md) è l'unica fonte narrativa. La relazione del 13 novembre 2026 ha **15 pagine, sei tabelle e otto figure**: costruzione dei corpus, ground truth, metriche e risultati sono centrali; tre pagine illustrano Luma. Le evidenze tecniche sono in [HW3_04_REPORT.md](HW3_04_REPORT.md).

## Build pubblica e copia di consegna

Servono Pandoc e MiKTeX/XeLaTeX nel PATH. Il task VS Code **Homework 3: genera PDF**, oppure il comando seguente dalla radice, genera una copia senza email:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/docs/build-report.ps1
```

Il PDF è `output/pdf/homework-3-report.pdf`; LaTeX e log sono in `build/homework-3/`. Questi artefatti sono ignorati da Git. Ogni build sostituisce il PDF di destinazione soltanto dopo una compilazione riuscita.

Per la consegna, predisporre `local-data/homework-3-metadata.yaml`, non versionato, con la chiave `contact-email` e l'indirizzo concordato. Non inserirlo in `REPORT.md`, negli script o in questa guida. Il filtro Lua associa il contatto all'autore durante la compilazione; senza metadati il contatto è assente.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/docs/build-report.ps1 -MetadataFile local-data/homework-3-metadata.yaml
```

Il parametro accetta un file di metadati Pandoc esistente; il percorso è risolto prima di cambiare directory. Anche il LaTeX intermedio della copia di consegna contiene il contatto e deve restare locale. Una build successiva senza metadati produce nuovamente la copia pubblica: controllare sempre quale versione si sta consegnando.

## Figure

Le figure sono versionate. I grafici leggono soltanto `experiments/homework3_results.json` e `experiments/homework3_performance_results.json`; non aprono documenti personali. Gli schemi metodologici usano i conteggi riconciliati nel protocollo corpus e vanno aggiornati se cambiano le evidenze.

Per rigenerare solo schemi metodologici e grafici:

```powershell
backend/.venv/Scripts/python.exe -m pip install matplotlib
backend/.venv/Scripts/python.exe scripts/docs/report_evaluation_figures.py
```

Matplotlib è uno strumento documentale opzionale, non una dipendenza del prodotto o dei test backend. La generazione verificata usa Matplotlib 3.11.2; il rendering PNG non è promesso identico byte per byte fra versioni/font diversi.

Per rigenerare anche gli schemi storici e le schermate, con backend e frontend installati nell'ambiente di sviluppo:

```powershell
backend/.venv/Scripts/python.exe scripts/docs/create-report-figures.py
```

Il comando richiama anche il generatore scientifico. Le schermate usano PySide6 e i font Windows Segoe UI/Consolas, tre documenti sintetici e storage temporaneo. Non modificano la sessione personale. Il rendering QML offscreen non attesta installer o accessibilità nativa. Le figure esistenti consentono la sola build PDF senza installare Matplotlib o avviare Qt.

## Controllo finale

```powershell
pdftoppm -scale-to 1500 -png output/pdf/homework-3-report.pdf build/homework-3/final
```

Ispezionare tutte le pagine, verificando 12–15 pagine, didascalie, tabelle, leggibilità dei diagrammi, collegamenti e numerazione. Nel log XeLaTeX non devono comparire `Overfull` o `Missing character`. Estrarre anche il testo per verificare metriche, unità e presenza del contatto nella sola copia finale; l'estrazione non sostituisce la verifica visuale.

Le metriche derivano dalle valutazioni congelate, non da una nuova esecuzione implicita. La regressione CLI può essere ripetuta separatamente con `backend/.venv/Scripts/python.exe experiments/run_homework3.py`: controllare tutti i dieci casi e le due regressioni. Il suo tempo su otto TXT non sostituisce il pilot sui cento documenti. Campagna estesa e benchmark desktop restano separati.
