# Repository Layout & Dependency Rules

## 1. Albero iniziale

```text
local-document-search/
├── README.md
├── .gitignore
├── .gitattributes
├── .editorconfig
├── backend/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/local_document_search/
│   │   ├── domain/          # documents, analysis, index, queries, snapshots
│   │   ├── application/     # contracts, ports, lifecycle, synchronization, jobs, search
│   │   ├── infrastructure/  # filesystem, readers, snapshot/settings storage
│   │   └── interfaces/      # CLI
│   └── tests/{unit,integration,fixtures}/
├── frontend/              # futuro progetto Windows
├── experiments/           # query di test e benchmark, senza dati sensibili
└── docs/                  # PRD, architecture, ADR, assignment, roadmap
```

Ogni package Python è rappresentato da un `__init__.py` e da **moduli con docstring segnaposto**, senza business logic. Il frontend contiene soltanto un README.

## 2. Matrice di dipendenza

| Modulo | Può dipendere da | Non deve dipendere da |
|---|---|---|
| `domain` | Standard library e Domain | Application, Infrastructure, UI, parser PDF |
| `application` | Domain, proprie porte | Adattatori concreti, librerie GUI |
| `infrastructure` | Application ports, Domain | Frontend Windows |
| `interfaces` | Application + composition root | Strutture mutabili dell'indice dall'esterno |
| `frontend` | API pubbliche / trasporto | Domain Python interno, filesystem di storage diretto |

I componenti vengono collegati da un piccolo **composition root** da introdurre quando sarà scelto il meccanismo d'esecuzione. Evitare un generico `shared/` che diventi una dipendenza circolare.

## 3. Responsabilità dei moduli

- `domain/documents.py`: identità e metadati dei documenti; CDM e IndexedDocument.
- `domain/analysis.py`: tokenization, normalizzazione e posizioni.
- `domain/index.py`: posting lists e costruzione dell'indice.
- `domain/queries.py`: sintassi già interpretata e matching.
- `domain/snapshots.py`: manifest, catalogo, snapshot/draft.
- `application/contracts.py`: DTO stabili dei casi d'uso.
- `application/ports.py`: interfacce dei servizi esterni.
- `application/lifecycle.py`: startup e directory selection.
- `application/synchronization.py`: diff e pipeline di aggiornamento.
- `application/jobs.py`: single-writer, sync/async, progress.
- `application/search.py`: ricerca/recupero di documenti.
- `infrastructure/filesystem.py`: discovery e metadati sorgente.
- `infrastructure/readers/`: estrazione specifica per formato.
- `infrastructure/snapshot_storage.py`: staging, validation, activation.
- `infrastructure/settings_storage.py`: directory ricordata.
- `interfaces/cli.py`: comandi dell'Homework 3 (non ancora presenti).

## 4. File operativi e Git

Gli snapshot del motore, i contenuti estratti dagli utenti, i database runtime e la configurazione personale devono restare **fuori dal repository**, in uno storage applicativo locale da definire. La `.gitignore` include convenzioni per prevenire commit accidentali, ma non garantisce protezione di file posizionati arbitrariamente.

Il repository non include un file LICENSE perché la licenza non è stata scelta. Nessun servizio CI è configurato perché non esistono test eseguibili; saranno aggiunti durante l'implementazione.
