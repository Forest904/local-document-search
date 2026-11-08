# PRD — Local Document Search v2

**Stato: approvato per v2 il 7 novembre 2026; implementazione parziale.** V2-01, V2-02, il retrieval V2-03 e storage/lifecycle V2-04 sono chiusi localmente; il collaudo del pacchetto resta V2-08. Il prodotto iniziale è descritto nella [baseline](BASELINE.md). Questo documento è la fonte dei requisiti; le scelte tecniche ancora aperte sono nel [registro decisioni](OPEN_DECISIONS.md).

## Prodotto e utenti

V1 soddisfa l'Homework e offre un desktop per interagirvi. V2 evolve lo stesso prodotto, gli stessi package e il backend già implementato: aggiunge capacità di ricerca, rinnova la presentazione e completa la distribuzione. La [mappa M0–M9 → v2](BASELINE.md#continuità-da-m0m9-a-v2) mostra cosa viene riutilizzato; V2-01 parte dai generatori e dalle verifiche già presenti per costruire il corpus ibrido funzionale. V2 deve permettere a utenti Windows non tecnici di installare e usare un prodotto completo senza Python preinstallato, servizi remoti o configurazione di sviluppo. La distribuzione pubblica è destinata all'uso personale e di studio; uso professionale soggetto ad autorizzazione.

Il percorso principale è: installare offline → scegliere una cartella → indicizzare → cercare → leggere il contesto → aprire il file. Le aperture successive recuperano l'indice e sincronizzano in background. La UI espone attese, errori e recupero senza richiedere conoscenze tecniche.

## Requisiti e accettazione

Gli ID sono stabili. I riferimenti Txx sono scenari della [strategia di test](TEST_STRATEGY.md); le milestone sono nella [roadmap](ROADMAP.md).

| ID | Requisito approvato | Accettazione | Milestone / scenario |
|---|---|---|---|
| V2-R01 | Windows 11 x64, esecuzione locale e offline | Installazione e flussi completi senza rete, Python o strumenti di sviluppo | V2-07, V2-08 / T01 |
| V2-R02 | Una directory ricorsiva attiva; TXT, MD e PDF testuali | Nessun attraversamento symlink/junction; un file = un documento; esclusioni distinte dagli errori | V2-04, V2-08 / T02 |
| V2-R03 | Due indici posizionali proprietari e analyzer coerenti | AND e frasi soddisfatti interamente nello stesso campo, anche in BOTH | V2-03 / T03 |
| V2-R04 | Indice secondario ordinato sul vocabolario | Coerenza con entrambi i campi e snapshot; confronto misurato della struttura scelta | V2-03 / T04 |
| V2-R05 | Prefissi espliciti e suggerimenti durante digitazione | Suggerimenti separati dalla query, riferiti allo snapshot; nessuna espansione implicita della ricerca esatta | V2-03, V2-05, V2-06 / T05 |
| V2-R06 | Filtri per formato e cartella; rilevanza e percorso | Filtri coerenti con totale/pagine; ranking dei soli match, deterministico con spareggio stabile | V2-05 / T06 |
| V2-R07 | Snippet ed evidenziazione nei risultati e nell'anteprima | Testo e corrispondenze della versione richiesta, senza rilettura dei sorgenti | V2-05, V2-06 / T07 |
| V2-R08 | Target 10.000 file / 300 MB di testo estratto | Budget approvati su corpus e hardware definiti per p95 query, avvio, build, sync e RAM; verifica sul pacchetto | V2-02, V2-03, V2-04, V2-08 / T08 |
| V2-R09 | Snapshot immutabili, commit atomico e single-writer | Ricerca sul precedente della stessa cartella; nessun candidato parziale dopo errore o recovery | V2-04, V2-08 / T09 |
| V2-R10 | Annullamento cooperativo prima del commit | Esito annullato distinto da errore, vecchio snapshot preservato; richiesta tardiva rifiutata esplicitamente | V2-04, V2-06 / T10 |
| V2-R11 | Rilevare variazioni dei metadati durante ingestione | Variazione rilevata interrompe il candidato e offre retry; nessun hash o controllo dei sorgenti durante query | V2-04 / T11 |
| V2-R12 | Desktop Qt Quick/QML minimale e professionale | Sidebar, ricerca centrale, risultati e anteprima; Invio esegue, rilevanza predefinita; UI utilizzabile sotto carico | V2-06 / T12 |
| V2-R13 | Italiano/inglese, temi e accessibilità | Preferenze persistenti, tastiera completa, focus e contrasto, DPI e Narrator sui flussi principali | V2-06 / T13 |
| V2-R14 | Storage v2 separato, nessuna migrazione automatica | Nuova selezione cartella; v1 non letta, modificata o rimossa dalla gestione dati v2 | V2-04, V2-07 / T14 |
| V2-R15 | Installer offline per utente con wizard | Nessuna elevazione; Python, Qt, plugin e runtime necessari inclusi; aggiornamento da installer completo | V2-07, V2-08 / T15 |
| V2-R16 | Disinstallazione e pulizia controllate | Dati conservati salvo scelta esplicita; sorgenti e dati v1 intatti; errore riprovabile | V2-07, V2-08 / T16 |
| V2-R17 | Privacy e distribuzione verificabili | Nessuna telemetria/upload; termini e inventario dipendenze verificati; avvisi della release non firmata documentati | V2-07, V2-08 / T17 |
| V2-R18 | Preservare CLI Homework e backend condiviso | Sintassi, ordine per percorso, output e codici esistenti; nessuna dipendenza Qt della CLI | V2-03, V2-05, V2-08 / T18 |
| V2-R19 | Corpus ibrido riproducibile per validazione funzionale | Sintetici TXT/MD/PDF deterministici; circa 12–30 documenti Internet indicizzabili con permessi espliciti, italiano/inglese e almeno un file reale per formato; ground truth completa e versionata; suite reale opt-in valida solo con corpus completo | V2-01 / T20, T21 |

## Limiti e non-obiettivi

Restano esclusi OCR, AI/ricerca semantica, watcher continuo, più directory attive, OR/NOT, fuzzy, servizi cloud, updater online e motori IR esterni. I documenti originali non vengono modificati. Nessuna promessa di rendering PDF, coordinate di pagina o conservazione del layout originale nelle anteprime.

Il diff resta basato su path, size e mtime_ns. Modifiche che preservano dimensione e timestamp possono non essere rilevate, anche con i nuovi controlli in ingestione. I risultati possono diventare obsoleti fino al sync. PDF multicolonna e tabelle possono produrre testo imperfetto; le frasi operano sul testo canonico unico.

Il [corpus funzionale](TEST_DATASETS.md) non è un benchmark; fonti concrete e dettagli di acquisizione restano gate V2-01.

Il target di scala non è un limite automatico ai file né una garanzia su qualunque PDF o hardware. Soglie e profilo supportato devono essere approvati in V2-02; risorse esaurite devono produrre errori gestibili quando intercettabili. Non si promette recupero da ogni OOM o perdita fisica di alimentazione.

## Condizione di rilascio

La release pubblica richiede V2-08, incluse le lacune M9 trasferite nella [baseline](BASELINE.md), e i [gate di distribuzione](SECURITY_AND_PRIVACY.md#distribuzione-e-diritti). Approvazione del progetto, test del sorgente e collaudo del pacchetto sono evidenze differenti. La sola riscrittura documentale non soddisfa nessuna milestone di implementazione.
