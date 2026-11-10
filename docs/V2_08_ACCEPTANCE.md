# V2-08 — Registro di accettazione della release 0.2.0

Stato: **completato il 9 novembre 2026** sul candidato identificato da commit pulito, SHA-256 dell'installer e manifest dello stesso payload. Le prove storiche V2-07 e del redesign Luma non sono state trasferite automaticamente.

Verifiche sul sorgente prima del commit candidato (Windows 11 build 26200, CPython 3.12.2): suite congiunta backend/frontend/script **461 passed, 6 skipped**; corpus reale completo opt-in mirato **6 passed**; runner Homework **PASS**; `pip check` **PASS**. Il runner V2-02 su corpus smoke, un ciclo e due campioni, ha prodotto `PASS` con revisione di base `05e9c2a` e working tree modificato: è solo un controllo funzionale del runner, non T08 né prova del pacchetto. Report locali in `experiments/results/`, fuori Git.

## Candidato e prove locali

Candidato da revisione pulita `3b78203e6cfbb3be1b01d8bed82728c45b56ab00`. CI GitHub `Backend and desktop`, run `42522632704`: **success** su Windows e Ubuntu. Build `./scripts/package/build.ps1 -Release` completata con CPython 3.12.2, MSVC 2022 e Inno Setup 6.7.3. Installer `LocalDocumentSearch-0.2.0-windows-x64-setup.exe`, SHA-256 `a13f53a76e6ef8a09f8efb023c6b32c4702f1b74ae699198b220e7e34dd883b3`. Manifest con `dirty_worktree=false`, 319 file inventariati e 319 hash verificati senza differenze nello staging e nell'installazione. Il file `.manifest.json` esterno corrisponde all'hash dell'installer. La reinstallazione silenziosa sul laptop ha restituito exit 0, senza riavvio. Diagnostica smoke dall'EXE installato: `PASS`, un ciclo, due campioni; avvio UI con `LOCALAPPDATA` isolato rimasto attivo per cinque secondi senza creare storage prima dell'informativa. Il 9 novembre, in una prova interattiva dello stesso EXE installato su un altro `LOCALAPPDATA` temporaneo, l'informativa è stata accettata, il corpus sintetico M9 da 12 TXT/MD/PDF è stato indicizzato, `corpus comune` ha restituito **12 risultati** con estratti e il clic sul primo TXT ha aperto `NomeSolo00000.txt` in Blocco note con il testo previsto. Questa prova non copre apertura MD/PDF, carico o accessibilità con Narrator.

T08 dal pacchetto compilato sul laptop Windows 11 build 26200, Ryzen AI 7 350, 32 GB RAM, SSD WD SN5000S, Balanced e batteria in carica: corpus target 10.000 file, 299.948.099 byte estratti, tre cicli indipendenti, cinque warm-up e cento campioni/query. Il run finale `report.json` è `PASS` con `budget_status=PASS`: massimi build **215,01 s**, avvio fino alla ricerca **9,53 s**, no-change **0,781 s**, sync 100/100/100 **5,04 s**, query p95 **97,52 ms**, working set **1.359,1 MiB**. Cache OS non svuotata e processi nuovi per fase. Report grezzo in `%TEMP%/lds-v2-08-packaged-target-final/output/`.

Un run precedente dello stesso commit è stato interrotto dopo un ciclo completo: il suo report resta `INCOMPLETE` e quel ciclo aveva p95 **103,48 ms** per `"frasecomune consecutiva"` nel contenuto, sopra il budget di 100 ms. Un ulteriore run da due cicli è `PASS` e `budget_status=PASS` (massimo p95 92,47 ms). I risultati indicano variabilità vicino al limite: il run finale completo soddisfa T08, ma lo scostamento osservato rimane registrato.

Il kit per il PC pulito comprendeva installer/checksum/manifest, precedenti installer (0.1.9 solo di prova), corpus/fixture, scheda e benchmark. I 30 file di `KIT-SHA256.txt` coincidevano dopo la copia. Al ritorno l’hash installer coincideva ancora; la scheda compilata era necessariamente cambiata. Sul PC pulito la verifica hash è attestata come «sì», senza digest trascritto. Log e report grezzi restano fuori Git.

## Collaudo sul PC pulito

