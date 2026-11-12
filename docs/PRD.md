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
| V2-R15 | Installer offline per utente con wizard | Nessuna elevazione; Python, Qt, plugin e runtime necessari inclusi; prima installazione in cartella locale fissa selezionabile, aggiornamento completo nella cartella registrata; riepilogo, retry con app aperta e avvio finale opzionale | V2-07, V2-08 / T15 |
| V2-R16 | Disinstallazione e pulizia controllate | Dati conservati salvo scelta esplicita; sorgenti e dati v1 intatti; errore riprovabile | V2-07, V2-08 / T16 |
| V2-R17 | Privacy e distribuzione verificabili | Nessuna telemetria/upload; termini e inventario dipendenze verificati; avvisi della release non firmata documentati | V2-07, V2-08 / T17 |
| V2-R18 | Preservare CLI Homework e backend condiviso | Sintassi, ordine per percorso, output e codici esistenti; nessuna dipendenza Qt della CLI | V2-03, V2-05, V2-08 / T18 |
| V2-R19 | Corpus ibrido riproducibile per validazione funzionale | Sintetici TXT/MD/PDF deterministici; circa 12–30 documenti Internet indicizzabili con permessi espliciti, italiano/inglese e almeno un file reale per formato; ground truth completa e versionata; suite reale opt-in valida solo con corpus completo | V2-01 / T20, T21 |
| V2-R28 | Aprire i PDF alla pagina del primo match | Mappa delle pagine persistita con lo snapshot; viewer interno naviga alla pagina del primo match nel contenuto, o alla prima se il match è solo nel nome; ritorno ai risultati ed errori gestibili | V2-11 / T26, T27 |
| V2-R24 | Leggere TXT/MD nel viewer interno | Sorgente in sola lettura, salto esatto al primo match quando il file corrisponde allo snapshot, ricerca manuale indipendente, limiti ed errori gestibili; CLI invariata | V2-12 / T28, T29 |
| V2-R25 | Filtri formato rapidi nel desktop | `.txt`, `.md` e `.pdf` isolati nella barra sostituiscono i formati di sessione all'invio; filtro solo senza ricerca; riepilogo con reset a icona accessibile e Impostazioni dalla home | Dopo V2-12 / T30 |
| V2-R26 | Modifica esplicita TXT/MD | Editor del sorgente dei risultati, bozza protetta, salvataggio atomico con conflitti e sincronizzazione successiva; CLI invariata | V2-13 / T31 |
| V2-R27 | Anteprima Markdown | Lettura formattata offline con salto esatto quando la provenienza è rappresentabile; sorgente disponibile come fallback | V2-13 / T32 |
| V2-R29 | Layout e accessibilità desktop adattivi | Tutte le schermate e i dialoghi utilizzabili da 480×360 pixel logici, con ridimensionamento continuo, DPI 100–200%, tastiera e Narrator; controlli e contenuti raggiungibili | V2-14 / T33 |
| V2-R30 | Guida locale alle funzionalità | F1 e Aiuto aprono la guida IT/EN offline da ogni schermata; F5 mantiene il sync; la guida non altera navigazione, query o bozza | V2-14 / T34 |

## Limiti e non-obiettivi

**Estensione V2-11:** il desktop apre i PDF in un viewer interno alla pagina fisica del primo match nel testo indicizzato; i risultati che corrispondono solo nel nome partono dalla prima pagina. La navigazione usa una mappa delle pagine salvata nello snapshot. La ricerca manuale nel PDF usa il testo presente nel file aperto e non altera lo snapshot. Non sono promessi scorrimento o evidenziazione automatica alla parola della query Luma, né corrispondenza con un sorgente modificato dopo l'indicizzazione. [Decisione](adr/0017-v2-pdf-page-navigation.md).

Il viewer presenta una barra fissa con navigazione per pagina, zoom automatico, dimensione reale, adattamento alla pagina o larghezza e percentuali predefinite dal 50% al 400%, rotazione visiva e azioni sul file. La barra di ricerca inferiore compare su Ctrl+F; l'utente può scegliere se evidenziare tutte le occorrenze manuali. Pagine che entrano nel viewport restano centrate senza scorrimento laterale.

Restano esclusi OCR, AI/ricerca semantica, watcher continuo, più directory attive, OR/NOT, fuzzy, servizi cloud, updater online e motori IR esterni. Ricerca e reader non modificano i documenti originali; V2-13 consente soltanto il salvataggio esplicito di TXT/MD aperti dai risultati, secondo [ADR 0020](adr/0020-v2-text-editor.md). Il viewer V2-11 rende le pagine PDF; non promette coordinate della query né conservazione del layout originale nel testo estratto.

