# Roadmap — Dallo scaffold alla v1 desktop

**Stato:** M1–M8 implementate e verificate localmente; M9 richiede il collaudo del pacchetto finale e la correzione delle lacune normative. Il 7 novembre 2026 l'utente ha rinviato alle versioni successive Windows pulito/account standard distinto: l'uscita M9 è ora locale sul PC attuale. Il rinvio non dimostra portabilità. [Evidenze M9](M9_VERIFICATION.md).
M0 verificata documentalmente il 6 novembre 2026: [evidenze e limiti](M0_VERIFICATION.md). M1 verificata localmente il 6 novembre 2026: [evidenze e limiti](M1_VERIFICATION.md); CI della baseline de93bab verde su Windows e Ubuntu. M2 verificata localmente il 6 novembre 2026: [evidenze e limiti](M2_VERIFICATION.md). M3 verificata localmente il 6 novembre 2026: [evidenze e limiti](M3_VERIFICATION.md). M4 verificata localmente il 6 novembre 2026: [evidenze e limiti](M4_VERIFICATION.md). M5 verificata localmente il 6 novembre 2026: [evidenze e limiti](M5_VERIFICATION.md). M6 verificata localmente il 6 novembre 2026: [evidenze e limiti](M6_VERIFICATION.md). M7 verificata localmente il 6 novembre 2026: [evidenze e limiti](M7_VERIFICATION.md). M8 verificata localmente il 6 novembre 2026: [evidenze e limiti](M8_VERIFICATION.md). M9: packaging implementato; verifiche locali e limiti in [Verifica M9](M9_VERIFICATION.md). La prova Windows pulito è rinviata alle versioni successive.
Sequenza lineare: ogni milestone richiede la precedente, mai una milestone futura.
Prima consegna: CLI TXT. Traguardo: Windows 11 x64, ZIP autonomo senza Python preinstallato.

## Come usare questa roadmap

- Seguire le attività nell'ordine indicato; chiudere ogni milestone con evidenze verificabili.
- Registrare comandi, esiti e artefatti; specifiche approvate non equivalgono a codice funzionante.
- Cambi a comportamento, contratti o dipendenze richiedono decisione esplicita e aggiornamento dei documenti.
- CLI e UI condividono casi d'uso e motore; evitare framework e ottimizzazioni preventive.
- I dettagli normativi risiedono nelle specifiche collegate e negli ADR, non in copie divergenti.

## Sequenza

| Milestone | Risultato | Stato |
|---|---|---|
| M0 | Specifica eseguibile | Verificata (documentazione, 2026-11-06) |
| M1 | Fondazioni verificabili | Verificata localmente (2026-11-06); CI della baseline de93bab verde su Windows e Ubuntu |
| M2 | Motore di ricerca puro | Verificata localmente (2026-11-06); CI della baseline de93bab verde su Windows e Ubuntu |
| M3 | CLI TXT e Homework 3 | Verificata localmente (2026-11-06); 3 test saltati, CI remota da verificare |
| M4 | Ingestione multiformato | Verificata localmente (2026-11-06); 5 test saltati, CI remota da verificare |
| M5 | Snapshot persistenti | Verificata localmente (2026-11-06); 5 test saltati, CI remota da verificare |
| M6 | Sync e lifecycle | Verificata localmente (2026-11-06); 5 test saltati, CI remota da verificare |
| M7 | Job e concorrenza | Verificata localmente (2026-11-06); 5 test saltati, CI remota da verificare |
| M8 | Desktop completo | Verificata localmente (2026-11-06); CI della baseline de93bab verde su Windows e Ubuntu |
| M9 | Distribuzione e accettazione v1 | Packaging e prove locali storiche disponibili; collaudo ZIP finale in corso, Windows pulito rinviato ([evidenze](M9_VERIFICATION.md)) |

## M0 — Specifica eseguibile

**Ingresso:** Scaffold attuale; solo progettazione.

**Attività ordinate**
1. Formalizzare negli ADR le decisioni su ricerca, reader, storage e runtime.
2. Allineare dominio e contratti: clausole miste, pulizia dati, riuso job e paginazione.
3. Collegare ogni OD-01…OD-23 a decisione/esclusione e milestone di verifica.

**Confini:** Solo documentazione; nessuna dipendenza installata o API Python anticipata.

**Verifica e uscita**
- Registro completo; nessun TBD v1 implicito; link validi e milestone senza cicli.
- Contratti coerenti ed esempi di accettazione definiti, senza dichiarare implementato il prodotto.

