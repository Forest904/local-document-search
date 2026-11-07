# Decisioni architetturali

**Accepted** indica una direzione concordata, non implementazione né collaudo. Gli ADR 0001–0009 documentano v1; restano consultabili insieme all'[archivio v1](../archive/v1/README.md). Gli ADR 0010–0014 fissano la direzione v2. Le scelte ancora aperte sono soltanto nel [registro corrente](../OPEN_DECISIONS.md).

L'[ADR 0014](0014-v2-performance-budgets.md) fissa metodo e budget V2-D01
approvati dopo la baseline misurata; il codice v1 non è dichiarato conforme.

| ADR | Argomento | Relazione v2 |
|---|---|---|
| [0001](0001-modular-monolith.md) | Monolite modulare e porte | Conservato |
| [0002](0002-canonical-document.md) | Un file, testo canonico | Conservato |
| [0003](0003-positional-index.md) | Due indici posizionali | Esteso da 0010 |
| [0004](0004-snapshot-sync.md) | Snapshot e sync | Esteso da 0012 |
| [0005](0005-ingestion-policy.md) | Reader e discovery | Conservato |
| [0006](0006-application-interfaces.md) | Casi d'uso e porte | Esteso dai contratti v2 |
| [0007](0007-analysis-and-readers.md) | Analyzer e query v1 | Esteso da 0010 |
| [0008](0008-sqlite-snapshots.md) | Storage v1 | Strategia v2 aperta in 0012 |
| [0009](0009-desktop-runtime.md) | Qt Widgets, ZIP v1 | UI sostituita da 0011; ZIP da 0013 |
| [0010](0010-v2-retrieval.md) | Vocabolario ordinato e ricerca v2 | Direzione approvata, da implementare |
| [0011](0011-v2-desktop.md) | Qt Quick e UX | Direzione approvata, da implementare |
| [0012](0012-v2-lifecycle-storage.md) | Lifecycle e isolamento dati | Direzione approvata, da implementare |
| [0013](0013-v2-distribution.md) | Installer e distribuzione | Direzione approvata, da implementare |

Nuove decisioni che cambiano requisiti, contratti o dipendenze aggiornano ADR, registro, specifiche e scenari. Dettagli interni ordinari non richiedono un ADR.
