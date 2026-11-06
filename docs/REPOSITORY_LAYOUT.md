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
├── frontend/              # pacchetto desktop PySide6 e test Qt
├── scripts/               # automazione sviluppo Windows e relativi test
├── experiments/           # query di test e benchmark, senza dati sensibili
└── docs/                  # PRD, architecture, ADR, assignment, roadmap
```

M1 implementa modelli di dominio, DTO di ricerca, porte e `interfaces/composition.py`, con test eseguibili. M2 implementa analyzer, parser, matching e costruzione degli snapshot. M3 aggiunge build completo e ricerca applicativi, discovery TXT, reader UTF-8, repository in memoria e CLI operativa. M4 aggiunge reader Markdown/PDF, dispatcher per formato e discovery multiformato. M5 aggiunge `infrastructure/sqlite_snapshot_storage.py`, acquisizioni protette e `GetDocument`; la CLI conserva il repository volatile. M6 aggiunge lifecycle bloccante, sync incrementale, settings e `infrastructure/persistent_storage.py` per il catalogo e il rebuild. M7 implementa jobs, runtime delle letture e `infrastructure/storage_lock.py`, con coordinamento thread-safe degli adapter persistenti. M8 aggiunge il pacchetto frontend separato `local_document_search_desktop` con launcher, finestra/controller, composizione desktop e test Qt. La dipendenza PySide6 appartiene soltanto a frontend; CLI e backend restano installabili senza Qt.

## 2. Matrice di dipendenza

| Modulo | Può dipendere da | Non deve dipendere da |
|---|---|---|
| `domain` | Standard library e Domain | Application, Infrastructure, UI, parser PDF |
| `application` | Domain, proprie porte | Adattatori concreti, librerie GUI |
| `infrastructure` | Application ports, Domain | Frontend Windows |
| `interfaces` | Application + composition root | Strutture mutabili dell'indice dall'esterno |
| `frontend` | API pubbliche application, PySide6 | Domain Python interno, filesystem di storage diretto |

Il punto di composizione minimo in `interfaces/composition.py` riceve esplicitamente le quattro porte e restituisce `ApplicationDependencies`, senza eseguire I/O. M1 ne verifica il cablaggio con sostituti nei test; `compose_cli` collega i casi d'uso agli adapter multiformato M4; non usa settings o lifecycle. `compose_persistent_application` assembla separatamente il backend persistente M7, acquisendo il lock prima dei database e coordinando la chiusura dei worker. Evitare un generico `shared/` che diventi una dipendenza circolare.

## 3. Responsabilità dei moduli

- `domain/documents.py`: identità e metadati dei documenti; CDM e IndexedDocument.
- `domain/analysis.py`: tokenization, normalizzazione e posizioni.
- `domain/index.py`: posting lists e indici immutabili.
- `domain/queries.py`: sintassi già interpretata e matching.
- `domain/snapshots.py`: manifest, catalogo, snapshot/draft e IndexBuilder puro.
- `application/contracts.py`: DTO stabili dei casi d'uso.
- `application/ports.py`: interfacce dei servizi esterni.
- `application/lifecycle.py`: startup e directory selection.
- `application/synchronization.py`: build completo sincrono M3; diff e aggiornamenti in M6.
- `application/jobs.py`: single-writer, sync/async, progress.
- `application/search.py`: ricerca/recupero di documenti.
- `infrastructure/filesystem.py`: discovery e metadati sorgente.
- `infrastructure/readers/`: estrazione specifica per formato.
- `infrastructure/snapshot_storage.py`: repository in memoria con staging e retention. `infrastructure/sqlite_snapshot_storage.py`: persistenza transazionale, recovery e retention M5.
- `infrastructure/settings_storage.py`: directory ricordata.
- `interfaces/cli.py`: sessione query dell'Homework 3 e codici d'uscita.

## 4. File operativi e Git

`scripts/dev/` contiene il master di avvio VS Code e gli script coesi per virtualenv, dipendenze,
arresto e avvio desktop. `.vscode/tasks.json` è versionato; gli altri file personali VS Code restano
ignorati. Il lock dipendenze di sviluppo è distinto dalla distribuzione M9. PID e log di avvio
restano in `runtime/`, fuori da Git. [Uso e verifiche](../scripts/dev/README.md).

`scripts/package/` possiede launcher e configurazione standalone M9, lock separato, build e
licenze. Output in `build/` e `dist/`, esclusi da Git. `experiments/` contiene generatore e runner
M9; corpus/risultati in `experiments/results/`, storage di prova esterno al repository.
[Packaging](../scripts/package/README.md), [evidenze M9](M9_VERIFICATION.md).

Gli snapshot del motore, i contenuti estratti dagli utenti, i database runtime e la configurazione personale devono restare **fuori dal repository**, in `%LOCALAPPDATA%/LocalDocumentSearch` su Windows. La `.gitignore` include convenzioni per prevenire commit accidentali, ma non garantisce protezione di file posizionati arbitrariamente.

Il repository non include un file LICENSE perché la licenza non è stata scelta. GitHub Actions esegue installazione, `pip check` e pytest su Windows/Linux con Python 3.12. Il workflow è configurato; l'esecuzione remota resta da verificare. Il test AST controlla import assoluti, relativi e sotto `TYPE_CHECKING` nei moduli domain/application, vietando anche SQLite nel core. Non è una sandbox contro import dinamici o I/O arbitrario.