**Riferimenti:** [Decisioni](OPEN_DECISIONS.md), [ADR](adr/README.md), [Contratti](INTERFACE_CONTRACTS.md).

## M1 — Fondazioni verificabili

**Ingresso:** M0 verificata; Python >=3.12 e Ports & Adapters.

**Attività ordinate**
1. Configurare ambiente riproducibile, pytest e CI.
2. Introdurre tipi minimi per documenti, token, clausole, snapshot e DTO.
3. Definire porte e punto di composizione minimo; verificare automaticamente i confini d'import. Il collegamento operativo a casi d'uso e adapter resta in M3.

**Confini:** Domain puro; application dipende da dominio e porte; nessun Qt/SQLite/parser nel core.

**Verifica e uscita**
- Installazione da ambiente pulito e test di invarianti verdi; zero test non è successo.
- Nessun framework generico o astrazione senza utilizzatore concreto.

**Evidenze:** 73 test superati su Windows/Python 3.12.2, installazione in ambiente virtuale e `pip check` riusciti. GitHub Actions configurata per Windows/Linux e Python 3.12; nessuna esecuzione remota verificata. Dettagli e comandi in [Verifica M1](M1_VERIFICATION.md).

**Riferimenti:** [Layout](REPOSITORY_LAYOUT.md), [Dominio](DOMAIN_MODEL.md), [Test](TEST_STRATEGY.md).

## M2 — Motore di ricerca puro

**Ingresso:** M1; analyzer e grammatica fissati.

**Attività ordinate**
1. Implementare analyzer distinti e preparazione filename senza estensione.
2. Implementare parser di termini/frasi AND con errori espliciti.
3. Costruire posting e catalogo nel draft; congelare lo snapshot interrogabile.
4. Implementare matching per campo, BOTH e ordine deterministico.

**Confini:** Dominio senza I/O o conoscenza dei formati dei documenti.

**Verifica e uscita**
- Unicode, apostrofi, CamelCase, numeri, posizioni e termini ripetuti verificati.
- Query miste soddisfatte in un singolo campo; nessun match distribuito tra campi.
- Modifiche successive al draft non alterano lo snapshot attivo.

**Evidenze:** 145 test superati su Windows/Python 3.12.2, inclusi 72 nuovi casi M2; `pip check` riuscito. Analyzer, parser, draft/builder, matching e isolamento degli snapshot verificati con dati sintetici in memoria. [Verifica M2](M2_VERIFICATION.md). CLI e persistenza restano nelle milestone successive.

**Riferimenti:** [Analisi](INDEXING_AND_ANALYSIS.md), [Dominio](DOMAIN_MODEL.md).

## M3 — CLI TXT e Homework 3

**Ingresso:** M2; UTF-8 rigoroso e discovery senza symlink/junction.

**Attività ordinate**
1. Implementare discovery TXT ricorsiva e reader con ordine stabile.
2. Orchestrare build/ricerca in application usando un repository in memoria.
3. Collegare CLI e composition root: directory e sessione query per campo.
4. Eseguire circa dieci query, misurare file/tempi e compilare la relazione.

**Confini:** Filesystem in infrastructure; CLI senza algoritmi; adapter in memoria riutilizzabile nei test.

**Verifica e uscita**
- Sessione console completa con AND, frasi e clausole miste.
- Encoding/lettura errati non espongono candidati parziali.
- Relazione con query, risultati, ambiente, numero file, tempi e URL repository reali.

**Evidenze:** 194 test superati, 3 saltati su Windows/Python 3.12.2; installazione sviluppo e `pip check` riusciti. Dieci query e due regressioni PASS su 8 TXT sintetici (192 byte), build iniziale misurato in 0,016752 s. [Verifica M3](M3_VERIFICATION.md), [relazione compilata](homework-3/REPORT.md). Nessun push o invio al docente; CI remota non verificata.

**Riferimenti:** [Consegna](homework-3/ASSIGNMENT_ALIGNMENT.md), [Query](homework-3/QUERY_TEST_PLAN.md), [Relazione](homework-3/REPORT_TEMPLATE.md).

## M4 — Ingestione multiformato

**Ingresso:** M3 già consegnabile; pypdf e markdown-it-py scelti.

**Attività ordinate**
1. Implementare Markdown dai token, separando blocchi e applicando le esclusioni.
2. Implementare PDF concatenando testo delle pagine, senza OCR.
3. Estendere discovery e registrazione reader senza cambiare analyzer/evaluator.

