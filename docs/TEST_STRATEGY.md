# Strategia di verifica v2

HW3-01 usa `backend/tests/integration/test_homework3_corpus.py` per fixture piccole di preparazione e verifica. Copre riproducibilità da seed/ID e indipendenza dal profilo, annidamento, varietà di dimensioni/sezioni/strutture, tutte le materie in IT/EN, famiglie riservate e termini assenti. Le frasi consecutive, interrotte da una parola e invertite sono controllate direttamente sui testi, senza analyzer del prodotto; si controllano anche coppie distanti e contaminazioni fra campi. Le prove negative coprono file mancanti/aggiuntivi, hash, conteggi, byte, identità e metadati alterati, volume fuori tolleranza, UTF-8 invalido e destinazioni esistenti. I manifest schema 1 restano una regressione esplicita. La prova congiunta riduce i conteggi dei tre profili nelle fixture, senza cambiare dimensioni o generazione per ID.

La verifica completa dei tre profili da 100/1.000/10.000 TXT tramite `verify-nested`, l'integrità del corpus reale e la revisione manuale sono prove separate opt-in, registrate nel [protocollo HW3-01](homework-3/HW3_01_CORPUS.md). La regressione `experiments/run_homework3.py` deve riportare esplicitamente dieci query e due regressioni superate. Queste prove non misurano recall o prestazioni dei nuovi corpus e non sostituiscono V2-01/V2-02.

