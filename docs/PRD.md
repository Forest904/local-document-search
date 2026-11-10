# PRD — Local Document Search v2

Approvato il 7 novembre 2026. [Stato implementato e release](README.md#stato-implementato), [decisioni tecniche](adr/README.md).

## Prodotto e utenti

Ricerca locale per utenti Windows non tecnici: installare offline senza Python → scegliere una cartella → indicizzare → cercare → leggere estratti → aprire il file. Agli avvii successivi recuperare l’indice e sincronizzare in background. Attese, errori e recupero devono essere comprensibili senza conoscenze tecniche.

La v2 evolve il backend esistente, preservando CLI Homework e regressioni. Uso personale, di studio e interno gratuito, anche professionale; [termini e distribuzione](SECURITY_AND_PRIVACY.md#distribuzione-e-diritti).

## Requisiti e accettazione

Gli ID sono stabili. Txx identifica gli scenari della [strategia di test](TEST_STRATEGY.md); V2-xx le milestone concluse, con evidenze nella [stato del progetto](README.md#stato-implementato).

| ID | Requisito approvato | Accettazione | Milestone / scenario |
|---|---|---|---|
| V2-R01 | Windows 11 x64, esecuzione locale e offline | Installazione e flussi completi senza rete, Python o strumenti di sviluppo | V2-07, V2-08 / T01 |
| V2-R02 | Una directory ricorsiva attiva; TXT, MD e PDF testuali | Nessun attraversamento symlink/junction; un file = un documento; esclusioni distinte dagli errori | V2-04, V2-08 / T02 |
| V2-R03 | Due indici posizionali proprietari e analyzer coerenti | AND e frasi soddisfatti interamente nello stesso campo, anche in BOTH | V2-03 / T03 |
| V2-R04 | Indice secondario ordinato sul vocabolario | Coerenza con entrambi i campi e snapshot; confronto misurato della struttura scelta | V2-03 / T04 |
| V2-R05 | Prefissi espliciti e suggerimenti durante digitazione | Suggerimenti separati dalla query, riferiti allo snapshot; nessuna espansione implicita della ricerca esatta | V2-03, V2-05, V2-06 / T05 |
| V2-R06 | Filtri per formato e cartella; rilevanza e percorso | Filtri coerenti con totale/pagine; ranking dei soli match, deterministico con spareggio stabile | V2-05 / T06 |
| V2-R07 | Snippet ed evidenziazione nei risultati | Testo e corrispondenze della versione richiesta, senza rilettura dei sorgenti | V2-05, V2-06 / T07 |
| V2-R08 | Target 10.000 file / 300 MB di testo estratto | Budget approvati su corpus e hardware definiti per p95 query, avvio, build, sync e RAM; verifica sul pacchetto | V2-02, V2-03, V2-04, V2-08 / T08 |
| V2-R09 | Snapshot immutabili, commit atomico e single-writer | Ricerca sul precedente della stessa cartella; nessun candidato parziale dopo errore o recovery | V2-04, V2-08 / T09 |
| V2-R10 | Annullamento cooperativo prima del commit | Esito annullato distinto da errore, vecchio snapshot preservato; richiesta tardiva rifiutata esplicitamente | V2-04, V2-06 / T10 |
| V2-R11 | Rilevare variazioni dei metadati durante ingestione | Variazione rilevata interrompe il candidato e offre retry; nessun hash o controllo dei sorgenti durante query | V2-04 / T11 |
| V2-R12 | Desktop Qt Quick/QML minimale e professionale | Ingresso guidato, home Luma, lista ad apertura diretta e Impostazioni separate; Invio esegue, rilevanza predefinita; UI utilizzabile sotto carico | V2-06 / T12 |
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

Il [corpus funzionale](TEST_DATASETS.md) resta distinto dal benchmark prestazionale.

Il target di scala non è un limite automatico ai file né una garanzia su qualunque PDF o hardware. Soglie e profilo supportato sono fissati nell’[ADR 0014](adr/0014-v2-performance-budgets.md); risorse esaurite devono produrre errori gestibili quando intercettabili. Non si promette recupero da ogni OOM o perdita fisica di alimentazione.

## Condizione di rilascio

La release pubblica richiede V2-08, incluse le lacune M9 trasferite nella [stato del progetto](README.md#stato-implementato), e i [gate di distribuzione](SECURITY_AND_PRIVACY.md#distribuzione-e-diritti). Approvazione del progetto, test del sorgente e collaudo del pacchetto sono evidenze differenti.

## Nome pubblico stabile (10 novembre 2026)

Il prodotto si presenta come Local Document Search senza suffissi generazionali; i numeri tecnici di release restano disponibili. V2-R14/R16 preservano sia i dati v1 sia quelli della precedente installazione in `LocalDocumentSearchV2`. Nuovi dati in `LocalDocumentSearch/Data`, installazione in `Programs/LocalDocumentSearch` sotto `%LOCALAPPDATA%`. Passaggio tramite disinstallazione conservativa e nuovo avvio, senza migrazione; V2-R15 mantiene gli aggiornamenti successivi nel percorso neutro.
