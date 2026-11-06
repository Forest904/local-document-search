# Registro decisioni v1 e limiti

**Stato:** OD-01…OD-23 risolte per la v1 o escluse esplicitamente; implementazione non iniziata.
Le decisioni sono approvate il 6 novembre 2026. Accepted significa progettato, non verificato nel codice.
Nuove scelte che cambiano comportamento, contratti o dipendenze richiedono confronto con l'utente.

## Tracciabilità

| ID | Decisione v1 | Specifica / ADR | Verifica |
|---|---|---|---|
| OD-01 | SQLite, snapshot completi; niente full-text SQL | [ADR 0008](adr/0008-sqlite-snapshots.md) | M5 |
| OD-02 | Candidato, validazione e riferimento attivo nella stessa transazione; recovery SQLite | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M5 |
| OD-03 | Attivo e precedente; letture in corso protette; nessuna cache di altre directory | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M5–M7 |
| OD-04 | Indici/draft in RAM, no spill; ResourceFailure quando intercettabile, nessun commit parziale | [ADR 0008](adr/0008-sqlite-snapshots.md) | M5, M9 |
| OD-05 | pypdf, testo in ordine di pagina, no OCR; password necessaria/errore → FAILED | [Analisi](INDEXING_AND_ANALYSIS.md) | M4 |
| OD-06 | markdown-it-py; testo visibile e inline code, esclusi code block/front matter/HTML grezzo | [Analisi](INDEXING_AND_ANALYSIS.md) | M4 |
| OD-07 | UTF-8 strict con BOM ammesso; nessun fallback | [ADR 0007](adr/0007-analysis-and-readers.md) | M3–M4 |
| OD-08 | NFC+casefold, accenti mantenuti, niente stemming/stop word; focus lingue latine | [Analisi](INDEXING_AND_ANALYSIS.md) | M2 |
| OD-09 | Filename senza suffisso, separazione CamelCase e lettere/cifre | [Analisi](INDEXING_AND_ANALYSIS.md) | M2 |
| OD-10 | Clausole termini/frasi in AND; prefissi CLI nome/contenuto/entrambi | [Contratti](INTERFACE_CONTRACTS.md) | M2–M3 |
| OD-11 | Riuso logico degli invariati, serializzazione di snapshot completi | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M5–M6 |
| OD-12 | Path relativi preservati; nessun casefold/normalizzazione Unicode distruttiva; rename remove+add | [Dominio](DOMAIN_MODEL.md) | M3, M6 |
| OD-13 | Schema/processing incompatibili → rebuild, niente migrazione né ricerca incompatibile | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M6 |
| OD-14 | Esito/ultimo controllo in stato operativo separato; no-change non crea snapshot | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M6 |
| OD-15 | PySide6 Qt Widgets; Windows 11 x64, ZIP portabile pyside6-deploy standalone | [ADR 0009](adr/0009-desktop-runtime.md) | M8–M9 |
| OD-16 | Chiamate in-process ai contratti; niente IPC/HTTP; una istanza sullo storage | [Architettura](ARCHITECTURE.md) | M7–M9 |
| OD-17 | Ordine lessicografico per percorso relativo preservato; niente scoring | [Contratti](INTERFACE_CONTRACTS.md) | M2, M8 |
| OD-18 | Testo completo e apertura file; snippet/highlighting fuori v1 | [UX](UX_WINDOWS.md) | M8 |
| OD-19 | Ricerca con Invio; polling 200 ms; check 1,5 s; pagine da 50 | [UX](UX_WINDOWS.md) | M8 |
| OD-20 | LOCALAPPDATA, protezioni account, niente cifratura aggiuntiva; ClearLocalData | [Privacy](SECURITY_AND_PRIVACY.md) | M6, M8–M9 |
| OD-21 | PDF senza caratteri non-whitespace escluso; misti indicizzati per testo disponibile | [Analisi](INDEXING_AND_ANALYSIS.md) | M4 |
| OD-22 | Sync sovrapposto restituisce stesso job_id con reused=true | [Contratti](INTERFACE_CONTRACTS.md) | M7 |
| OD-23 | Cancel, watcher, OR/NOT, fuzzy, scoring e OCR esclusi | [PRD](PRD.md) | M0, M9 |

## Limiti accettati, non bug

- Size e mtime_ns invariati possono nascondere modifiche; nessun hash dei sorgenti.
- Risultati potenzialmente obsoleti fino al sync; nessuna verifica filesystem per query.
- Un file è un documento: niente pagine/sezioni o coordinate di provenienza.
- Le frasi possono attraversare confini di pagina/paragrafo dopo l'estrazione.
- Ordine PDF imperfetto; nessuna segmentazione linguistica dedicata CJK.
- Byte completati misurano avanzamento, non ETA.
- Sorgenti statiche durante il job; nessuna protezione da modifiche concomitanti.
- Nessun limite applicativo alla dimensione, ma RAM/disco finiti; possibile terminazione del processo.

## Rischi e verifiche assegnate

- Memoria: snapshot attivo più draft; misurare corpus personale contenuto in M9.
- PDF/Markdown: fixture di layout ed esclusioni in M4; documentare perdite intenzionali.
- Commit: fault injection e riavvio in M5, ripetuti sul pacchetto in M9.
- Path: nomi distinti, alias e rename in M3/M6; non fondere documenti tramite normalizzazione.
- Consegna: M3 indipendente dalle estensioni, come in [Roadmap](ROADMAP.md).
- Responsività: worker non garantisce da solo assenza di rallentamenti; verificare UI sotto carico in M8/M9.

## Governance

Per nuove decisioni aggiornare ADR, questo registro, specifiche interessate e test di accettazione.
I dettagli interni possono essere affinati senza riaprire requisiti o introdurre funzionalità fuori scope.
