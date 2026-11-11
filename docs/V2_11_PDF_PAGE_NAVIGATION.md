# V2-11 — PDF alla pagina del primo match

## Requisiti

Un risultato PDF apre un viewer interno alla pagina fisica della prima corrispondenza nel contenuto estratto. Le frasi mantengono la semantica del testo canonico unico e possono attraversare le pagine; la destinazione è la pagina iniziale. Per una corrispondenza solo nel nome si apre la prima pagina. TXT e MD continuano con l'app predefinita. La destinazione proviene dallo snapshot, senza rileggere il sorgente durante la ricerca.

## Stato e limiti

Il codice sorgente conserva gli intervalli delle pagine nello snapshot schema 3 e aggiunge il viewer Qt Quick PDF. Lo schema precedente richiede rebuild esplicito. Il file aperto può differire dalla versione indicizzata e non viene controllato preventivamente. Una pagina fuori intervallo torna alla prima con avviso. Il viewer offre ora ricerca manuale sul testo del PDF aperto, con evidenziazione Qt delle occorrenze. La query associata alla risposta è proposta senza avviare la ricerca. I PDF senza testo ricercabile disabilitano il comando. La posizione esatta della query Luma non viene evidenziata automaticamente; OCR e coordinate geometriche dello snapshot restano futuri.

La rifinitura usa un adattamento locale del QML `PdfMultiPageView` di Qt PDF 6.140.0, con copyright e licenza originali. Riduce spazio orizzontale e bounce, limita lo zoom manuale, modera il pinch e aggiunge controlli a icona e apertura della cartella originale. Il controllo del testo usa un documento Qt separato su worker; gli esiti di aperture precedenti vengono scartati. Nessun cambio di schema o dipendenza.

## Evidenze

Verifiche locali su working tree modificato, Windows 11 x64, Python 3.12.2 e Qt 6.12.0/Qt PDF 6.140.0:

- `cd backend && python -m pytest -q`: **410 passed, 6 skipped**.
- `python -m pytest -q frontend/tests scripts/tests`: **106 passed** (desktop 61, script 45). Il probe QML offscreen ha verificato `currentPage` 2 su un PDF sintetico di tre pagine, fallback a 0 fuori intervallo, errore su file assente e mantenimento del viewer dopo cambio snapshot.
- `python experiments/run_homework3.py`: esecuzione completata sulla regressione CLI TXT.
- `python experiments/run_v2_benchmark.py run experiments/results/v2-target-final experiments/results/v2-11-target --cycles 3 --samples 100 --warmups 5`: report **PASS** per completezza/correttezza, corpus sintetico distinto da V2-01, revisione `d14e753` dirty. Massimi: build 264,630 s, riapertura 18,821 s, no-change 1,165 s, sync 14,574 s, query p95 127,145 ms, working set 1372,4 MB. I budget approvati di avvio 15 s, no-change 1 s e query 100 ms sono superati: **gate prestazionale aperto**, in continuità con gli scostamenti già registrati per V2-10. Gli altri massimi sono entro budget. La cache OS non è stata azzerata.
- Build completa locale finale con `python scripts/package/build.py`: ZIP e installer compilati con Qt PDF e archivio sorgente Qt WebEngine/PDFium verificato SHA-256 `141e9b23…88bb96e7`. Il manifest finale elenca 332 file e attribuisce `qt6pdf.dll`, `qt6pdfquick.dll` e `pdfquickplugin.dll`; il QML del viewer nel payload coincide con il sorgente. SHA-256 ZIP `37764ec18925e0529a72d198e1e3eb92705c06bc7960ba1911870e47e834b60a`; installer `8df62f0823f330d5332a80ed88ccd1013e17131e9a08b45c6b8ebc871dd4bafa`. La build è una prova del sorgente locale dirty, non collaudo install/update/uninstall su account standard isolato. Il nome artefatto `0.2.0` deriva dalla versione pubblica non incrementata e non rappresenta una nuova release.

Non eseguiti collaudo manuale di tastiera/focus/DPI e prova del pacchetto installato su Windows pulito. Nessuna nuova release pubblicata.

## Verifica della rifinitura

Su Windows 11 con PySide6 6.12.0 e Qt PDF 6.140.0, il probe ha confermato `QPdfDocument.getAllText()` su pagine testuali e vuote. I test QML offscreen verificano il salto iniziale, la query della risposta precompilata senza ricerca automatica, la prima e successive occorrenze, navigazione inversa, ricerca senza risultati, Escape, PDF senza testo, PDF misto, larghezza iniziale del contenuto, zoom dei pulsanti e apertura della cartella. La suite backend è **410 passed, 6 skipped**; frontend/script **111 passed, 1 deselected**; runner Homework completato. La suite frontend/script senza esclusioni ha fallito unicamente il test dell'installer silenzioso, che rifiuta l'esecuzione con Local Document Search già aperto nella sessione Windows.

La build completa nell'ambiente bloccato (`python scripts/package/build.py --inside-venv`) è riuscita: ZIP SHA-256 `64ac8e00f6db7d21e7a72265f211105aa7c2724c5f91474e17e9eb911af9d2ac`, installer SHA-256 `bb7b137c04ee573316587d52c2ddafca3ec74e439b94cf79344d1caf1d415ad5`. Il manifest inventaria 343 file e attribuisce `LocalPdfMultiPageView.qml` a Qt PDF/Qt WebEngine, con avviso LGPL e sorgente incluso. I tre QML del viewer nello ZIP coincidono byte per byte col sorgente finale. Il payload comprende `PySide6/QtPdf.pyd`: uno smoke test dell'eseguibile confezionato, con dati locali temporanei e Qt offscreen, ha confermato l'avvio per cinque secondi senza uscita anticipata. Si tratta di artefatti locali con nome di versione invariato, non di una release pubblicata.

