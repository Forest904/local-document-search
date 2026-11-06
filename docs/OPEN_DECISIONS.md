# Open Decisions, Implementation Limits & Risks

**Documento di controllo:** ciò che segue **non è stato approvato o implementato**. Non colmare i vuoti con assunzioni nascoste. Quando una scelta sarà presa, registrarla in un ADR e aggiornare la documentazione coinvolta.

## 1. Decisioni approvate (non riaprire implicitamente)

Un file = un documento; una directory attiva, scansione ricorsiva; TXT/MD/PDF testuali; Markdown code blocks esclusi; nessun OCR e PDF privi di testo esclusi; encoding non valido = errore e niente commit; no symlink/junction né file symlink; nessun limite di dimensione prefissato; due positional inverted indexes proprietari; testo estratto persistito; snapshot immutabili, sync incrementale con solo path+size+mtime, single-writer, ricerca sullo snapshot precedente durante sync, progresso a byte indicativo, niente watcher continuo, query BOTH soddisfatta integralmente da un campo.

## 2. Critici per implementare la v1 backend

| ID | Argomento | Opzioni da valutare / domanda | Impatto |
|---|---|---|---|
| OD-01 | **Storage fisico** | JSON, SQLite o formato custom? Come separare manifest/testo/posting e attivare atomicamente? | Alto |
| OD-02 | **Recovery e durability** | Staging directory, pointer swap, fsync, recovery dei candidati rimasti dopo crash? | Alto |
| OD-03 | **Retention snapshot** | Quante versioni conservare, quando raccoglierle, come gestire `GetDocument(snapshot_id)`? | Alto |
| OD-04 | **Memoria e file enormi** | Build tutto in RAM o pipeline streaming/spill-to-disk? Che cosa fare in caso di ResourceFailure? | Alto |
| OD-05 | **PDF extraction** | Libreria, ordine di lettura, errori PDF protetti/corrotti, file misti testo+immagini. | Alto |
| OD-06 | **Markdown extraction** | Parser e policy precisa per heading, tabelle, link, immagini, HTML inline, front matter. | Alto |
| OD-07 | **Encoding** | UTF-8 strict, BOM, fallback automatico? Come segnalare character set non riconosciuto senza perdere dati? | Alto |
| OD-08 | **Tokenizer multilingue** | Regole esatte Unicode, NFC/casefold, apostrofi, accents, CamelCase, numeri, CJK; stop words/stemming. | Alto |
| OD-09 | **Filename analyzer** | Indicizzare estensione? Segmentazione CamelCase e confini lettera-cifra? | Medio |
| OD-10 | **Query grammar** | Sintassi per campo/virgolette, gestione errori, default AND, combinazioni consentite e stringhe vuote. | Alto |
| OD-11 | **Incremental storage** | Snapshot completo scritto ogni volta vs riuso fisico dei segmenti invariati; garbage collection. | Alto |
| OD-12 | **Identità paths Windows** | Case-insensitivity, Unicode, separatori, nomi duplicati, directory spostata, reparse points. | Alto |
| OD-13 | **Versioning/migration** | Come interpretare modifiche a schema o processing rules e quando forzare rebuild? | Alto |
| OD-14 | **No-change sync** | Come registrare ultimo controllo riuscito senza creare un nuovo snapshot? Stato operativo separato? | Medio |

## 3. Rimandabili alla UI Windows / future release

| ID | Argomento | Da decidere |
|---|---|---|
| OD-15 | Windows frontend | WPF, WinUI 3, altro stack; desktop packaging |
| OD-16 | Trasporto | IPC named pipes, API loopback, processo integrato; autenticazione locale |
| OD-17 | Ranking e ordine | Ordinamento per path per la v1 (proposto) oppure un punteggio minimale |
| OD-18 | Snippet/highlighting | Offset token→testo, troncamento, gestione frammenti PDF |
| OD-19 | Progresso UI | Frequenza eventi, debounce e durata check completamento |
| OD-20 | Privacy/retention | Storage per-utente, permessi, eventuale crittografia, cancellazione dei dati |
| OD-21 | Corpi di testo vuoti | Politica per PDF con solo spazi/artefatti o pagine parzialmente testuali |
| OD-22 | Richieste sovrapposte | Quando un secondo Sync chiede il job esistente, indicare che nessun nuovo avvio è avvenuto |
| OD-23 | Requisiti non richiesti | Cancellation, watcher continuo, OR/NOT, fuzzy matching, scoring, OCR: **non inclusi in v1** |

## 4. Limitazioni accettate — non bug

1. **Rilevazione modifiche non perfetta:** size e `mtime_ns` possono rimanere uguali nonostante contenuto cambiato.
2. **Ricerca stantia:** dopo eliminazione/modifica, un risultato resta possibile fino al successivo snapshot; non si verifica il filesystem per ogni query.
3. **Nessuna provenienza pagine:** risultati restituiscono file, non pagina PDF o sezione Markdown.
4. **Phrase queries dopo estrazione:** token adiacenti per artefatti di layout possono corrispondere erroneamente.
5. **Progress approssimativo:** byte/file ≠ costo di elaborazione o ETA.
6. **Static source assumption:** la directory non cambia **durante** il job; il sistema non protegge da mutazioni concomitanti dei sorgenti.
7. **Niente OCR:** PDF immagini non indicizzati e registrati come esclusi.
8. **Nessun limite applicativo di file size:** resta possibile memoria/spazio insufficiente; errori devono essere espliciti.

## 5. Rischi prioritari

- **R1: Snapshot troppo grandi.** Conserviamo sia testo sia posting → misurare storage e memoria prima di ottimizzare.
- **R2: PDF complessi.** Ordine di lettura scorretto → test con multi-colonna; documentare precisione limitata.
- **R3: Reader Markdown.** Eliminare markup o codice senza cancellare parole adiacenti involontariamente → test specifici.
- **R4: Crash durante commit.** Snapshot candidato mai visibile prima della validazione; protocollo concreto da testare.
- **R5: Path normalization.** Duplicati o falsi 'removed/added' su Windows → definire canonical path policy.
- **R6: Time-to-homework.** Mantenere una CLI TXT + due indici + phrase queries come primo incremento completo, senza bloccarlo dietro la futura UI.

## 6. Regola di governance

Ogni scelta risolta deve aggiornare: (1) ADR, (2) questo registro, (3) i contratti o PRD interessati, (4) test di accettazione corrispondenti.