**Confini:** Reader negli adapter, senza assegnazione ID o costruzione posting.

**Verifica e uscita**
- Contract test per Extracted, Excluded ed ExtractionFailed.
- Markdown: tabelle, link, alt immagini, codice inline, HTML e front matter.
- PDF: testuale/misto, immagini, spazi, protetto e corrotto; TXT/MD vuoti ricercabili per nome.

**Riferimenti:** [Analisi](INDEXING_AND_ANALYSIS.md), [Contratti](INTERFACE_CONTRACTS.md).

**Evidenze M4:** 234 test superati, 5 saltati su Windows/Python 3.12.2; installazione sviluppo e `pip check` riusciti. Reader Markdown/PDF, discovery multiformato, CLI e conservazione dello snapshot precedente verificati con fixture sintetiche. [Verifica M4](M4_VERIFICATION.md). CI remota non verificata.

## M5 — Snapshot persistenti

**Ingresso:** M4; SQLite, snapshot completi e retention minima.

**Attività ordinate**
1. Implementare round-trip di manifest, catalogo, testo e posting.
2. Salvare/validare candidato e riferimento attivo nella stessa transazione.
3. Pubblicare in memoria dopo commit; aggiungere caricamento e recovery.
4. Conservare attivo/precedente, proteggere letture in corso e predisporre pulizia dati.

**Confini:** SQLite solo in infrastructure; matching e indici proprietari in domain.

**Verifica e uscita**
- Round-trip esatto, rollback, crash prima/durante/dopo commit e disco pieno simulato.
- Mai snapshot parziali al riavvio; versione eliminata → SnapshotUnavailable.
- Storage per utente; nessuna modifica ai documenti originali.

**Evidenze M5:** 268 test superati, 5 saltati su Windows/Python 3.12.2; installazione sviluppo e `pip check` riusciti. Round-trip, pubblicazione atomica, recovery, retention, letture protette e `GetDocument` verificati nel backend. CLI invariata; lifecycle e lock rinviati a M6–M7. Crash simulati di processo, non perdita di alimentazione. [Verifica M5](M5_VERIFICATION.md).

**Riferimenti:** [Snapshot](SNAPSHOTS_AND_SYNC.md), [Privacy](SECURITY_AND_PRIVACY.md).

## M6 — Sync e lifecycle

**Ingresso:** M5; diff path+size+mtime_ns e rebuild per incompatibilità.

**Attività ordinate**
1. Implementare add/modify/remove e riuso logico dei documenti invariati.
2. Preservare ID sullo stesso percorso e aggiornare entrambi gli indici.
3. Integrare startup, settings, cambio directory e stato no-change.
4. Integrare rebuild e ClearLocalData a job fermo.

**Confini:** Application orchestra porte; filesystem e persistenza restano adapter.

**Verifica e uscita**
- Invariati non riletti, rename = removed+added, no-change senza nuovo snapshot.
- Sorgente assente conserva snapshot compatibile; incompatibile non è interrogabile.
- Cambio directory senza risultati vecchi; rebuild fallito conserva i dati precedenti.

**Riferimenti:** [Snapshot](SNAPSHOTS_AND_SYNC.md), [Contratti](INTERFACE_CONTRACTS.md).

**Evidenze M6:** 293 test superati, 5 saltati su Windows/Python 3.12.2; `pip check` riuscito. Diff, riuso senza rilettura/analisi, startup, cambio directory, rebuild, crash di processo e pulizia verificati. CLI invariata; worker e lock restano M7. [Verifica M6](M6_VERIFICATION.md).

## M7 — Job e concorrenza

**Ingresso:** M6 funzionante in modalità bloccante.

**Attività ordinate**
1. Aggiungere JobManager con un worker e stesso algoritmo sync/async.
2. Esporre progresso e indicazione esplicita di job riutilizzato.
3. Eseguire ricerche su snapshot acquisito fuori dal futuro thread UI.
4. Integrare lock per tutte le sessioni persistenti e chiusura che attende job/letture; CLI Homework volatile invariata.

**Confini:** Coordinamento applicativo; primitive esterne negli adapter; nessun Qt nel core.

**Verifica e uscita**
- Trigger sovrapposti: un job; seconda istanza rifiutata senza alterare storage.
- Ricerca su N durante commit N+1 senza mix; letture già iniziate completano.
- Scansione indeterminata, sole rimozioni senza divisione per zero, successo dopo commit.
- Chiusura normale attende; arresto forzato lascia recovery valido.

