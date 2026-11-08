# Snapshot, sincronizzazione e lifecycle

[Contratto v1 e dettagli SQLite](archive/v1/SNAPSHOTS_AND_SYNC.md). La v2 mantiene snapshot immutabili, single-writer e attivazione atomica. Il vecchio snapshot della stessa directory rimane disponibile durante il sync; un errore non pubblica risultati parziali. Layout e gate prestazionale V2-D04 sono chiusi localmente nell'[ADR 0012](adr/0012-v2-lifecycle-storage.md).

## Versioni e persistenza

Lo snapshot logico comprende manifest, catalogo, testo estratto, indici posizionali e vocabolario ordinato per campo. `schema_version` e `processing_version` identificano compatibilità; il vocabolario secondario deve riferirsi alla stessa versione degli indici primari. Candidato e riferimento attivo diventano visibili insieme dopo validazione e commit. Durante retention, letture acquisite mantengono la loro versione fino al rilascio.

Lo storage v2 per utente è distinto da v1: `%LOCALAPPDATA%/LocalDocumentSearchV2`. Il primo avvio v2 richiede selezione della cartella; nessuna migrazione automatica, nessuna lettura o pulizia dei dati v1. SQLite conserva manifest per snapshot e versioni immutabili di testo e posting per documento; i posting sono blocchi compressi e validati. Le versioni invariate sono riusate. Lo snapshot attivo è caricato all'avvio, il precedente su richiesta. Un upgrade v2 incompatibile o uno snapshot corrotto richiede rebuild/recovery espliciti; i dati precedenti restano fino alla nuova pubblicazione valida.

## Diff, sorgenti variabili e cancel

Discovery confronta percorso relativo, dimensione e `mtime_ns`; gli invariati possono riusare dati logici. La query non controlla mai i sorgenti. Durante ingestione, il job verifica metadati prima e dopo la lettura/elaborazione; una variazione osservata produce errore e retry esplicito. Dimensione e timestamp invariati restano un limite noto.

L'annullamento cooperativo è ammesso finché il job non ha iniziato il commit non interrompibile. In tal caso il candidato viene scartato, il vecchio snapshot resta attivo e l'esito è CANCELLED, distinto da FAILED. Dopo quel punto la richiesta di cancel è rifiutata e il job termina con successo o errore di commit. Chiudere la finestra durante un job segue il lifecycle definito nei [contratti](INTERFACE_CONTRACTS.md), senza introdurre un secondo writer.

Cambio directory, pulizia e nuova sincronizzazione devono rispettare il single-writer. La pulizia non tocca i sorgenti né i dati v1. Le lacune M9 relative a cambio directory, pulizia in corso e reader diventano [scenari v2](BASELINE.md).
