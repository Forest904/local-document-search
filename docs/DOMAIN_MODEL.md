# Domain Model v1

**Stato:** decisioni di dominio consolidate; tipi concreti da codificare successivamente.

## 1. Identità del documento

**Un file fisico = un documento logico**. `DocumentId` è opaco, univoco in uno snapshot; proposta implementativa: intero progressivo preservato per file con stesso percorso relativo. I file con identico basename in sottodirectory differenti restano distinti.

| Tipo | Campi concettuali | Note |
|---|---|---|
| `DocumentId` | valore opaco | Id delle posting lists |
| `RelativePath` | percorso sotto `root_directory` | Identifica la sorgente nel manifest |
| `FileFingerprint` | `size_bytes`, `mtime_ns` | Value object; **nessun hash** |
| `DocumentDescriptor` | ID, relative path, filename, format, fingerprint | Metadati sorgente |
| `CanonicalDocument` | descriptor, `content: string` | Transitorio dopo la lettura; nessuna pagina/segmento |
| `IndexedDocument` | descriptor, `extracted_text`, token counts | Persistito nel catalogo |

**Attenzione ai path:** la politica di normalizzazione Unicode/case sensitivity e gestione degli alias Windows è aperta; non assumere che due stringhe diverse rappresentino sempre file distinti.

## 2. Manifest e catalogo

`IndexManifest`: mappa **per percorso relativo** delle `FileEntry`. Ogni entry contiene fingerprint, formato, esito e riferimenti, se presenti, al documento indicizzato.

Esiti consentiti a livello di manifest pubblicato:

- `INDEXED`: documento valido nel catalogo e negli indici (un TXT vuoto può avere zero token di contenuto).
- `EXCLUDED`: esclusione intenzionale, per esempio PDF senza testo estraibile; nessun `DocumentId` presente nel catalogo per tale entry.

Un errore inatteso di reader/encoding non è un'esclusione intenzionale: il job fallisce e **non pubblica** la versione incompleta.

`DocumentCatalog`: mappa `DocumentId -> IndexedDocument`, contenente nome, percorso, formato, fingerprint e **testo estratto persistito**. Non è una copia dei file binari PDF o Markdown.

## 3. Indici invertiti

Per ogni campo abbiamo un indice posizionale indipendente:

```text
field -> term -> document_id -> [position_0, position_1, ...]
```

`Term` è una stringa normalizzata non vuota; `Posting` associa un documento alle posizioni del termine; `PositionalIndex` contiene il dizionario dei termini e le relative posting lists.

**Invarianti delle posting:**

- posizioni intere, zero-based, non negative e strettamente crescenti;
- nessun docID nelle posting che non sia nel catalogo;
- posizioni indipendenti in `filename` e `content`;
- tutte le occorrenze di un documento modificato sono sostituite per entrambi i campi;
- una phrase query richiede adiacenza e ordine nello stesso campo, anche per termini ripetuti.

## 4. Snapshot

`IndexSnapshot` è la radice di consistenza, immutabile dopo l'attivazione:

- `snapshot_id`, `root_directory`, `created_at`;
- `schema_version` e `processing_version` (incompatibilità → ricostruzione completa);
- `IndexManifest`, `DocumentCatalog`, `FilenameIndex`, `ContentIndex`.

`SnapshotDraft` è una rappresentazione modificabile **solo in fase di build**, mai usata per le ricerche. Lo stato *active* è un riferimento gestito dal repository, non un flag modificabile dentro lo snapshot.

## 5. Ricerca

- `SearchField`: `FILENAME`, `CONTENT`, `BOTH`.
- `MatchMode`: `ALL_TERMS`, `EXACT_PHRASE`.
- `SearchQuery`: ricerca interpretata, termini normalizzati e campi.
- `SearchMatch`: documento e campo/i che soddisfano **interamente** la query.

`BOTH` ha semantica `match(filename, q) OR match(content, q)`, dove la **query completa** (non i singoli termini separatamente) deve essere soddisfatta in uno dei due campi.

**Limite accettato:** il CDM è un'unica stringa. Dopo l'estrazione, una frase può attraversare pagine/paragrafi; non persistiamo provenienza a livello di pagina, né segmenti.

## 6. Invarianti dell'aggregato

1. `DocumentId` univoco nel catalogo di uno snapshot.
2. `RelativePath` univoco nel manifest.
3. Ogni entry `INDEXED` identifica esattamente un `IndexedDocument` coerente; un `EXCLUDED` non compare nel catalogo/indici.
4. Catalogo, testo estratto e posting lists derivano dalla stessa versione di analisi.
5. Per ogni campo, tutte le posting si riferiscono a ID validi e posizioni corrette.
6. Uno snapshot attivo è immutabile, completo e compatibile con il software.
7. La sostituzione/rimozione documentale non lascia posting obsolete.
8. Le differenze di fingerprint non producono aggiornamenti parziali pubblicati.

## 7. Fuori dal dominio

JobManager, status/progresso, UI spinner, scanner fisico, reader concreti, serializer e policy di retention appartengono ad Application/Infrastructure. Non introdurre Domain Entity `User`, `Workspace`, `Collection` o `DocumentPage` nella v1.
