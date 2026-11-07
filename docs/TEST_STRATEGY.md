# Strategia di verifica v2

Una specifica approvata non equivale a codice funzionante. Conservare test v1 e CLI Homework come regressione; estenderli con il [corpus ibrido funzionale](TEST_DATASETS.md), usando report legati a revisione e artefatto. [Evidenze storiche](archive/v1/README.md), [lacune M9](BASELINE.md). I casi qui sono scenari da eseguire nelle milestone, non risultati già ottenuti.

## Validazione funzionale V2-01

T20 è automatizzato in `backend/tests/integration/test_v2_corpus.py`: verifica generazione ripetuta, hash dei sintetici e liste complete. T21 è verificato localmente con i 12 reali completi e le 36 query della ground truth, ricontrollate sui testi estratti prima del confronto col motore. La suite reale resta opt-in. Un file reale mancante, alterato o una ground truth assente non è un PASS. [Evidenze e limiti della chiusura V2-01](ROADMAP.md#v2-01--corpus-ibrido-e-validazione-funzionale).

La suite ordinaria usa i sintetici deterministici offline. La suite reale è opt-in e richiede tutti i documenti del manifest verificati tramite hash; se uno è stato saltato o non disponibile, segnala corpus incompleto e non passa. Confronta le liste complete di percorsi attesi per query e campo, comprese frasi e casi senza match. La ground truth viene preparata dopo acquisizione e associata alla versione dei documenti; [provenienza, metodo e limiti](TEST_DATASETS.md). Nessun tempo misurato in questo corpus costituisce un obiettivo di prestazione.

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
non valgono come PASS. I budget T08 sono approvati in V2-D01:
massimo query p95 ≤100 ms, avvio fino alla ricerca ≤15 s, build ≤300 s,
sync incrementale 100/100/100 ≤60 s, no-change ≤1 s e picco working set
≤2560 MiB. Si applica il massimo dei tre cicli e, per le query, il massimo
dei p95 di tutti i casi. [Metodo ed evidenze](V2_02_BENCHMARK.md); la prova
sul pacchetto finale resta V2-08.

Unit test per dominio, contratti per reader/storage, integrazione per sync/concorrenza, E2E per CLI e desktop, collaudo sul pacchetto installato. La suite deve raccogliere test effettivi. Benchmark separati per lookup, intersezione, ranking, serializzazione, caricamento e UI; corpus, seed, hardware, OS, cache, revisioni e distribuzioni delle durate registrati. I budget V2-02 sono fissati sopra prima delle ottimizzazioni. Il target è 10.000 file e 300 MB di testo estratto; includere anche corpus piccolo e casi avversi. Non confrontare tempi M9 con condizioni diverse.

## Scenari di accettazione

| ID | Scenario e risultato atteso | Milestone |
|---|---|---|
| T01 | Installer e flussi completi offline su Windows 11 x64 pulito, account standard, senza Python/tool di sviluppo | V2-07, V2-08 |
| T02 | TXT/MD/PDF testuali, PDF protetto/vuoto/misto e TXT/MD vuoti; symlink/junction esclusi; errori distinti dalle esclusioni | V2-04, V2-08 |
| T03 | AND, frasi, termini ripetuti e BOTH nello stesso campo; match identici a v1 per query esatte | V2-03 |
| T04 | Vocabolari ordinati coerenti dopo build, update, restart e recovery; confronto strutture e costi documentato | V2-03, V2-04 |
| T05 | Prefisso esplicito e suggerimenti corretti per campo/versione; digitazione non avvia query; limiti approvati. Backend V2-03 coperto da `test_v2_retrieval.py`; integrazione digitazione UI in V2-06 | V2-03, V2-05, V2-06 |
| T06 | Filtri e ranking su soli match, totale/pagina coerenti; ordine deterministico e alternativa per percorso | V2-05 |
| T07 | Snippet e highlight Unicode/frasi nella versione del risultato; anteprima sotto carico e versione rimossa gestita | V2-05, V2-06, V2-08 |
| T08 | Budget approvati su 10.000/300 MB per p95 query, avvio, build, sync, RAM; metodologia e limiti registrati | V2-02, V2-03, V2-04, V2-08 |
| T09 | Add/modify/remove, no-change, A→B→A, rebuild, fault commit, recovery; mai snapshot parziale o directory errata | V2-04, V2-08 |
| T10 | Cancel durante estrazione/build conserva N e produce CANCELLED; cancel al commit rifiutato; pulizia durante job rifiutata | V2-04, V2-06, V2-08 |
| T11 | Sorgente modificato durante lettura con metadati diversi: fallimento/retry; size+mtime identici resta limite dichiarato | V2-04 |
| T12 | UI usabile durante build, ricerca e anteprima; query/filtri/directory obsolete non sovrascrivono stato corrente | V2-06, V2-08 |
| T13 | Italiano/inglese, temi persistenti, tastiera, focus, contrasto, DPI e Narrator su flussi principali | V2-06, V2-08 |
| T14 | Prima selezione v2 e upgrade v2 senza leggere, alterare o cancellare dati v1 | V2-04, V2-07 |
| T15 | Wizard install/update/uninstall completo senza rete o elevazione, runtime Qt/Python inclusi e avvio riuscito | V2-07, V2-08 |
| T16 | Disinstallazione conserva dati per default; cancellazione solo esplicita, rifiuto durante job, sorgenti/v1 intatti | V2-07, V2-08 |
| T17 | Nessuna connessione richiesta, inventario dipendenze e obblighi Qt verificati; termini approvati; avvisi release non firmata registrati | V2-07, V2-08 |
| T18 | Runner Homework e CLI: sintassi, ordine, codici e installazione backend senza Qt invariati | V2-03, V2-05, V2-08 |
| T19 | CI della revisione finale, manifest/hash del pacchetto e risultati legati alla stessa revisione pulita | V2-08 |
| T20 | Sintetici TXT/MD/PDF riproducibili: analyzer, campi, AND, frasi, Unicode e edge case confrontati con ground truth indipendente dal motore | V2-01 |
| T21 | 12–30 file reali autorizzati, IT/EN e tre formati; provenienza/hash verificati, query con liste attese complete; download mancante → suite reale incompleta, non PASS | V2-01 |

## Gate finale

Le [lacune M9-G01…G07](BASELINE.md) richiedono prove sul pacchetto v2 finale. Test del sorgente, mock e collaudo dello ZIP v1 non sostituiscono questa prova. V2-08 è chiusa solo se tutti i requisiti applicabili hanno esiti registrati; un limite accettato rimane documentato. Durante la sola riscrittura documentale non si rieseguono suite o benchmark applicativi.