Non è stato eseguito il collaudo fisico del pinch su touchpad, del focus con Narrator, dei DPI e dell'installer su Windows pulito. Lo smoke test dell'eseguibile verifica l'avvio offline, non ancora apertura e salto nel viewer del binario confezionato. Il benchmark precedente non è stato ripetuto per la rifinitura del viewer.

## Barra di lettura ispirata a Firefox

Il viewer occupa la larghezza della finestra. Una barra fissa in alto riunisce ritorno, nome del file, pagina, zoom, ricerca, rotazione e azioni esterne; il documento scorre nello spazio sottostante. La ricerca manuale apre una barra in basso con navigazione, conteggio ed evidenziazione di tutte le occorrenze, inizialmente disattivata. Restano esclusi miniature, stampa e annotazioni. La modalità automatica adatta alla larghezza la pagina corrente senza ingrandirla oltre il 100%; sono disponibili anche larghezza, pagina e 100%. Le pagine che entrano nel viewport restano centrate senza scorrimento laterale; a zoom elevato si raggiungono i bordi senza ampie aree vuote.

Verifiche di questa iterazione: backend **410 passed, 6 skipped**; frontend e script **113 passed, 1 deselected** (installazione silenziosa con app già aperta); runner Homework completato. I test QML offscreen coprono barra e navigazione pagina, zoom, rotazione, evidenziazione selettiva e centratura di pagine con larghezze diverse.

La build locale completa nell'ambiente bloccato è riuscita. SHA-256 dello ZIP: `334c077c946d19567fdf97816699eea2b923e39ecaa4270c027d4552194028c7`; installer: `dfc47b0291e8c94d919592b4b593ba9e0066bf342f2af2a51a2a1b426cf95616`. Lo ZIP contiene 346 file e `PySide6/QtPdf.pyd`; `Main.qml`, i due QML del viewer e le due icone di rotazione coincidono byte per byte con i sorgenti locali. Il nome `0.2.0` resta quello della versione pubblica corrente: questa build locale non è una release. Non sono stati eseguiti il collaudo manuale su touchpad, Narrator, temi/DPI e l'installazione su Windows pulito; il test del pacchetto non prova ancora l'interazione completa nel binario installato.

## Correzione dell'overlay e dei colori

La barra superiore e quella di ricerca sono livelli opachi sopra il viewport PDF: le pagine scorrono dietro i controlli, mentre margini interni al contenuto mantengono leggibili l'inizio e la fine. Il menu dello zoom usa colori espliciti per pulsante, indicatore, voci e popup nei temi chiaro e scuro; anche campi, casella di evidenziazione, tooltip e messaggi del viewer seguono la palette locale. Nessun cambio a backend, schema o dipendenze.

Il test QML offscreen scorre un PDF sintetico multipagina e verifica che la barra resti sopra il viewport, quindi apre il popup nei due temi e ne controlla lo sfondo. Le suite locali di questa correzione riportano backend **410 passed, 6 skipped**, frontend/script **114 passed, 1 deselected** (installer silenzioso con app aperta), runner Homework completato. Il test offscreen non sostituisce una verifica visiva dell'hover e del contrasto su Windows nativo.

La build locale della correzione è riuscita: ZIP SHA-256 `3143900059ced12aa64b96b3839e1b7a741eea68b213f4bcb08ff42f23c816e1`, installer SHA-256 `4cdf13a710973f840a154fa0d0035cd62344e367a8ff495266799fb78953fb0a`. Lo ZIP contiene 347 file; i cinque QML coinvolti, incluso il nuovo controllo dello zoom, coincidono byte per byte con i sorgenti. Il pacchetto non è stato installato o pubblicato.

La barra «Trova» è stata poi portata nell'overlay della finestra, sopra il livello locale del PDF e della barra superiore. Il margine inferiore del documento resta attivo quando la ricerca è aperta. Il test QML verifica posizione nella finestra, visibilità, ordine dei livelli e margine inferiore; **9 test PDF passati** sul sorgente. Questa correzione successiva non è inclusa negli hash del pacchetto riportati sopra.

Escape è gestito dalla finestra: chiude prima «Trova» indipendentemente dal controllo che ha il focus, quindi torna ai risultati alla pressione successiva. Il test QML copre entrambe le pressioni anche con il focus sulla casella di evidenziazione. Dopo questa modifica, la suite frontend riporta **69 passed**.

## Menu zoom ampliato

Il controllo centrale a pillola offre, nell'ordine, zoom automatico, dimensione reale, adatta pagina, adatta larghezza e preset 50%, 75%, 100%, 125%, 150%, 200%, 300%, 400%. La selezione dei preset imposta direttamente la scala Qt; i pulsanti e il pinch mantengono il loro percorso esistente e mostrano la percentuale corrente. Il popup usa gli stessi colori espliciti nei temi chiaro e scuro. I test QML verificano tutte le percentuali e il ritorno a dimensione reale. Le immagini offscreen del popup sono state ispezionate per geometria e contrasto; nell'ambiente offscreen i glifi appaiono come quadrati per assenza dei font di sistema. Questa iterazione non è inclusa negli hash di build precedenti.