Il diff resta basato su path, size e mtime_ns. Modifiche che preservano dimensione e timestamp possono non essere rilevate, anche con i nuovi controlli in ingestione. I risultati possono diventare obsoleti fino al sync. PDF multicolonna e tabelle possono produrre testo imperfetto; le frasi operano sul testo canonico unico.

Il [corpus funzionale](TEST_DATASETS.md) resta distinto dal benchmark prestazionale.

Il target di scala non è un limite automatico ai file né una garanzia su qualunque PDF o hardware. Soglie e profilo supportato sono fissati nell’[ADR 0014](adr/0014-v2-performance-budgets.md); risorse esaurite devono produrre errori gestibili quando intercettabili. Non si promette recupero da ogni OOM o perdita fisica di alimentazione.

La revisione V2-D01 del 12 novembre 2026 fissa p95 ≤100 ms per query esatte, wildcard ordinarie e suggerimenti, p95 ≤200 ms per `frasecom*` nel contenuto e no-change ≤2 s. Gli altri budget restano invariati; il confronto fra compilati documenta anche eventuali rallentamenti non spiegati, che possono essere accettati entro tali soglie.

## Condizione di rilascio

La release pubblica richiede V2-08, incluse le lacune M9 trasferite nella [stato del progetto](README.md#stato-implementato), e i [gate di distribuzione](SECURITY_AND_PRIVACY.md#distribuzione-e-diritti). Approvazione del progetto, test del sorgente e collaudo del pacchetto sono evidenze differenti.

## Nome pubblico stabile (10 novembre 2026)

Il prodotto si presenta come Local Document Search senza suffissi generazionali; i numeri tecnici di release restano disponibili. V2-R14/R16 preservano sia i dati v1 sia quelli della precedente installazione in `LocalDocumentSearchV2`. Nuovi dati in `LocalDocumentSearch/Data`; installazione predefinita in `Programs/LocalDocumentSearch` sotto `%LOCALAPPDATA%`, con scelta di una diversa cartella locale fissa solo alla prima installazione. Passaggio dalla precedente installazione tramite disinstallazione conservativa e nuovo avvio, senza migrazione; V2-R15 mantiene gli aggiornamenti successivi nel percorso registrato.

## Estensione V2-09 — suffissi espliciti

La ricerca supporta anche `*suffisso` con opzione wildcard esplicita e suggerimenti di termini che terminano nel frammento digitato. Sono ammessi solo `prefisso*` e `*suffisso` fuori dalle frasi. Restano invariati ricerca esatta, AND/frasi nello stesso campo, CLI Homework e trattamento della punteggiatura con wildcard disabilitate. Per ogni campo lo snapshot deriva un vocabolario ordinato rovesciato, senza nuovi posting o schema SQLite. [Decisione](adr/0015-v2-suffix-wildcards.md), [scenari T22/T23](TEST_STRATEGY.md#scenari-di-accettazione).

| ID | Requisito V2-09 | Accettazione |
|---|---|---|
| V2-R20 | Ricerca esplicita per suffisso | `*termine` restituisce match completi nello stesso campo, con limiti e ranking coerenti; T22 |
| V2-R21 | Suggerimenti per suffisso | Termini dello snapshot in ordine originale; il desktop sostituisce la clausola senza avviare query durante digitazione; T23 |

La navigazione PDF, etichettata `V2-R20` nella tabella principale prima della correzione documentale 0.2.2, è `V2-R28`. `V2-R20` resta l'ID della ricerca per suffisso; nessun comportamento o contratto cambia per questa rinumerazione.

## Estensione V2-10 — correzione ortografica proposta

V2-10 fa eccezione al limite generale che esclude il fuzzy: aggiunge una **proposta separata**, senza espandere la ricerca esatta. Dopo ogni ricerca desktop, una query di parole esatte può mostrare «Intendevi…?», anche se esistono risultati. L'utente decide se eseguire la proposta. Frasi, wildcard, CLI Homework, documenti e sorgenti restano invariati. [Decisione](adr/0016-v2-spelling-correction.md), [scenari T24/T25](TEST_STRATEGY.md#scenari-di-accettazione).

| ID | Requisito V2-10 | Accettazione |
|---|---|---|
| V2-R22 | Proposta ortografica separata | Candidati dal vocabolario dello snapshot, bigrammi/Jaccard/Levenshtein, una query proposta con correzioni anche parziali; T24 |
| V2-R23 | Scelta esplicita nel desktop | Proposta IT/EN dopo ogni ricerca, risultati originali intatti, selezione da tastiera, scarto di risposte obsolete; T25 |