Scheda restituita il 9 novembre 2026 per il candidato `3b78203`: Windows 11 build `26200.9445`, AMD Ryzen 5 2600X 3,60 GHz, 32 GB RAM, disco con 137 GB usati su 466 GB. Account standard di test distinto e vergine, rete disconnessa, Python e tool di sviluppo assenti. Nessun avviso Windows o errore segnalato. I tempi di questo PC non sono stati misurati e non sono confrontati con il benchmark del laptop di riferimento.

La scheda e successive conferme puntuali coprono i casi della matrice sotto, inclusi reader problematici, symlink/junction, snapshot dopo errore, doppia istanza, pulizia durante job, downgrade, termini IT/EN e sostituzione Qt. Tastiera/Narrator verificati su selezione, ricerca, risultati/apertura, Impostazioni, focus e dialoghi nelle due lingue e nei temi. Sono **resoconti manuali dell’utente**: la scheda raggruppa i casi, senza una riga per prova. Nessun fallimento segnalato.

## Pubblicazione successiva

Il tag Git `v0.2.0` punta al commit candidato `3b78203`, non al successivo commit di merge. La [Release GitHub v0.2.0](https://github.com/Forest904/local-document-search/releases/tag/v0.2.0) distribuisce l'installer collaudato, il checksum e un manifest pubblico senza percorsi assoluti del laptop. L'EXE è stato scaricato dalla Release: 158.370.246 byte e SHA-256 `a13f53a76e6ef8a09f8efb023c6b32c4702f1b74ae699198b220e7e34dd883b3`, uguale all'originale sulla chiavetta. `/releases/latest` indirizza a `v0.2.0`.

## Evidenze desktop precedenti al candidato

Il prototipo Qt Quick dell’8 novembre 2026 (base `2ad36c1aeff3ecd0cc5c478ccd401e20861d9dd0`, working tree modificato) fu provato su Windows 11 build 26200, Python 3.12.2, PySide6 6.12.0, Ryzen AI 7 350/32 GB. Suite backend 384 passed/6 skipped, frontend 27 passed, script 17 passed; Homework e pip check PASS. Probe sorgente target: 10.000 documenti, 421 cicli ricerca/anteprima durante rebuild, loop Qt massimo 635 ms incluse catture. Era una prova di concorrenza, non T08 o Narrator completo.

Il redesign Luma successivo (build base `e103de792dfb2e841255a238082f2a06b2c67620`, working tree modificato) verificò navigazione, filtri/reset, apertura singola, focus e IT/EN: frontend 39 passed, poi 40 dopo ritocchi logo/toggle. Probe small a scala 1/2 con opener stub: 6/8 cicli ricerca/apertura; non prova dell’app esterna. Catture native furono necessarie per font/layout, non verificabili offscreen. Tre test QML nativi passarono con avviso COM `0x8001010d`: non una prova pulita di accessibilità. Entrypoint corretto dopo un primo smoke fallito e coperto da regressione.

Questi prototipi e i loro conteggi non identificano il binario distribuito né trasferiscono l’approvazione del payload V2-07. Narrator, tastiera completa e UI Luma sul candidato pulito sono verificati nel [collaudo sul PC pulito](#collaudo-sul-pc-pulito); tale prova chiude anche V2-06. I dati delle prove precedenti restano storici, senza nuova esecuzione durante la revisione documentale.

## Procedura del candidato

1. Su revisione pulita eseguire suite backend/frontend/script, Homework e corpus reale completo; registrare commit e CI.
2. Costruire con `./scripts/package/build.ps1 -Release`; verificare hash, manifest, licenze e risorse dello stesso payload.
3. Generare small/adverse/target; eseguire la [diagnostica installata](../scripts/package/README.md#diagnostica-e-collaudo). T08 richiede target 10.000/300 MB, tre cicli, cinque warm-up e cento campioni/query.
4. Usare corpus/fixture sintetici (`m9_corpus.py`, `error_fixtures()`) e storage isolato per gli [scenari](TEST_STRATEGY.md); conservare log/catture fuori Git.
5. Trasferire installer/checksum/manifest, installer precedente identificato, corpus e scheda; ricontrollare hash. Collaudare offline con account standard distinto su Windows pulito senza Python/tool. Compilare la scheda sotto.

## Matrice dei gate

`PASS sorgente` indica la suite della revisione candidata; `PASS PC pulito` indica la scheda restituita e, per i dettagli non trascritti, la conferma successiva dell'utente. Il benchmark compilato è distinto dalla UI manuale.

| Scenario | Stato | Evidenza |
|---|---|---|
| T01 | PASS PC pulito | Installazione e uso offline con account standard distinto, senza tool di sviluppo |
| T02 | PASS sorgente + PC pulito | Reader TXT/MD/PDF, vuoti e problematici; esclusione symlink/junction confermata |
| T03 | PASS sorgente | Suite backend: AND, frasi, BOTH e regressioni query esatte |
| T04 | PASS sorgente | Suite backend: vocabolari dopo build, update, restart e recovery |
| T05 | PASS sorgente + PC pulito | Prefissi per campo/snapshot nella suite; suggerimenti UI nel collaudo |
| T06 | PASS sorgente + PC pulito | Filtri/ranking/totali/pagine nella suite; filtri e pagine sul pacchetto |
| T07 | PASS sorgente + PC pulito | Snippet/highlight Unicode nella suite; estratti e apertura file sul pacchetto |
| T08 | PASS pacchetto, scostamento registrato | Tre cicli target entro budget; p95 103,48 ms in un ciclo del run interrotto, che resta INCOMPLETE |
| T09 | PASS sorgente + PC pulito | Diff, A→B→A e fault nella suite; cambio cartella, rebuild, snapshot precedente e recovery sul pacchetto |
| T10 | PASS sorgente + PC pulito | Cancel e commit nella suite; cancel e pulizia rifiutata durante job sul pacchetto |
| T11 | PASS sorgente | Variazione dei metadati durante ingestione; limite size+mtime identici documentato |
| T12 | PASS sorgente + PC pulito | Controller/QML e prova locale; ricerca e apertura sotto carico sul pacchetto, risposte obsolete nella suite |
| T13 | PASS PC pulito | IT/EN, temi, DPI, tastiera, focus, dialoghi e Narrator sui flussi principali |
| T14 | PASS sorgente + PC pulito | Isolamento v1 nella suite; upgrade e sorgenti/dati v1 intatti sul PC pulito |
| T15 | PASS PC pulito | Wizard, upgrade 0.1.9 di prova, reinstallazione, downgrade bloccato, avvio offline |
| T16 | PASS PC pulito | Disinstallazione con conservazione e cancellazione esplicita; lock e pulizia durante job |
| T17 | PASS candidato + PC pulito | Inventario/licenze/manifest, termini IT/EN, DLL Qt sostituita, assenza di avvisi e rete |
| T18 | PASS sorgente | CLI Homework senza Qt, runner PASS |
| T19 | PASS candidato | CI Windows/Ubuntu, commit pulito, manifest e hash dell'installer ricontrollato |
| T20 | PASS sorgente | Corpus sintetico riproducibile nella suite ordinaria |
| T21 | PASS sorgente opt-in | Corpus reale completo, 6 test mirati |
| M9-G01 | PASS PC pulito | Cambio directory e rebuild sul pacchetto |
| M9-G02 | PASS PC pulito | Pulizia rifiutata durante job sul pacchetto |
| M9-G03 | PASS PC pulito | PDF problematici e TXT/MD vuoti sul pacchetto |
| M9-G04 | PASS PC pulito | Ricerca e apertura sotto carico sul pacchetto |
| M9-G05 | PASS PC pulito | Windows pulito senza Python/tool di sviluppo, offline |
| M9-G06 | PASS PC pulito | Account standard distinto e vergine |
| M9-G07 | PASS candidato | CI e artefatto da revisione pulita |

## Scheda per il PC pulito

Registrare commit, hash installer verificato dopo copia, Windows/build, CPU/RAM/disco, account, rete e assenza di tool. Per ogni scenario della matrice: PASS/FAIL/NON ESEGUITO, passi, messaggi e avvisi. Identificare la versione usata per upgrade/reinstallazione/downgrade; verificare disinstallazione con dati conservati e cancellati, sorgenti/v1 intatti. Separare i tempi del PC di collaudo dal benchmark dell’hardware di riferimento.