Una specifica approvata non equivale a codice funzionante. Conservare test v1 e CLI Homework come regressione; estenderli con il [corpus ibrido funzionale](TEST_DATASETS.md), usando report legati a revisione e artefatto. [Evidenze storiche](archive/v1/README.md), [lacune M9](V2_08_ACCEPTANCE.md#matrice-dei-gate). I casi qui sono scenari da eseguire nelle milestone, non risultati già ottenuti.

## Validazione funzionale V2-01

T20/T21 sono in `backend/tests/integration/test_v2_corpus.py`: sintetici riproducibili nella suite offline, reali opt-in con manifest completo e hash corretti. Confrontare liste complete di percorsi, non conteggi; corpus/ground truth assenti o alterati non sono PASS. [Metodo, provenienza e risultati](TEST_DATASETS.md). Questo corpus non definisce obiettivi di prestazione.

## Metodo e criteri

Per T08 il runner V2-02 in `experiments/run_v2_benchmark.py` usa tre cicli
indipendenti e processi nuovi per build, riapertura, no-change, query e sync
incrementale. Il corpus sintetico è distinto da T20/T21 e verificato con hash
prima della prova; i risultati grezzi restano fuori Git. Le query hanno cinque
warm-up e cento campioni, ordine mescolato deterministico, pagina 50 e p95
nearest-rank; gli attesi completi sono derivati dai marcatori del generatore.
Registrare tempi individuali dei job, memoria del processo, ambiente, revisione,
dimensione del testo estratto e condizioni di cache. La cache OS non è svuotata;
un processo nuovo non è una misura a cache fredda. Report incompleti o errori
non valgono come PASS. I budget T08 originari, ora storici, erano approvati in V2-D01:
massimo query p95 ≤100 ms, avvio fino alla ricerca ≤15 s, build ≤300 s,
sync incrementale 100/100/100 ≤60 s, no-change ≤1 s e picco working set
≤2560 MiB. Si applica il massimo dei tre cicli e, per le query, il massimo
dei p95 di tutti i casi. [Metodo ed evidenze](PERFORMANCE.md#v2-02); la prova
sul pacchetto finale è documentata in V2-08.

Revisione approvata il 12 novembre 2026 per le nuove prove: p95 ≤100 ms separatamente per query esatte, wildcard ordinarie e suggerimenti; p95 ≤200 ms per `frasecom*` nel contenuto; no-change ≤2 s. Gli altri limiti e il massimo di tre cicli restano invariati. Il confronto fra compilati e la correttezza completa sono richiesti per T08; un rallentamento non spiegato, descritto con i limiti dell'indagine, non blocca l'accettazione se tutti i nuovi limiti sono rispettati.

Unit test per dominio, contratti per reader/storage, integrazione per sync/concorrenza, E2E per CLI e desktop, collaudo sul pacchetto installato. La suite deve raccogliere test effettivi. Benchmark separati per lookup, intersezione, ranking, serializzazione, caricamento e UI; corpus, seed, hardware, OS, cache, revisioni e distribuzioni delle durate registrati. I budget V2-02 sono fissati sopra prima delle ottimizzazioni. Il target è 10.000 file e 300 MB di testo estratto; includere anche corpus piccolo e casi avversi. Non confrontare tempi M9 con condizioni diverse.

## Scenari di accettazione

| ID | Scenario e risultato atteso | Milestone |
|---|---|---|
| T01 | Installer e flussi completi offline su Windows 11 x64 pulito, account standard distinto, senza Python/tool di sviluppo | V2-08 |
| T02 | TXT/MD/PDF testuali, PDF protetto/vuoto/misto e TXT/MD vuoti; symlink/junction esclusi; errori distinti dalle esclusioni | V2-04, V2-08 |
| T03 | AND, frasi, termini ripetuti e BOTH nello stesso campo; match identici a v1 per query esatte | V2-03 |
| T04 | Vocabolari ordinati coerenti dopo build, update, restart e recovery; confronto strutture e costi documentato | V2-03, V2-04 |
| T05 | Prefisso esplicito e suggerimenti corretti per campo/versione; digitazione non avvia query; limiti approvati. Backend V2-03 coperto da `test_v2_retrieval.py`; integrazione digitazione UI in V2-06 | V2-03, V2-05, V2-06 |
| T06 | Filtri e ranking su soli match, totale/pagina coerenti; ordine deterministico e alternativa per percorso. Backend: `test_v2_search_application.py` | V2-05 |
| T07 | Snippet e highlight Unicode/frasi nella versione del risultato; backend: `test_v2_search_application.py`. Estratti e apertura diretta UI sotto carico: V2-06/V2-08 | V2-05, V2-06, V2-08 |
| T08 | Budget approvati su 10.000/300 MB per p95 query, avvio, build, sync, RAM; metodologia e limiti registrati | V2-02, V2-03, V2-04, V2-08 |
| T09 | Add/modify/remove, no-change, A→B→A, rebuild, fault commit, recovery; mai snapshot parziale o directory errata | V2-04, V2-08 |
| T10 | Cancel durante estrazione/build conserva N e produce CANCELLED; cancel al commit rifiutato; pulizia durante job rifiutata | V2-04, V2-06, V2-08 |
| T11 | Sorgente modificato durante lettura con metadati diversi: fallimento/retry; size+mtime identici resta limite dichiarato | V2-04 |
| T12 | UI Luma usabile durante build, ricerca e apertura diretta; query/filtri/directory obsolete non sovrascrivono stato corrente | V2-06, V2-08 |
| T13 | Italiano/inglese, temi persistenti, tastiera, focus, contrasto, DPI e Narrator su flussi principali | V2-06, V2-08 |
| T14 | Prima selezione v2 e upgrade v2 senza leggere, alterare o cancellare dati v1 | V2-04, V2-07 |
| T15 | Wizard IT/EN install/update/uninstall completo senza rete o elevazione; scelta di cartella nuova o vuota su disco locale fisso alla prima installazione, percorso registrato negli upgrade, riepilogo aggiornato, retry con app aperta, avvio finale opzionale; runtime Qt/Python inclusi, reinstallazione consentita e downgrade bloccato | V2-07, V2-08 |
| T16 | Disinstallazione conserva dati per default anche in modalità silenziosa; cancellazione solo esplicita con lock, rifiuto durante job, sorgenti/v1 intatti | V2-07, V2-08 |
| T17 | Nessuna connessione richiesta; termini IT/EN mostrati nel wizard senza casella; inventario dei file runtime con fonte, licenza, avviso e sorgenti Qt verificati; DLL Qt ricostruita e sostituita in una copia dell'installazione; avvisi release non firmata registrati | V2-07, V2-08 |
| T18 | Runner Homework e CLI: sintassi, ordine, codici e installazione backend senza Qt invariati | V2-03, V2-05, V2-08 |
| T19 | CI della revisione finale, manifest/hash del pacchetto e risultati legati alla stessa revisione pulita | V2-08 |
| T20 | Sintetici TXT/MD/PDF riproducibili: analyzer, campi, AND, frasi, Unicode e edge case confrontati con ground truth indipendente dal motore | V2-01 |
| T21 | 12–30 file reali autorizzati, IT/EN e tre formati; provenienza/hash verificati, query con liste attese complete; download mancante → suite reale incompleta, non PASS | V2-01 |
| T22 | `*suffisso` per campo e BOTH, AND/frasi, Unicode, limiti 256/257, ranking, filtri, snippet e versioni snapshot; regressioni T03–T09/T18 | V2-09 |
| T23 | Suggerimenti per suffisso in ordine originale, limite/deduplica e snapshot; digitazione senza ricerca, selezione e risposte obsolete nel desktop IT/EN; regressioni T12/T13 | V2-09 |
| T24 | Parole isolate e query AND: bigrammi, Jaccard, Levenshtein e spareggi; campi/BOTH, Unicode, codici esclusi, proposte parziali, frasi/wildcard escluse; build, sync e versioni snapshot, nessuna espansione della ricerca originale | V2-10 |
| T25 | Desktop IT/EN: proposta dopo ricerche con e senza risultati, accettazione esplicita e tastiera, query/filtri/snapshot obsoleti scartati, errori della correzione separati dai risultati; misure separate di latenza, build, riapertura e RAM | V2-10 |
| T26 | PDF sintetici con pagine vuote e immagini: mappa nel testo canonico, destinazioni per termini/AND/frasi/wildcard e campi, round-trip SQLite, sync, recovery e rebuild schema 3; regressioni CLI | V2-11 |
| T27 | Viewer PDF interno: salto effettivo, barra fissa e ricerca inferiore, campo pagina, zoom automatico/dimensione reale/pagina/larghezza e preset 50–400%, rotazione, evidenziazione opzionale, centratura di pagine miste e limiti del pan, ricerca manuale e disabilitazione senza testo, azioni file/cartella, ritorno ai risultati, IT/EN, tema, tastiera, errori Qt e file cambiato/assente; packaging e collaudo offline separati dai test sorgente | V2-11 |
| T28 | TXT/MD: prima destinazione per parola, frase, AND, wildcard e campi; proiezione Markdown su markup/entità/tabelle/duplicati, BOM/newline/Unicode, file cambiato, errori e limiti; nessuna lettura sorgente durante query | V2-12 |
| T29 | Reader Qt: caricamento incrementale, numeri di riga e a capo, ricerca manuale letterale/ciclica, focus/Escape, temi e accessibilità; regressioni PDF/CLI e collaudo offline distinti dai test sorgente | V2-12 |
| T30 | Desktop: estensioni isolate applicano formati senza ricerca intermedia, frasi/nomi file restano query, filtro solo prepara la home; riepilogo con reset accessibile, risultati obsoleti scartati e CLI invariata | Dopo V2-12 |
| T31 | TXT/MD: bozza, undo/redo, salvataggio esplicito con BOM/newline, limiti, conflitti e percorsi sicuri; uscita protetta, serializzazione con job e sync successivo | V2-13 |
| T32 | MD: anteprima offline, tabelle/codice/link/immagini, salto al match esatto o fallback dichiarato; ricerca manuale nelle due modalità, IT/EN, temi, tastiera e Narrator | V2-13 |
| T33 | Tutte le superfici e i dialoghi a 480×360, 640×480, 900×640, 1280×820 e 1920×1080; lingue/temi, resize continuo e DPI 100–200%; nessuna sovrapposizione o azione irraggiungibile, focus e Narrator nativi | V2-14 |
| T34 | F1 e Aiuto da onboarding, home, risultati, impostazioni e viewer; guida IT/EN offline, indice, scorrimento, Escape e focus ripristinato, query/bozza preservate, F5 ancora sync | V2-14 |

La revisione visiva dopo V2-13 estende T12/T13/T25/T27/T29/T32: controlli a icona e tooltip nei temi IT/EN, focus e nomi accessibili, barre dei reader alla dimensione minima, proposta ortografica cliccabile e attivabile da tastiera con filtri conservati. Le prove QML offscreen verificano comportamento e geometria; DPI e Narrator richiedono verifica Windows nativa separata.

## Gate finale

Collegare ogni risultato a revisione, artefatto, ambiente e comandi. Il pacchetto finale deve superare gli scenari applicabili, incluse le lacune M9-G01–G07: test sorgente, mock e ZIP v1 non sostituiscono Windows pulito/account standard distinto. [Matrice e limiti della release 0.2.0](V2_08_ACCEPTANCE.md#matrice-dei-gate).

Le regressioni lifecycle sono in `backend/tests/integration/test_v2_lifecycle.py`; controller/QML e probe verificano il desktop. Zero test raccolti non è una suite verde. Annotare skip, errori, scostamenti prestazionali e prove non eseguite.

## Regressioni Luma

T12/T13 includono onboarding senza snapshot, errore/cancel e retry, home dopo
attivazione, recupero automatico v2 e sync non bloccante. Verificare navigazione
home/risultati/Impostazioni con query preservata, filtri/reset di sessione,
apertura singola da clic/Invio senza richiesta dei dettagli, file mancante,
risposte obsolete, IT/EN, temi, asset e QML nel payload. Il rendering offscreen
verifica caricamento e binding; la resa dei font Windows richiede il plugin
nativo. Narrator e collaudo finale rimangono prove distinte.

## Regressione nome pubblico e percorsi neutri

- T12/T13: testi IT/EN senza etichette generazionali; onboarding anche con soli dati storici presenti, riapertura della nuova sessione.
- T14/T16: primo avvio, riapertura e pulizia nel percorso `LocalDocumentSearch/Data`; dati storici v1 e `LocalDocumentSearchV2` intatti. Rifiutare reparse point nella radice dati e negli antenati; mantenere lock e confini di cancellazione.
- T15: installer e collegamenti senza suffissi; blocco della vecchia installazione prima delle modifiche, anche silenzioso; disinstallazione conservativa e reinstallazione pulita; successivi aggiornamenti/reinstallazioni nel percorso registrato, downgrade bloccato.
- Revisione T15: provare percorso predefinito e personalizzato con spazi/Unicode, rifiuto di rete/rimovibili/junction/radice/dati, permessi e spazio; `/DIR` divergente in upgrade anche silenzioso; riepilogo IT/EN e navigazione indietro/avanti; retry ripetuto e controllo prima della copia; avvio finale selezionato/deselezionato e mai in silenzioso. In T14/T16 verificare che installazione e disinstallazione da cartella personalizzata lascino intatti dati storici e sorgenti; in T17 assenza di download; in T18 CLI invariata.
- Collaudo del pacchetto Windows distinto dai test sorgente: le evidenze della release pubblicata non coprono automaticamente questi cambiamenti.
