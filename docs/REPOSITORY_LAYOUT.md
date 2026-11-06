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

M1 implementa modelli di dominio, DTO di ricerca, porte e `interfaces/composition.py`, con test eseguibili. M2 implementa analyzer, parser, matching e costruzione degli snapshot. Servizi applicativi e adapter operativi restano segnaposto. Il frontend contiene soltanto un README.

## 2. Matrice di dipendenza

| Modulo | Può dipendere da | Non deve dipendere da |
|---|---|---|
| `domain` | Standard library e Domain | Application, Infrastructure, UI, parser PDF |
| `application` | Domain, proprie porte | Adattatori concreti, librerie GUI |
| `infrastructure` | Application ports, Domain | Frontend Windows |
| `interfaces` | Application + composition root | Strutture mutabili dell'indice dall'esterno |
| `frontend` | API pubbliche application, PySide6 | Domain Python interno, filesystem di storage diretto |

Il punto di composizione minimo in `interfaces/composition.py` riceve esplicitamente le quattro porte e restituisce `ApplicationDependencies`, senza eseguire I/O. M1 ne verifica il cablaggio con sostituti nei test; M3 collegherà i casi d'uso e gli adapter della CLI, poi riutilizzati dal frontend in-process. Evitare un generico `shared/` che diventi una dipendenza circolare.

## 3. Responsabilità dei moduli

- `domain/documents.py`: identità e metadati dei documenti; CDM e IndexedDocument.
- `domain/analysis.py`: tokenization, normalizzazione e posizioni.
- `domain/index.py`: posting lists e indici immutabili.
- `domain/queries.py`: sintassi già interpretata e matching.
- `domain/snapshots.py`: manifest, catalogo, snapshot/draft e IndexBuilder puro.
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

Gli snapshot del motore, i contenuti estratti dagli utenti, i database runtime e la configurazione personale devono restare **fuori dal repository**, in `%LOCALAPPDATA%/LocalDocumentSearch` su Windows. La `.gitignore` include convenzioni per prevenire commit accidentali, ma non garantisce protezione di file posizionati arbitrariamente.

Il repository non include un file LICENSE perché la licenza non è stata scelta. GitHub Actions esegue installazione, `pip check` e pytest su Windows/Linux con Python 3.12. Il workflow è configurato; l'esecuzione remota resta da verificare. Il test AST controlla import assoluti, relativi e sotto `TYPE_CHECKING` nei moduli domain/application, vietando anche SQLite nel core. Non è una sandbox contro import dinamici o I/O arbitrario.
