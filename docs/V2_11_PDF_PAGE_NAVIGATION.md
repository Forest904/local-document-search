# V2-11 — PDF alla pagina del primo match

## Requisiti

Un risultato PDF apre un viewer interno alla pagina fisica della prima corrispondenza nel contenuto estratto. Le frasi mantengono la semantica del testo canonico unico e possono attraversare le pagine; la destinazione è la pagina iniziale. Per una corrispondenza solo nel nome si apre la prima pagina. TXT e MD continuano con l'app predefinita. La destinazione proviene dallo snapshot, senza rileggere il sorgente durante la ricerca.

## Stato e limiti

Il codice sorgente conserva gli intervalli delle pagine nello snapshot schema 3 e aggiunge il viewer Qt Quick PDF. Lo schema precedente richiede rebuild esplicito. Il file aperto può differire dalla versione indicizzata e non viene controllato preventivamente. Una pagina fuori intervallo torna alla prima con avviso; il testo e le coordinate esatte non vengono evidenziati. OCR e coordinate geometriche restano futuri.

## Evidenze

Verifiche locali su working tree modificato, Windows 11 x64, Python 3.12.2 e Qt 6.12.0/Qt PDF 6.140.0:

- `cd backend && python -m pytest -q`: **410 passed, 6 skipped**.
- `python -m pytest -q frontend/tests scripts/tests`: **106 passed** (desktop 61, script 45). Il probe QML offscreen ha verificato `currentPage` 2 su un PDF sintetico di tre pagine, fallback a 0 fuori intervallo, errore su file assente e mantenimento del viewer dopo cambio snapshot.
- `python experiments/run_homework3.py`: esecuzione completata sulla regressione CLI TXT.
- `python experiments/run_v2_benchmark.py run experiments/results/v2-target-final experiments/results/v2-11-target --cycles 3 --samples 100 --warmups 5`: report **PASS** per completezza/correttezza, corpus sintetico distinto da V2-01, revisione `d14e753` dirty. Massimi: build 264,630 s, riapertura 18,821 s, no-change 1,165 s, sync 14,574 s, query p95 127,145 ms, working set 1372,4 MB. I budget approvati di avvio 15 s, no-change 1 s e query 100 ms sono superati: **gate prestazionale aperto**, in continuità con gli scostamenti già registrati per V2-10. Gli altri massimi sono entro budget. La cache OS non è stata azzerata.
- Build completa locale finale con `python scripts/package/build.py`: ZIP e installer compilati con Qt PDF e archivio sorgente Qt WebEngine/PDFium verificato SHA-256 `141e9b23…88bb96e7`. Il manifest finale elenca 332 file e attribuisce `qt6pdf.dll`, `qt6pdfquick.dll` e `pdfquickplugin.dll`; il QML del viewer nel payload coincide con il sorgente. SHA-256 ZIP `37764ec18925e0529a72d198e1e3eb92705c06bc7960ba1911870e47e834b60a`; installer `8df62f0823f330d5332a80ed88ccd1013e17131e9a08b45c6b8ebc871dd4bafa`. La build è una prova del sorgente locale dirty, non collaudo install/update/uninstall su account standard isolato. Il nome artefatto `0.2.0` deriva dalla versione pubblica non incrementata e non rappresenta una nuova release.

Non eseguiti collaudo manuale di tastiera/focus/DPI e prova del pacchetto installato su Windows pulito. Nessuna nuova release pubblicata.
