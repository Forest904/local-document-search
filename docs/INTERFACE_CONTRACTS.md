# Contratti applicativi e porte

API Python in-process condivisa da UI e CLI; nessun HTTP/IPC. I DTO immutabili copiano le collezioni ricevute. Tipi e firme: [contracts.py](../backend/src/local_document_search/application/contracts.py); la [CLI](../backend/README.md#sessione-console) mantiene sintassi, ordine e codici indipendenti dal desktop.

## Build e lifecycle

| Caso d’uso | Risposta e regole |
|---|---|
| `BuildIndex.execute(root_directory)` | Build completo sincrono su radice assoluta validata. `BuildResult`: snapshot_id, discovered/indexed/excluded, processed_bytes, elapsed monotono e report. Errori sollevati, non successi parziali. CLI: una directory, repository volatile, niente diff. |
| `InitializeApplication.execute()` | Ripristino e, quando possibile, avvio sync senza attenderlo. `ApplicationState`: active_directory/id snapshot opzionali, search_available, warning, last_sync_outcome, job. |
| `SelectDirectory.execute(path)` | Valida/salva la radice e avvia sync; restituisce ApplicationState. Rifiuta job attivo; mai risultati di un’altra directory. |
| `GetIndexStatus.execute()` | Stato aggiornato della sessione, senza avviare lavoro. |
| `RequestSynchronization.execute(trigger="manual")` | `JobRef(job_id, status, reused)`; trigger manual/startup/select, sovrapposizioni riusano lo stesso job. |
| `RunSynchronization.execute(trigger="manual")` | Attende lo stesso job; `SyncResult` con snapshot_id, changed, added/modified/removed/unchanged/excluded/failed, elapsed, processed_bytes e report; errori propagati, cancel → CancelledResult. |
| `ClearLocalData.execute()` | A job fermo pulisce e restituisce ApplicationState senza directory; barriera alle nuove letture, attesa delle esistenti. |

Composizione persistente v2: `compose_v2_application`; quella v1 rimane per regressione. [Persistenza, identità, retention e recovery](ARCHITECTURE.md#snapshot-e-sincronizzazione).

## Operazioni di ricerca

| Operazione logica | Input | Output e invarianti |
|---|---|---|
| Ricerca | Query, campo `filename/content/both`, filtri formato/cartella opzionali, ordine rilevanza/percorso, opzioni esplicite per prefissi, pagina | `snapshot_id`, risultati della pagina e totale del medesimo insieme filtrato; ogni risultato porta documento, percorso, formato, campi corrispondenti e dati per snippet/evidenziazione |
| Suggerimenti | Testo parziale, campo, limite e contesto di snapshot corrente | Termini del vocabolario ordinato dello snapshot; nessuna esecuzione implicita della query o lettura dei sorgenti |
| Dettagli/anteprima | `document_id`, `snapshot_id`, query/contesto di evidenziazione | Metadati e testo estratto della stessa versione, con intervalli evidenziati coerenti; versione rimossa → SnapshotUnavailable |

Default `SearchRequest`: field=BOTH, limit=50, offset=0, order=PATH, allow_prefixes=False. Limit intero positivo e offset intero non negativo; altrimenti `InvalidInput`. Risposte senza match o offset oltre il totale sono valide: pagina vuota, totale reale e snapshot_id interrogato. `matched_fields` contiene solo FILENAME/CONTENT, mai BOTH.

La ricerca segue [semantica e ranking](INDEXING_AND_ANALYSIS.md): filtri e ordine precedono la paginazione, `total_matches` descrive l?insieme filtrato. Il desktop richiede RELEVANCE esplicitamente; il default API/CLI resta PATH.

**Prefissi e suggerimenti:** `SearchRequest.allow_prefixes` è `False` per default e abilita `termine*` fuori dalle frasi. Un prefisso deve produrre un solo token per ciascun campo selezionato, lungo almeno due caratteri normalizzati; oltre 256 espansioni per prefisso/campo la ricerca restituisce `InvalidInput` senza risultati parziali. `SuggestTerms` usa `SuggestRequest(text, field=BOTH, limit=10, snapshot_id=None)` e restituisce `SuggestResponse(snapshot_id, terms)`: termini normalizzati in ordine lessicografico, deduplicati in BOTH, massimo 50. Testo vuoto o di un carattere restituisce zero termini; token multipli o sintassi di query sono invalidi. Lo snapshot richiesto non disponibile dà `SnapshotUnavailable`. Nessuna digitazione avvia una ricerca.

**Filtri e risultati:** `SearchRequest` accetta `formats` (insieme non vuoto di `DocumentFormat`, OR), `folder` (cartella relativa ricorsiva con separatori `/`; niente segmenti vuoti, `.`/`..`, backslash, due punti o NUL; confine per segmento), `order` (`PATH` o `RELEVANCE`) e `snapshot_id` opzionali. `SearchResult` contiene `snippet` e `filename_highlights`; `GetDocument` accetta query/campo/prefissi opzionali e restituisce `filename_highlights` e `content_highlights`. Gli intervalli `[start, end)` sono punti di codice Python sul testo restituito; nello snippet sono relativi alla finestra, la cui posizione nel testo completo è `start`. La finestra ha massimo 240 caratteri e indicatori di troncamento. Formato, cartella, ordine e snapshot non validi danno `InvalidInput`; una versione non disponibile dà `SnapshotUnavailable`.

Una pagina successiva deve appartenere a una sola versione. Se lo snapshot è cambiato, il desktop scarta la risposta e riparte dalla prima pagina con query/filtri/ordine attuali; risultati obsoleti dopo cambio directory o query non vengono mostrati. Il testo persistito sostiene snippet e anteprima; niente accesso al file sorgente durante la ricerca. Nessuna API promette rendering o coordinate PDF.

## Job, stato e chiusura

`InvalidInput`: input, ID job o operazione non ammessi; `SnapshotUnavailable`: versione/documento assente, incompatibile o non acquisibile; `SourceUnavailable`: radice assente/inaccessibile; `ExtractionFailure`: lettura/encoding/estrazione; `StorageFailure`: accesso, lock, validazione o pubblicazione dati; `ResourceFailure`: memoria/spazio insufficienti intercettati. Errori prima del commit preservano l’attivo. I valori di dominio invalidi sollevano `ValueError`, tradotto dal caso d’uso quando deriva dall’input pubblico. CANCELLED non è un errore di lettura o storage. Il punto oltre il quale cancel è rifiutato è lo stato di commit non interrompibile, osservabile nel job.

**Annullamento e recupero:** `CancelSynchronization.execute(job_id)` restituisce `ACCEPTED`, `COMMIT_STARTED` o `FINISHED`; un ID sconosciuto dà `InvalidInput`. Il job annullato termina in `CANCELLED`, l'attesa bloccante restituisce `CancelledResult(job_id)` e l'ultimo controllo registra `cancelled`. `RebuildIndex.execute()` avvia un job esplicito; `RecoverPreviousSnapshot.execute()` riattiva il precedente valido solo quando non c'è un job.

`JobStatus` è immutabile, consultabile per tutta la sessione: PENDING/RUNNING/COMPLETED/FAILED/CANCELLED; fasi SCANNING, EXTRACTING, ANALYZING, BUILDING, COMMITTING. ID sconosciuto → InvalidInput. Totali ignoti in scansione; poi file/byte dei soli aggiunti/modificati da lavorare (tutti nel rebuild), incluse esclusioni completate, non rimozioni/invariati. `current_file` relativo. Progresso None per byte ignoti/zero, altrimenti massimo 0,99 finché non riesce; COMPLETED=1 anche per NO_CHANGES/solo rimozioni. Nessuna ETA.

`JobReport` conserva diagnostiche di categoria/fase/percorso relativo/motivo controllato, conteggi, `complete` e `published_snapshot_id`. Errori/cancel danno complete=False; le esclusioni del manifest finale compaiono anche in NO_CHANGES. Un errore nel salvare LastCheck **dopo** commit può dare FAILED senza annullare lo snapshot pubblicato; il report ne conserva l’ID.

Ricerca, suggerimenti e dettagli offrono `execute` bloccante e `submit` con Future nello stesso runtime, separato dal worker sync. Senza runtime, submit dà InvalidInput. Acquisizione snapshot all’inizio dell’esecuzione, non all’accodamento: senza ID usa l’attivo, con ID esattamente la versione richiesta. Future trasportano gli errori; il chiamante scarta risposte obsolete.

`close()` è idempotente: ferma l’ammissione, attende job/letture accettate (anche execute), chiude risorse e rilascia lock. Nuove operazioni durante/dopo chiusura → InvalidInput. Durante pulizia le nuove acquisizioni danno SnapshotUnavailable; quelle già aperte completano. Chiudere la finestra non implica cancel automatico.

## Porte infrastrutturali

Application definisce i [Protocol](../backend/src/local_document_search/application/ports.py), infrastructure li implementa:

| Porta | Contratto |
|---|---|
| `DirectoryResolverPort` | Radice utente → assoluta valida, senza attraversare link. |
| `FileDiscoveryPort.discover(root)` | Sequenza ordinata di `FileCandidate(root_directory, metadata)`; scansione fallita è errore, non esclusione. Niente diff/lettura contenuto. |
| `DocumentReaderPort.read(candidate)` | `Extracted(CanonicalDocument)` / `Excluded(reason)` / `ExtractionFailed(reason)`; niente assegnazione ID/posting. [Regole per formato](INDEXING_AND_ANALYSIS.md#discovery-e-reader). |
| `SnapshotRepositoryPort` | load_active, reserve_document_ids, acquire, save_candidate, validate_candidate, activate, discard_candidate. Prenotazione ID durevole prima del candidato; acquire protegge la versione fino all’uscita dal contesto, anche con eccezione. |
| `LifecycleSnapshotRepositoryPort` | Aggiunge select_directory, clear, close e indicatore incompatible; coordina invalidazione, barriera letture e pulizia dei dati posseduti. |
| `SettingsRepositoryPort` | load/save/clear di directory e LastCheck (istante, esito updated/no_changes/failed/cancelled, diagnostica opzionale); niente indici o conteggi derivabili. |
| `PreferencesRepositoryPort` | load_preferences/save_preferences in [preferences.py](../backend/src/local_document_search/application/preferences.py), separata dallo snapshot. |

## Preferenze e distribuzione

Lingua e tema persistono separatamente dagli snapshot: cambiarli non ricrea l?indice. Isolamento v1 e gestione dei dati da installer seguono la [politica di distribuzione](SECURITY_AND_PRIVACY.md).

**Preferenze:** `DesktopPreferences(language="it", theme="light")` ammette `it/en` e `light/dark`; `GetDesktopPreferences.execute()` e `SaveDesktopPreferences.execute(value)` usano una porta applicativa e la tabella preferenze del catalogo v2, indipendente dallo snapshot. Valori non validi danno `InvalidInput`; errori persistenti danno `StorageFailure`. `ClearLocalData` cancella anche lingua e tema dopo conferma UI, riportando i default. La UI esegue richieste in worker, mostra solo risposte del contesto e dello snapshot correnti e richiede `RELEVANCE` esplicitamente; i default CLI/API non cambiano.

Le decisioni di ranking e snippet sono nell'[ADR 0010](adr/0010-v2-retrieval.md). [Decisioni ancora aperte](adr/README.md#decisioni-aperte), [scenari](TEST_STRATEGY.md).

Il desktop apre il file con directory e percorso del risultato corrente, senza richiedere GetDocument. Navigazione e filtri sono stato di sessione del controller; solo lingua/tema persistono. [UX](UX_WINDOWS.md).

## Percorso desktop pubblico stabile

La composizione desktop e il rilevamento della sessione usano `%LOCALAPPDATA%/LocalDocumentSearch/Data`. Le porte applicative, i DTO e lo schema SQLite non cambiano; storage esplicito per test/diagnostica resta supportato. Nessuna lettura o importazione automatica dei dati storici v1 o di `LocalDocumentSearchV2`; primo avvio senza sessione nel nuovo percorso.
