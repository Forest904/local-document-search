# HW3-04 — Relazione e verifica della consegna

## Risultato

Relazione riscritta il **13 novembre 2026**: 15 pagine A4, sei tabelle, otto figure, testo discorsivo centrato sulle raccomandazioni del docente. Costruzione dei sintetici e dei TXT reali, ground truth, recall e prestazioni sono spiegate separatamente; tre pagine presentano Luma. I punti di forza sono motivati dai risultati, mantenendo i limiti necessari per interpretarli.

Sorgente: [REPORT.md](REPORT.md). PDF locale: `output/pdf/homework-3-report.pdf`. [Build pubblica e di consegna](BUILD.md): contatto fornito dall'utente soltanto nei metadati locali e nella copia finale, non nei file versionati. Nessun invio al docente, push o pubblicazione effettuati.

## Riconciliazione dei dati

- Manifest finale `real-002`: 427 candidati, 392 inclusi (346 PDF, 30 TXT, 16 Markdown), 30 esclusioni senza testo, cinque didattiche, zero errori; **12.979.279 byte UTF-8**. Fra gli inclusi, 18 coppie / 36 documenti duplicati sia per sorgente sia per TXT. Il manifest complessivo conserva 19 coppie di sorgenti perché comprende anche gli esiti esclusi: non sono 19 coppie fra i 392 inclusi.
- Versioni reader registrate: markdown-it-py 4.2.0 e pypdf 7.0.0. Descrizioni confrontate con reader, generatore, campionamento e verificatore nel codice, oltre che con i protocolli.
- Ricalcolate indipendentemente dai conteggi le metriche delle **130 righe** (120 confronti lessicali e dieci bisogni tematici), gli aggregati micro/macro e le numerosità valide. Riconciliati gli aggregati pubblici con i **cinque report locali congelati**, verificandone l'identità mediante `unseal`.
- Riconciliato il report prestazionale identificato dall'hash: **240 confronti**, dei quali **180 campioni misurati**. Ricalcolati mediane, min–max e rapporti per query e campo, escludendo i warm-up dalle statistiche temporali.
- Nessuna nuova annotazione, riscrittura delle query, modifica del motore o ripetizione delle campagne grandi. Nessun difetto di correttezza emerso da queste verifiche; nessuna ottimizzazione introdotta.

I controlli locali sono registrati in `build/homework-3/data-check.json` e nello script di riconciliazione ad hoc `check-data.py`; quest'ultimo verifica la build pubblica e va usato prima della compilazione con contatto. I dati privati e gli artefatti grezzi restano ignorati da Git.

## Test e controllo del PDF

Suite eseguita da `backend/` con `python -m pytest`: **493 passed, 7 skipped**, 500 raccolti, 55,04 s. Comprende tutti i **54 test Homework pertinenti**: 25 corpus, 24 valutazione e cinque pilot; nessuno skip fra questi. Non sono esecuzioni da sommare alla suite completa.

I sette skip sono cinque casi symlink non consentiti nella sessione Windows, un caso di nomi distinti soltanto per maiuscole non supportato dal filesystem e il corpus reale V2 opt-in, diverso dal corpus Homework. La regressione CLI separata ha verificato **10 query e due regressioni PASS**, otto file e 192 byte; JSON locale `build/homework-3/cli-verification.json`.

La copertura esistente include esempi manuali delle metriche, denominatori nulli, Unicode, frasi/BOTH, integrità e riproducibilità dei corpus, conversioni, campionamento, approvazioni, paginazione oltre 50 risultati, errori/timeout ed esportazione senza dati privati. Non sono stati aggiunti test duplicativi a fronte di modifiche documentali; la nuova build è verificata sul PDF effettivo in entrambe le modalità.

Build pubblica controllata: 15 pagine e contatto assente. Copia di consegna: 15 pagine, contatto presente vicino all'autore. Tutte le pagine sono state renderizzate con Poppler e ispezionate; figure, tabelle, formule, didascalie e numerazione controllate. Assenza di `Overfull` e `Missing character` nel log finale. Il messaggio MiKTeX relativo al controllo degli aggiornamenti non impedisce la compilazione.

Le schermate QML sono rigenerate dal sorgente locale su dati sintetici; non sono prove dell'installer. Le figure statistiche usano Matplotlib, installato soltanto come strumento documentale opzionale. Non cambiano dipendenze runtime, API o CLI.

Il riepilogo locale `build/homework-3/final-verification.json` identifica il PDF tramite SHA-256 e registra controllo del contatto, assenza di dati privati nei file versionabili, link PDF e verifica delle 15 pagine. Anche metadati, PDF e log risultano esclusi da Git. `git diff --check` non segnala errori di whitespace.

## Confini della chiusura

La campagna prestazionale estesa rimane rinviata. La correttezza su 10.000 documenti non viene trasformata in evidenza di scalabilità; recall tematica e controllo visuale mantengono i limiti del campione approvato. Corpus funzionale V2-01 e benchmark desktop V2-02 restano distinti.

HW3-04 attesta preparazione e verifica del materiale, non l'invio amministrativo della consegna.
