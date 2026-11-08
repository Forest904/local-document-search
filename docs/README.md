# Documentazione

**V1 archiviata; v2 in corso.** V2-01–V2-05 sono chiuse localmente e il desktop V2-06 è implementato con [verifiche ancora aperte](V2_06_DESKTOP.md). Lo stato reale, il debito M9 e la continuità M0–M9 sono nella [baseline](BASELINE.md). Un ADR accettato non prova una verifica eseguita.

## Percorso principale

[README del progetto](../README.md) → [PRD](PRD.md) → [Roadmap](ROADMAP.md): obiettivo di lettura complessivo 15–20 minuti. Per usare il software attuale seguire i README operativi, non le specifiche v2.

## Riferimenti tecnici

| Documento | Fonte autorevole per |
|---|---|
| [Architettura](ARCHITECTURE.md) | Componenti, dipendenze e flussi |
| [Layout](REPOSITORY_LAYOUT.md) | Ownership e collocazione del codice |
| [Dominio](DOMAIN_MODEL.md) | Entità e invarianti |
| [Analisi e ricerca](INDEXING_AND_ANALYSIS.md) | Reader, analyzer, matching e vocabolario |
| [Snapshot e sync](SNAPSHOTS_AND_SYNC.md) | Consistenza, lifecycle e persistenza |
| [Contratti](INTERFACE_CONTRACTS.md) | Operazioni, dati scambiati ed errori |
| [UX](UX_WINDOWS.md) | Flussi desktop e accessibilità |
| [Privacy e distribuzione](SECURITY_AND_PRIVACY.md) | Dati, installer e diritti |
| [Verifiche](TEST_STRATEGY.md) | Scenari di accettazione e metodo di misura |
| [Corpus di test](TEST_DATASETS.md) | Sintetici, fonti Internet, manifest e ground truth funzionale |
| [Decisioni aperte](OPEN_DECISIONS.md) | Scelte da approvare prima del codice pertinente |
| [ADR](adr/README.md) | Decisioni approvate e loro motivazioni |

## Come mantenere i documenti

Il PRD identifica i requisiti; la roadmap assegna le milestone; la strategia di test identifica gli scenari. I riferimenti incrociati sostituiscono le copie. Stato implementato, approvato per v2 e da decidere devono essere espliciti. Evidenze, conteggi e misure appartengono ai report, non ai documenti normativi.

[Archivio v1](archive/v1/README.md): specifiche e verifiche storiche, conservate senza reinterpretarne i risultati. [Homework 3](homework-3/README.md): materiale del corso, mantenuto al percorso originale. Gli ADR v1 rimangono consultabili e segnalano le sostituzioni limitate alla v2.
