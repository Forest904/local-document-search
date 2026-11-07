> Archivio v1 — fotografia documentale del 7 novembre 2026. Stati e risultati sono storici; non descrivono la v2. [Documentazione corrente](../../README.md).

# Registro decisioni v1 e limiti

**Stato:** OD-01…OD-23 risolte per la v1 o escluse esplicitamente; fondazioni M1 verificate localmente ([evidenze](M1_VERIFICATION.md)). Le verifiche operative assegnate alle milestone successive restano aperte.
Le decisioni sono approvate il 6 novembre 2026. Accepted significa progettato, non verificato nel codice.

M2 verifica OD-08/09, semantica query OD-10 e ordine OD-17. M3 verifica UTF-8/BOM OD-07 per TXT, prefissi CLI OD-10 e identità per percorso OD-12, con i limiti di piattaforma in [Verifica M3](M3_VERIFICATION.md). M4 verifica OD-05/06/21 e UTF-8/BOM Markdown OD-07: [evidenze e limiti](M4_VERIFICATION.md). M5 verifica OD-01/02, retention e acquisizioni esplicite OD-03, errori di risorse intercettabili OD-04 e serializzazione completa OD-11: [evidenze e limiti](M5_VERIFICATION.md). M6 verifica OD-11/12/13/14 e pulizia backend OD-20: [evidenze e limiti](M6_VERIFICATION.md). M7 verifica OD-03/16/22 per concorrenza, lock e riuso job: [evidenze e limiti](M7_VERIFICATION.md). M8 verifica frontend PySide6 OD-15/16, presentazione OD-17/18, interazioni OD-19 e informativa/pulizia UI OD-20: [evidenze e limiti](M8_VERIFICATION.md). Packaging e misure locali M9: [evidenze](M9_VERIFICATION.md); resta aperta la prova Windows senza Python.