**Riferimenti:** [Architettura](ARCHITECTURE.md), [Contratti](INTERFACE_CONTRACTS.md).

**Evidenze M7:** 314 test superati, 5 saltati su Windows/Python 3.12.2; installazione sviluppo e `pip check` riusciti. Runtime con un worker sync e un worker letture, riuso dei job, progresso, snapshot protetti, lock OS e chiusura con attesa verificati con thread e processi reali. [Verifica M7](M7_VERIFICATION.md). CLI invariata; nessuna verifica Qt o del pacchetto.

## M8 — Desktop completo

**Ingresso:** M7; PySide6 Qt Widgets, stesso processo, nessun IPC/server.

**Attività ordinate**
1. Collegare selettore, stato directory e ricerca ai casi d'uso.
2. Aggiungere lista, pagine da 50, testo completo e apertura file.
3. Integrare polling 200 ms, check 1,5 secondi ed errori.
4. Integrare privacy notice, pulizia dati e chiusura durante job.

**Confini:** Frontend usa DTO pubblici; composition root assembla servizi e adapter.

**Verifica e uscita**
- Invio avvia ricerca; UI responsiva durante build, query e anteprima.
- Risposte superate non sovrascrivono nuova richiesta o directory.
- File assente, versione rimossa e sorgente indisponibile hanno recupero esplicito.
- Pulizia disabilitata durante job; nessun accesso UI diretto allo storage.

**Riferimenti:** [UX](UX_WINDOWS.md), [Privacy](SECURITY_AND_PRIVACY.md).

**Evidenze M8:** pacchetto frontend separato, interfaccia italiana, ricerca con Invio e pagine da 50,
testo completo, apertura file, polling e lifecycle asincroni. Backend: 314 test superati e 5 saltati;
frontend: 24 test superati. Verifica visiva Windows su 56 documenti sintetici. Installazioni e
`pip check` riusciti. [Verifica M8](M8_VERIFICATION.md). CI remota, pacchetto e misure di scala restano da verificare.

## M9 — Distribuzione e accettazione v1

**Ingresso:** M8; test pertinenti verdi.

**Attività ordinate**
1. Fissare versioni e configurazione pyside6-deploy standalone; produrre ZIP x64.
2. Includere istruzioni, dipendenze e avvisi/licenze di redistribuzione.
3. Provare lo ZIP finale sul PC attuale con ambiente del processo isolato e storage di prova; Windows pulito è rinviato alle versioni successive.
4. Eseguire corpus riproducibile e percorsi completi; registrare misure e limiti.

**Confini:** Packaging fuori dal dominio; nessun installer, updater, server o cloud.

**Verifica e uscita**
- ZIP con configurazione/versioni registrate e uso locale senza elevazione; prova su account standard distinto rinviata alle versioni successive.
- TXT/MD/PDF, sync, restart, errori e doppia istanza verificati nel pacchetto.
- Hardware, memoria massima, tempi build/riapertura/sync/query riportati.
- V1 pronta solo dopo evidenze; nessuna soglia prestazionale inventata.

**Evidenze M9 storiche:** build standalone e lock dedicato, ZIP con runtime/licenze e manifest, corpus sintetico di 3.000 documenti e circa 30 MB di testo. Backend: 314 passed e 5 skipped; frontend: 24 passed; script: 17 passed. Misure e prove sul pacchetto in [Verifica M9](M9_VERIFICATION.md). Il collaudo dello ZIP corretto è in corso. Windows pulito/account standard distinto sono rinviati alle versioni successive; M9 non è ancora completamente accettata secondo il nuovo perimetro locale.

**Riferimenti:** [Test](TEST_STRATEGY.md), [UX](UX_WINDOWS.md), [ADR desktop](adr/0009-desktop-runtime.md), [Packaging](../scripts/package/README.md).

## Vincoli di consegna

Homework 3: **13 novembre 2026 alle 18:00**, secondo il materiale del corso.
M3 non dipende da altri reader, SQLite, async o UI; nessuna consegna/pubblicazione automatica al docente.
Nessuna data desktop o soglia prestazionale concordata.
Scala: alcune migliaia di documenti e decine di MB di testo estratto.
Nessun limite applicativo ai file non significa risorse infinite: verificare ResourceFailure e recovery.
Ranking, snippet/highlighting, OCR, watcher, OR/NOT, fuzzy e cancel restano fuori v1.
