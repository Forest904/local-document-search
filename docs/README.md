# Documentazione e stato del progetto

Per installare e provare l’app parti dal [README](../README.md).

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

## Backlog installer

Proposte future, non approvate né implementate: firma digitale con timestamp; riepilogo della versione installata e di quella nuova; riparazione esplicita; messaggi diagnostici e accesso ai log; recupero da aggiornamento interrotto.

Richiedono una revisione dei requisiti: posizione configurabile degli indici, modalità portable, installazione per tutti gli utenti e aggiornamenti online. L'updater online resta escluso dal PRD attuale.