Avvio CLI e build iniziale M3 concordati il 6 novembre 2026: directory come argomento, sessione fino a EOF/Ctrl+C, tutte le pagine stampate; [ADR 0006](../../adr/0006-application-interfaces.md) e [contratti M3](INTERFACE_CONTRACTS.md#7-superficie-operativa-m3).
M7 concordata: CLI Homework invariata; lock solo sulle sessioni persistenti. Startup/selezione asincroni, RunSynchronization attende il job condiviso, ricerca/dettagli espongono submit con Future mantenendo execute. [ADR 0006](../../adr/0006-application-interfaces.md), [ADR 0009](../../adr/0009-desktop-runtime.md).

Nuove scelte che cambiano comportamento, contratti o dipendenze richiedono confronto con l'utente.

M9 concordata: build standalone per uso personale, nessuna licenza del progetto o pubblicazione;
prove sul solo PC attuale. Packaging e corpus riproducibile implementati, misure locali registrate;
il 7 novembre 2026 l'utente ha rinviato la prova su Windows pulito/account standard distinto alle
versioni successive. L'accettazione M9 riguarda il PC attuale; il rinvio non costituisce una prova
di portabilità. Restano da verificare le altre righe M9 sul pacchetto finale.
[Verifica M9](M9_VERIFICATION.md), [ADR 0009](../../adr/0009-desktop-runtime.md).

Il 7 novembre 2026 sono stati approvati: ID documentali non riciclati fino a ClearLocalData
riuscita, anche attraverso rebuild/cambio directory; pulizia esplicita dello storage precedente;
report dettagliato dei job limitato alla sessione; fault harness compilato separato dallo ZIP.

M8 concordata: pacchetto frontend separato con dipendenza dal backend e da PySide6, launcher proprio,
informativa a ogni avvio prima di Continua e nessuna nuova preferenza persistente.
La CLI resta indipendente da Qt; dettagli e versioni verificate nell'[ADR 0009](../../adr/0009-desktop-runtime.md).

## Tracciabilità

| ID | Decisione v1 | Specifica / ADR | Verifica |
|---|---|---|---|
| OD-01 | SQLite, snapshot completi; niente full-text SQL | [ADR 0008](../../adr/0008-sqlite-snapshots.md) | M5 |
| OD-02 | Candidato, validazione e riferimento attivo nella stessa transazione; recovery SQLite | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M5 |
| OD-03 | Attivo e precedente; letture in corso protette; nessuna cache di altre directory | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M5–M7 |
| OD-04 | Indici/draft in RAM, no spill; ResourceFailure quando intercettabile, nessun commit parziale | [ADR 0008](../../adr/0008-sqlite-snapshots.md) | M5, M9 |
| OD-05 | pypdf, testo in ordine di pagina, no OCR; password necessaria/errore → FAILED | [Analisi](INDEXING_AND_ANALYSIS.md) | M4 |
| OD-06 | markdown-it-py; testo visibile e inline code, esclusi code block/front matter/HTML grezzo | [Analisi](INDEXING_AND_ANALYSIS.md) | M4 |
| OD-07 | UTF-8 strict con BOM ammesso; nessun fallback | [ADR 0007](../../adr/0007-analysis-and-readers.md) | M3–M4 |
| OD-08 | NFC+casefold, accenti mantenuti, niente stemming/stop word; focus lingue latine | [Analisi](INDEXING_AND_ANALYSIS.md) | M2 |
| OD-09 | Filename senza suffisso, separazione CamelCase e lettere/cifre | [Analisi](INDEXING_AND_ANALYSIS.md) | M2 |
| OD-10 | Clausole termini/frasi in AND; prefissi CLI nome/contenuto/entrambi | [Contratti](INTERFACE_CONTRACTS.md) | M2–M3 |
| OD-11 | Riuso logico degli invariati, serializzazione di snapshot completi | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M5–M6 |
| OD-12 | Path relativi preservati; nessun casefold/normalizzazione Unicode distruttiva; rename remove+add | [Dominio](DOMAIN_MODEL.md) | M3, M6 |
| OD-13 | Schema/processing incompatibili → rebuild, niente migrazione né ricerca incompatibile | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M6 |
| OD-14 | Esito/ultimo controllo in stato operativo separato; no-change non crea snapshot | [Snapshot](SNAPSHOTS_AND_SYNC.md) | M6 |
| OD-15 | PySide6 Qt Widgets; Windows 11 x64, ZIP portabile pyside6-deploy standalone | [ADR 0009](../../adr/0009-desktop-runtime.md) | M8–M9 |
| OD-16 | Chiamate in-process ai contratti; niente IPC/HTTP; una istanza sullo storage | [Architettura](ARCHITECTURE.md) | M7–M9 |
| OD-17 | Ordine lessicografico per percorso relativo preservato; niente scoring | [Contratti](INTERFACE_CONTRACTS.md) | M2, M8 |
| OD-18 | Testo completo e apertura file; snippet/highlighting fuori v1 | [UX](UX_WINDOWS.md) | M8 |
| OD-19 | Ricerca con Invio; polling 200 ms; check 1,5 s; pagine da 50, ritorno alla prima se cambia snapshot | [UX](UX_WINDOWS.md) | M8 |
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

- Memoria: snapshot attivo più draft; corpus sintetico M9 misurato, picco e limiti in [Verifica M9](M9_VERIFICATION.md).
- PDF/Markdown: fixture di layout ed esclusioni in M4; documentare perdite intenzionali.
- Commit: fault injection e riavvio in M5, ripetuti sul pacchetto in M9.
- Path: nomi distinti, alias e rename in M3/M6; non fondere documenti tramite normalizzazione.
- Consegna: M3 indipendente dalle estensioni, come in [Roadmap](ROADMAP.md).
- Responsività: worker non garantisce da solo assenza di rallentamenti; verificare UI sotto carico in M8/M9.

## Governance

Per nuove decisioni aggiornare ADR, questo registro, specifiche interessate e test di accettazione.
I dettagli interni possono essere affinati senza riaprire requisiti o introdurre funzionalità fuori scope.
