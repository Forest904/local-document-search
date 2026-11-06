# Architecture — Modular Monolith / Ports & Adapters

**Stato:** backend M1–M7 implementato e verificato localmente; runtime concorrente e lock operativi. Desktop e distribuzione restano M8–M9; [evidenze M7](M7_VERIFICATION.md).

## 1. Principi

1. Domain: identità documentale, manifest, indici, analyzer e regole di matching **senza I/O**.
2. Application: orchestration dei casi d'uso, sincronizzazione, sessione e job; definisce le porte di cui ha bisogno.
3. Infrastructure: filesystem, reader, persistenza snapshot e settings, implementando le porte.
4. Presentation: CLI oggi, desktop Windows domani, tramite gli stessi contratti applicativi.
5. Un solo processo/job scrittore e un solo snapshot attivo per la directory corrente.

## 2. Dipendenze (dal codice)

```mermaid
flowchart TB
  UI[Windows frontend futuro] --> API[Application API in-process]
  CLI[CLI] --> API
  API --> APP[Application services + use cases]
  APP --> DOM[Domain: documents, analyzers, indexes, queries]
  INF[Infrastructure adapters] -. implementano porte definite in Application .-> APP
  INF --> DOM
  APP -. chiama porte .-> INF
```

Le frecce tratteggiate descrivono contratti/runtime. Il Domain **non importa** Application o Infrastructure; gli adapter concreti **dipendono** dalle astrazioni interne.

PySide6 Qt Widgets e backend nello stesso processo mediante contratti applicativi; nessun HTTP o IPC. CLI e UI hanno composition root dedicati che assemblano gli stessi servizi.

## 3. Flusso di indicizzazione

```mermaid
flowchart LR
  D[Directory selection / startup / manual Sync] --> J[IndexingJobManager]
  J --> S[IndexSynchronizer]
  S --> F[Recursive discovery]
  F --> M[Manifest diff: path + size + mtime_ns]
  M --> R[Readers TXT / MD / PDF]
  R --> C[CanonicalDocument]
  C --> A[Filename + Content analyzers]
  A --> B[IndexBuilder]
  B --> T[Snapshot candidate]
  T --> P[Persist + atomic activate]
```

I file invariati possono riutilizzare informazioni dello snapshot precedente; i documenti rimossi devono sparire sia dal catalogo sia dai due indici. Riuso logico degli invariati, senza rilettura; serializzazione completa in SQLite, indici/draft in RAM.

## 4. Flusso della ricerca

`SearchRequest` → `QueryParser` → analisi coerente con il campo → `QueryEvaluator` → snapshot attivo immutabile → `SearchResponse`. La ricerca non legge direttamente dal filesystem e non controlla se i documenti originali esistano ancora. `GetDocument` può usare il testo persistito.

Ogni ricerca si lega allo snapshot acquisito all'inizio. Il risultato deve comunicare lo `snapshot_id` per evitare ambiguità con gli aggiornamenti concorrenti.

## 5. Aggregato persistente

```text
IndexSnapshot (immutable once active)
  snapshot_id
  root_directory
  schema_version
  processing_version
  created_at
  IndexManifest        # sorgenti e fingerprint, incluse esclusioni
  DocumentCatalog      # metadati + testo estratto dei documenti indicizzati
  FilenameIndex        # term -> docID -> sorted positions
  ContentIndex         # term -> docID -> sorted positions
```

L'`IndexSnapshot` è un **aggregate boundary logico**, non implica un singolo file o un'unica classe monolitica. I draft possono essere modificati solo durante il build; dopo il commit, nessuna parte della versione pubblicata viene alterata.

## 6. Runtime e concorrenza

- `InitializeApplication` recupera directory e snapshot, poi richiede un job di sincronizzazione se una directory è configurata.
- `SelectDirectory` blocca la selezione se un job è attivo e avvia il sync per la nuova sorgente.
- `IndexingJobManager` gestisce al massimo un job attivo; esecuzione asincrona per Windows, bloccante opzionale per CLI/test.
- Il frontend riceve status/progress DTO, mai oggetti interni di posting.
- Il nuovo snapshot è **candidato** fino alla persist/validate/activate. Gli errori lasciano in uso l'ultimo snapshot valido della stessa directory.
- Se viene scelta una directory diversa, non si mostrano risultati della directory precedente come se fossero della nuova.

## 7. Installazione e distribuzione

Il backend è un package Python con dominio indipendente dal sistema operativo. `frontend/` ospiterà PySide6 Qt Widgets. Target Windows 11 x64: ZIP portabile pyside6-deploy standalone, senza Python preinstallato. Versioni/configurazione riproducibili e verifica su ambiente pulito in M9; nessun frontend operativo nello scaffold.

## 8. Confini intenzionalmente esclusi

Nessuna architettura a microservizi; niente OCR o infrastrutture cloud; nessun framework di eventi general-purpose; niente interfaccia astratta per ogni singolo value object. Aggiungere porte solo per confini reali (I/O, testabilità e trasporto).

## 9. Documenti collegati

[DOMAIN_MODEL](DOMAIN_MODEL.md) · [INTERFACE_CONTRACTS](INTERFACE_CONTRACTS.md) · [SNAPSHOTS_AND_SYNC](SNAPSHOTS_AND_SYNC.md) · [REPOSITORY_LAYOUT](REPOSITORY_LAYOUT.md)

## 10. Runtime v1 e primo incremento

Un worker sync e un worker separato per ricerca/dettagli; execute rimane bloccante, submit restituisce Future.
La futura UI riceverà i DTO tramite il proprio adapter; nessun callback grafico nel backend.
Application non importa Qt; dominio non conosce thread, SQLite o reader.
Lock OS esclusivo per tutta la sessione persistente; seconda istanza rifiutata prima di aprire i database.
La CLI Homework usa soltanto memoria e non acquisisce il lock.
Chiusura attende job e letture; arresto forzato gestito dal recovery.
CLI M3 usa repository in memoria e build bloccante; M5/M6 introducono persistenza e diff
senza duplicare il motore né richiedere funzionalità future per la consegna.
