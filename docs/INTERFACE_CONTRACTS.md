# Contratti applicativi — baseline v1 ed evoluzione v2

**Stato:** i [contratti v1](archive/v1/INTERFACE_CONTRACTS.md) e la ricerca applicativa V2-05 sono implementati nel backend. La UI e la CLI usano lo stesso backend; la CLI conserva sintassi, ordine e codici attuali.

## Operazioni di ricerca

| Operazione logica | Input | Output e invarianti |
|---|---|---|
| Ricerca | Query, campo `filename/content/both`, filtri formato/cartella opzionali, ordine rilevanza/percorso, opzioni esplicite per prefissi, pagina | `snapshot_id`, risultati della pagina e totale del medesimo insieme filtrato; ogni risultato porta documento, percorso, formato, campi corrispondenti e dati per snippet/evidenziazione |
| Suggerimenti | Testo parziale, campo, limite e contesto di snapshot corrente | Termini del vocabolario ordinato dello snapshot; nessuna esecuzione implicita della query o lettura dei sorgenti |
| Dettagli/anteprima | `document_id`, `snapshot_id`, query/contesto di evidenziazione | Metadati e testo estratto della stessa versione, con intervalli evidenziati coerenti; versione rimossa → SnapshotUnavailable |

Una query esatta conserva AND e frasi; in BOTH tutta la query deve essere soddisfatta in un campo. I prefissi si attivano soltanto con sintassi/opzione esplicita. Suggerimenti non modificano i risultati finché l'utente non esegue la ricerca. Il ranking ordina solo i match: priorità al nome, poi frequenza di posizioni distinte nei campi completi, poi percorso relativo. L'ordine per percorso è il default API e CLI; il desktop richiederà la rilevanza. Filtri e ranking si applicano prima della paginazione; `total_matches` descrive esattamente l'insieme visibile.

**Parte V2-03 implementata:** `SearchRequest.allow_prefixes` è `False` per default e abilita `termine*` fuori dalle frasi. Un prefisso deve produrre un solo token per ciascun campo selezionato, lungo almeno due caratteri normalizzati; oltre 256 espansioni per prefisso/campo la ricerca restituisce `InvalidInput` senza risultati parziali. `SuggestTerms` usa `SuggestRequest(text, field=BOTH, limit=10, snapshot_id=None)` e restituisce `SuggestResponse(snapshot_id, terms)`: termini normalizzati in ordine lessicografico, deduplicati in BOTH, massimo 50. Testo vuoto o di un carattere restituisce zero termini; token multipli o sintassi di query sono invalidi. Lo snapshot richiesto non disponibile dà `SnapshotUnavailable`. Nessuna digitazione avvia una ricerca.

**Parte V2-05 implementata:** `SearchRequest` accetta `formats` (insieme non vuoto di `DocumentFormat`, OR), `folder` (cartella relativa ricorsiva, confine per segmento), `order` (`PATH` o `RELEVANCE`) e `snapshot_id` opzionali. `SearchResult` contiene `snippet` e `filename_highlights`; `GetDocument` accetta query/campo/prefissi opzionali e restituisce `filename_highlights` e `content_highlights`. Gli intervalli `[start, end)` sono punti di codice Python sul testo restituito; nello snippet sono relativi alla finestra, la cui posizione nel testo completo è `start`. La finestra ha massimo 240 caratteri e indicatori di troncamento. Formato, cartella, ordine e snapshot non validi danno `InvalidInput`; una versione non disponibile dà `SnapshotUnavailable`.

Una pagina successiva deve appartenere a una sola versione. Se lo snapshot è cambiato, il desktop scarta la risposta e riparte dalla prima pagina con query/filtri/ordine attuali; risultati obsoleti dopo cambio directory o query non vengono mostrati. Il testo persistito sostiene snippet e anteprima; niente accesso al file sorgente durante la ricerca. Nessuna API promette rendering o coordinate PDF.

## Job e stato

| Operazione logica | Comportamento |
|---|---|
| Avvio sincronizzazione | Un job single-writer; trigger sovrapposti riferiscono il job condiviso come in v1. Ricerca possibile sul precedente snapshot della stessa directory. |
| Stato job | Fasi e progresso osservabili; esiti COMPLETED, FAILED e nuovo CANCELLED distinti. Diagnostiche sicure di sessione. |
| Annullamento | Richiede l'ID del job attivo; accettato cooperativamente prima del commit, rifiutato quando il commit è non interrompibile o il job è concluso. Esito esplicito. |
| Controllo sorgente | Metadati prima/dopo ingestione discordanti → errore del candidato e invito a riprovare; precedente invariato. |
| Pulizia/cambio directory | Rifiutati durante job incompatibile; nessun dato v1 o documento sorgente cancellato. |

`InvalidInput` copre query e opzioni non valide; `SnapshotUnavailable` versioni non disponibili; `SourceUnavailable` sorgenti mancanti; `ExtractionFailure`, `StorageFailure` e `ResourceFailure` mantengono i significati v1. CANCELLED non è un errore di lettura o storage. Il punto oltre il quale cancel è rifiutato è lo stato di commit non interrompibile, osservabile nel job.

**Backend V2-04 implementato:** `CancelSynchronization.execute(job_id)` restituisce `ACCEPTED`, `COMMIT_STARTED` o `FINISHED`; un ID sconosciuto dà `InvalidInput`. Il job annullato termina in `CANCELLED`, l'attesa bloccante restituisce `CancelledResult(job_id)` e l'ultimo controllo registra `cancelled`. `RebuildIndex.execute()` avvia un job esplicito; `RecoverPreviousSnapshot.execute()` riattiva il precedente valido solo quando non c'è un job. La composizione v2 usa `compose_v2_application`; il percorso v1 rimane disponibile per regressione.

## Preferenze e distribuzione

Lingua e tema sono preferenze persistenti nello storage v2, separate dagli snapshot. Cambiarle non genera un indice nuovo. La prima installazione v2 non importa preferenze o indici v1. Installer/upgrade/disinstallazione operano su file applicativi v2; conservano i dati v2 salvo scelta esplicita di eliminarli, senza toccare v1 o sorgenti. Nessun endpoint di rete fa parte del contratto.

Le decisioni di ranking e snippet sono nell'[ADR 0010](adr/0010-v2-retrieval.md). [Decisioni ancora aperte](OPEN_DECISIONS.md), [scenari](TEST_STRATEGY.md).
