# ADR 0006 — Contratti applicativi, JobManager e porte d'infrastruttura

- **Status:** Accepted (design)
- **Context:** CLI e futura UI Windows devono usare le stesse operazioni mentre la costruzione dell'indice avviene senza bloccare l'interfaccia.
- **Decision:** use cases `InitializeApplication`, `SelectDirectory`, `Request/RunSynchronization`, `SearchDocuments`, `GetIndexStatus`, `GetJobStatus`, `GetDocument`; porte `FileDiscoveryPort`, `DocumentReaderPort`, `SnapshotRepositoryPort`, `SettingsRepositoryPort`. `IndexingJobManager` separato da `IndexSynchronizer`, un job attivo alla volta, progress indipendente dalla UI, supporto esecuzione sync/async dello stesso algoritmo.
- **Alternatives considered:** accoppiare comandi UI direttamente a reader/index, metodi duplicati per CLI/UI, progress grafico dentro il core.
- **Consequences:** testabilità e portabilità, DTO espliciti, più file di struttura ma responsabilità nette.
- **Open implementation details:** protocollo reale, thread/process model, lifecycle della connessione, schema esatto DTO, errori di trasporto.
- **Related:** [Interface Contracts](../INTERFACE_CONTRACTS.md), [UX Windows](../UX_WINDOWS.md).
