# Documentazione e stato del progetto

Per installare e provare l’app parti dal [README](../README.md).

## Stato corrente — candidato 0.2.2

La [0.2.1 pubblicata](https://github.com/Forest904/local-document-search/releases/tag/v0.2.1) è la versione scaricabile. L'11 novembre 2026 l'utente ha confermato che l'installer scaricato da GitHub funziona correttamente sul PC di test; non ha comunicato hash, misure o risultati per singolo scenario. Il lavoro successivo prepara la **0.2.2 locale** con guida F1/Aiuto, layout da 480×360 pixel logici, audit di accessibilità e documentazione coerente. Build release pulita e verifica dell'installer superate; il benchmark compilato completa tre cicli ma **non supera T08** per no-change e query p95. DPI/Narrator nativi e collaudo del nuovo installer su account isolato restano pendenti. [Matrice di accettazione 0.2.2](V2_14_ACCEPTANCE.md). Nessuna prova della 0.2.1 attesta automaticamente il nuovo artefatto.

I paragrafi datati che seguono documentano la sequenza delle verifiche storiche: espressioni come «da pubblicare» e gate aperti si riferiscono al candidato di quella fase, non revocano la pubblicazione 0.2.1 né anticipano l'accettazione 0.2.2.

## Stato implementato

La release **0.2.0**, pubblicata il 9 novembre 2026, deriva dal candidato pulito `3b78203e6cfbb3be1b01d8bed82728c45b56ab00`: backend condiviso, CLI volatile senza Qt, ricerca con prefissi/ranking/filtri, SQLite v2 con cancel/recovery e desktop Luma Qt Quick con IT/EN e temi. Il desktop apre i file direttamente e mostra pagine da 20. [Codice e ownership](ARCHITECTURE.md).

V2-01–V2-08 sono concluse; nessuna ulteriore milestone è definita. Le evidenze riguardano revisioni e artefatti identificati, non automaticamente modifiche successive: [corpus V2-01](TEST_DATASETS.md#verifica-v2-01), [backend V2-02–05](PERFORMANCE.md), [audit installer V2-07](V2_07_INSTALLER.md), [accettazione finale e desktop V2-06/V2-08](V2_08_ACCEPTANCE.md). La matrice distingue suite, benchmark compilato e conferme manuali dell’utente; conserva anche lo scostamento p95 di un run interrotto.

## Riferimenti

| Ti serve capire… | Documento |
|---|---|
| Cosa deve fare il prodotto | [PRD](PRD.md) |
| Dove intervenire e come persistono i dati | [Architettura, dominio e snapshot](ARCHITECTURE.md) |
| Come chiamare il backend | [Contratti applicativi e porte](INTERFACE_CONTRACTS.md) |
| Come vengono letti e cercati i documenti | [Reader, analyzer e ricerca](INDEXING_AND_ANALYSIS.md) |
| Come si comporta il desktop | [UX Windows](UX_WINDOWS.md) |
| Quali dati conserva e come distribuirlo | [Privacy e diritti](SECURITY_AND_PRIVACY.md), [packaging](../scripts/package/README.md) |
| Perché sono state fatte certe scelte | [Decisioni approvate e aperte](adr/README.md) |
| Come verificare una modifica | [Strategia e scenari](TEST_STRATEGY.md), [corpus funzionale](TEST_DATASETS.md), [comandi esperimenti](../experiments/README.md) |

Requisiti e scenari mantengono ID stabili; misure ed esiti appartengono ai report. Le specifiche correnti sono autonome: l’[archivio v1](archive/v1/README.md) rimanda ai documenti storici a revisione Git fissa e riassume M9; non integra implicitamente le regole attuali.

## Continuità e limiti storici

La v2 riusa modello/analyzer/indici M0–M2, CLI/reader M3–M4 e snapshot/sync/job M5–M7; sostituisce Widgets M8 con Qt Quick e ZIP M9 con installer. Lo storage separato evita migrazioni implicite. Il corpus funzionale estende i generatori Homework/M9 e resta distinto dai benchmark.

M9 v1 rimane **parzialmente accettata**: le lacune G01–G07 sono state chiuse sul pacchetto v2, come registra la [matrice finale](V2_08_ACCEPTANCE.md#matrice-dei-gate), senza cambiare gli esiti v1. Misure storiche non sono automaticamente confrontabili; fault simulati non provano resistenza a ogni OOM o perdita di alimentazione. Il materiale [Homework 3](homework-3/README.md) conserva la regressione del corso e non prova l’invio amministrativo al docente.

## Modifiche successive alla release 0.2.0

La **0.2.1** raccoglie le modifiche sottostanti. L'utente ha riferito un collaudo positivo dal sorgente e tramite installer, e successivamente ha specificato che l'installer proviene da GitHub; hash del pacchetto provato non attestato. Build pulita, benchmark sul compilato e collaudo manuale restano evidenze distinte.

La [release **0.2.1**](https://github.com/Forest904/local-document-search/releases/tag/v0.2.1) è pubblicata dall'esatto commit `a799901766a5da35f0a133eef15bbb898bb0a6e1`: workflow Windows/Ubuntu verde, installer, checksum e manifest pubblico disponibili. SHA-256 dell'installer pubblicato `e9d253f6c269ab80243750902abe775014df414fbbdc5e70baa344b739ea5f6c`. Il binario GitHub differisce da quello della build locale; il benchmark locale non attesta l'asset pubblicato byte per byte. Il collaudo manuale riguarda un download GitHub ma non identifica l'hash del file provato.

L'11 novembre 2026 l'utente ha confermato un **PASS** del collaudo della nuova versione su PC Windows di test. Non è stato fornito l'hash dell'installer provato, quindi l'evidenza resta una conferma manuale della versione e non identifica byte per byte l'asset che produrrà GitHub Actions.

Verifica del candidato `165161847029f465983de169d289131e8f4d3b64`: suite **570 passed, 7 skipped**, runner Homework 3 **PASS**, build release pulita e audit del manifest superati. Installer SHA-256 `e6fc5386845904315b9eea54fc345d90d8fe222012ac03c7aa84df238b623d8e`. Benchmark del compilato su corpus sintetico target, tre cicli, 100 campioni e cinque warmup: **PASS** e sei budget rispettati; massimi build 160,092 s, riapertura 6,519 s, no-change 0,894 s, sync incrementale 4,103 s, query p95 72,266 ms, working set 1432,490 MB. [Report locale ignorato da Git](../experiments/README.md). Il collaudo install/update/uninstall del pacchetto finale su account Windows isolato non è attestato; la release resta da pubblicare.

### V2-09 — ricerca per suffisso

Milestone implementata e verificata sul sorgente locale: `*suffisso` e suggerimenti dinamici usano un vocabolario rovesciato immutabile per campo. L'API Python rinomina `allow_prefixes` in `allow_wildcards` senza alias; il desktop abilita entrambe le forme. Suite backend **394 passed, 6 skipped**, frontend/script **100 passed**, runner Homework verde; benchmark sintetico target su tre cicli **PASS** e probe Qt offscreen **PASS**. [ADR 0015](adr/0015-v2-suffix-wildcards.md), [report e limiti](V2_09_SUFFIX_SEARCH.md). Verifiche su working tree modificato, non su installer o nuova release; i risultati della release 0.2.0 e i benchmark V2-02 restano evidenze storiche separate.

Nome pubblico stabile senza etichetta generazionale, nuovi percorsi di installazione e dati, transizione tramite reinstallazione pulita: [ADR 0013](adr/0013-v2-distribution.md#revisione-approvata--10-novembre-2026). Queste modifiche non costituiscono una nuova release pubblicata; il collaudo del nuovo pacchetto Windows resta distinto dalle evidenze storiche V2-07/V2-08.

Verifiche locali del 10 novembre 2026 per il nome pubblico: suite backend e script **418 passed, 6 skipped**; dopo gli ultimi controlli aggiunti, suite desktop con compilazione sintetica/pulizia **54 passed**, suite dedicata packaging **6 passed** (esecuzioni sovrapposte, conteggi non sommabili). Coperti isolamento dei dati storici, primo avvio/riapertura/pulizia, junction negli antenati e confini della pulizia upgrade. Inno Setup compila lo script con payload sintetico; questo non ? un pacchetto applicativo distribuibile. Non eseguiti build completa n? collaudo install/update/uninstall su Windows pulito; blocco della vecchia installazione e nomi dei collegamenti richiedono ancora quel collaudo. Nessuna nuova release pubblicata.

La successiva revisione dell'installer aggiunge destinazione selezionabile alla prima installazione, riepilogo, retry con app aperta e avvio finale opzionale: [ADR 0013](adr/0013-v2-distribution.md#revisione-approvata--percorso-e-wizard). Queste modifiche non appartengono alla release pubblicata 0.2.0. I test dello script e il collaudo del pacchetto completo vanno registrati separatamente; il secondo resta pendente finché non viene provato su un account standard isolato.

Verifica locale della revisione: **44 test degli script**, **50 desktop** e **385 backend con 6 skip** verdi. Il test installer usa AppId e payload sintetici isolati e copre prima installazione Unicode, reinstallazione e rifiuto di `/DIR` divergente. La build completa locale ha prodotto un installer, ma non costituisce collaudo del pacchetto su sistema pulito né nuova release pubblicata.

### V2-10 — correzione ortografica proposta

Implementata sul sorgente locale: proposta separata dopo ogni ricerca desktop di parole esatte, tramite vocabolario dello snapshot, bigrammi/Jaccard e Levenshtein. Richiede selezione esplicita; CLI Homework e ricerca esatta conservano la loro semantica. [ADR 0016](adr/0016-v2-spelling-correction.md), [report e limiti](V2_10_SPELLING_CORRECTION.md). I risultati della release 0.2.0 non costituiscono evidenza di questa estensione.

Verifiche locali: backend **406 passed, 6 skipped**, desktop **59 passed** e runner Homework verde. Il benchmark sorgente target a tre cicli completa tutte le fasi, ma supera i budget di avvio (16,093/15 s), no-change (1,036/1 s) e query frase p95 (108,089/100 ms); il gate prestazionale V2-10 resta aperto. Build, sync incrementale e RAM sono entro budget. Nessun nuovo installer collaudato.

### V2-11 — Navigazione PDF alla pagina del match

Implementazione sul sorgente locale in verifica: mappa delle pagine nello snapshot desktop schema 3, destinazione nel risultato e viewer interno Qt Quick PDF. La rifinitura aggiunge ricerca manuale nel PDF, barre sovrapposte, navigazione pagina, zoom/pan contenuti con preset 50–400%, rotazione e apertura della cartella. Gli indici desktop precedenti richiedono rebuild esplicito. Suite backend **410 passed, 6 skipped**, desktop/script **114 passed, 1 test installer escluso** perché l'app è aperta nella sessione Windows; runner Homework verde. Il benchmark target a tre cicli precedente supera i budget di avvio, no-change e query p95: gate prestazionale aperto. La [specifica e le evidenze](V2_11_PDF_PAGE_NAVIGATION.md) distinguono test sorgente, benchmark e collaudo del pacchetto; nessuna nuova release pubblicata.

### V2-12 — Reader TXT e Markdown

Implementazione sul sorgente locale: reader Qt Quick in sola lettura, salto al primo match tramite posizione dello snapshot e provenienza Markdown calcolata all'apertura, ricerca manuale separata e limiti espliciti. Nessuna modifica dello schema SQLite o della CLI. Suite backend **433 passed, 6 skipped**; frontend/script **118 passed, 1 test installer escluso** perché l'app è aperta; runner Homework verde. [Decisione](adr/0018-v2-text-reader.md), [comportamento, evidenze e limiti](V2_12_TEXT_READER.md). Il collaudo del pacchetto resta distinto; nessuna nuova release pubblicata.

### V2-13 — Editor TXT/MD e anteprima Markdown

Implementazione nel sorgente locale: anteprima Markdown offline, editor del sorgente TXT/MD con salvataggio esplicito e protezione della bozza, controllo dei conflitti e sync successivo. Schema SQLite e CLI invariati. Suite backend **437 passed, 7 skipped**, frontend **86 passed**, runner Homework 3 verde. [Decisione](adr/0020-v2-text-editor.md), [comportamento, evidenze e limiti](V2_13_TEXT_EDITOR.md). Verifica nativa DPI/Narrator e collaudo dell'installer non attestati; nessuna nuova release pubblicata.

Revisione visiva successiva sul sorgente locale: icone editor/Markdown originali e uniformate, toolbar PDF/TXT/MD su due righe, Salva a icona nella toolbar e proposta ortografica compatta cliccabile con filtri conservati. Verifiche sulla revisione: frontend **87 passed**, backend **437 passed, 7 skipped**, script **46 passed**, runner Homework 3 **PASS** (10 query, 2 regressioni). Prove offscreen e test sorgente non attestano DPI/Narrator nativi, benchmark o collaudo del pacchetto; nessuna nuova release pubblicata.

## Backlog installer

### Filtri formato rapidi nel desktop — 11 novembre 2026

Implementati nel sorgente locale i token `.txt`, `.md` e `.pdf` nella barra desktop: selezionano i formati di sessione all'invio, vengono rimossi dalla query e, da soli, preparano il filtro nella home. Il riepilogo usa un'icona accessibile per il reset e non offre Impostazioni. [Decisione](adr/0019-desktop-format-query-filters.md), [comportamento](UX_WINDOWS.md). Verifiche: frontend **83 passed**, backend **433 passed, 6 skipped**, runner Homework 3 verde. Una prima esecuzione frontend in parallelo alla suite backend ha avuto un timeout nel test di paginazione; il test isolato e la suite frontend ripetuta in sequenza sono verdi. Verifica visiva su Windows nativo e collaudo dell'installer non eseguiti; nessuna nuova release pubblicata.

Proposte future, non approvate né implementate: firma digitale con timestamp; riepilogo della versione installata e di quella nuova; riparazione esplicita; messaggi diagnostici e accesso ai log; recupero da aggiornamento interrotto.

Richiedono una revisione dei requisiti: posizione configurabile degli indici, modalità portable, installazione per tutti gli utenti e aggiornamenti online. L'updater online resta escluso dal PRD attuale.
