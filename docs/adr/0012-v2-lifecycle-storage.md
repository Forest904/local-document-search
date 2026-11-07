# ADR 0012 — Lifecycle robusto e isolamento v2

- **Stato:** Accepted (direzione v2), 2026-11-07; non implementato.
- **Contesto:** M9 evidenzia costi di caricamento/sync e lacune di collaudo. V1 assume sorgenti statiche durante il job e attende la chiusura senza cancel.
- **Decisione:** storage v2 distinto da v1, nessuna migrazione automatica; snapshot immutabili, attivazione atomica e single-writer. Aggiungere cancel cooperativo prima del commit e controllo dei metadati durante ingestione. Nessun hash dei sorgenti o controllo filesystem in ricerca.
- **Scelte rinviate:** layout/strategia fisica, compatibilità v2 e recovery [V2-D04](../OPEN_DECISIONS.md), budget [V2-D01](../OPEN_DECISIONS.md).
- **Conseguenze:** primo avvio richiede nuova selezione; dati v1 rimangono intatti. Size e mtime invariati possono nascondere modifiche. Cancellazione durante commit è rifiutata, con esito osservabile.
- **Relazione con v1:** estende [ADR 0004](0004-snapshot-sync.md) e [0008](0008-sqlite-snapshots.md); sostituisce per v2 l'assunzione di sorgenti statiche e l'assenza di cancel. Non impone la strategia SQLite completa di v1 alla v2.
- **Verifica:** V2-04/V2-08, T09–T11 e T14 nella [strategia](../TEST_STRATEGY.md).
