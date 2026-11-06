# Snapshots & Incremental Synchronization v1

**Stato:** persistenza, recovery e retention M5 implementate nel backend ([evidenze](M5_VERIFICATION.md)); diff/lifecycle/rebuild M6 implementati in modalità bloccante ([evidenze](M6_VERIFICATION.md)); coordinamento dei job, letture concorrenti e lock M7 implementati ([evidenze](M7_VERIFICATION.md)). CLI invariata in memoria; [ADR 0008](adr/0008-sqlite-snapshots.md).

## 1. Rappresentazione e memoria

Snapshot completo: versioni schema/processing, directory, manifest, catalogo con testo, due indici proprietari.
SQLite persiste snapshot completi separati logicamente per snapshot_id e un riferimento attivo.
Nessun full-text SQL; matching in domain. In RAM: versione attiva e draft, letture delle vecchie versioni finché in uso.
Riuso degli invariati logico, senza rilettura/analisi sorgenti; scrittura completa del candidato.
Nessuno spill/streaming generale. Memoria/disco insufficienti → ResourceFailure se intercettabile.
Se il sistema termina il processo, recovery al riavvio; nessuna promessa di file arbitrariamente grandi.

## 2. Identità e diff

Directory selezionata + percorso relativo preservato identificano il documento; [Dominio](DOMAIN_MODEL.md).
Fingerprint: size_bytes e mtime_ns, senza hash o controllo contenuto.
ADDED → lettura/analisi; MODIFIED → sostituzione di catalogo e posting, ID preservato.
REMOVED → eliminazione; UNCHANGED → riuso senza leggere il contenuto, anche per EXCLUDED.
Rename, compreso cambio del percorso riportato dalla discovery, è REMOVED+ADDED.
Nessuna differenza e versioni compatibili → NO_CHANGES, nessun nuovo snapshot.
Ultimo controllo riuscito/esito/diagnostica risiedono nello stato operativo, non nell'aggregato immutabile.

## 3. Transazione di pubblicazione

Adapter SQLite tramite standard library; foreign keys abilitate, journal DELETE e synchronous FULL.
Schema fisico interno versionato; niente pickle o esecuzione di dati serializzati.
1. Costruire e validare invarianti del draft in RAM.
2. Aprire una transazione, inserire l'intero candidato con manifest/catalogo/testo/posting.
3. Validare la rappresentazione persistita nella transazione e aggiornare il riferimento attivo.
4. Eseguire COMMIT; soltanto dopo pubblicare il riferimento immutabile in memoria.
5. Dichiarare successo; eseguire pulizia retention separatamente, senza invalidare il commit riuscito.

SaveCandidate/ValidateCandidate/Activate sono fasi dello stesso confine transazionale, non commit separati.
Errore prima del commit → rollback, vecchio attivo della stessa directory preservato.
Crash durante commit → recovery SQLite: stato vecchio o nuovo completo, mai un mix.
Crash dopo commit prima della pubblicazione in RAM → riavvio carica il nuovo riferimento persistito.
Un errore di pulizia è diagnostica riprovabile, non trasforma un commit riuscito in indice fallito.
Non ricostruire posting leggendo i sorgenti durante LoadActive.

## 4. Retention e letture

Conservare snapshot attivo e precedente della directory corrente.
Ogni ricerca acquisisce una versione immutabile e la mantiene fino al completamento.
La pulizia differisce la rimozione delle versioni in uso; riprova al rilascio e al riavvio.
GetDocument(document_id, snapshot_id) usa esattamente quella versione, mai un fallback alla corrente.
Versione rimossa → SnapshotUnavailable; il chiamante può ripetere la ricerca.
Una versione presente ma incompatibile non è consultabile.
Dopo crash non restano lettori attivi: recovery completa anche la pulizia pendente.

## 5. Lifecycle, directory e compatibilità

Startup carica settings e snapshot compatibile, poi richiede sync automatico.
Se la sorgente manca, conserva settings/snapshot e consenti ricerca compatibile con avviso di obsolescenza.
SelectDirectory valida la nuova radice, è rifiutata durante job e disabilita risultati della vecchia.
Nessuna cache multi-directory: vecchi dati rimossi appena non in uso; ritorno alla cartella richiede indicizzazione.
Il cambio invalida le nuove richieste di dettaglio della precedente directory; le letture già iniziate completano.

schema_version o processing_version incompatibili → rebuild automatico dai sorgenti, non migrazione.
Durante rebuild la versione incompatibile non è ricercabile; dati vecchi conservati fino al successo.
Per schema fisico incompatibile usare un database candidato separato, mantenendo l'originale.
Il catalogo di attivazione stabile seleziona il database solo dopo commit/validazione riusciti;
aggiornare questo riferimento transazionalmente nello storage di controllo.
Crash fra preparazione e selezione lascia il precedente riferimento; candidati non referenziati vengono ripuliti.
Se sorgenti indisponibili, segnalare errore e preservare dati; non simulare compatibilità.
Il catalogo di controllo usa formato stabile v1, separato dagli schemi versionati dei dati.
Questa selezione fra database riguarda solo il rebuild di schema fisico: i normali sync
pubblicano candidato e riferimento attivo nella singola transazione del database corrente.

## 6. Job, progresso e accesso esclusivo

Un worker sync; RunSynchronization bloccante e RequestSynchronization async usano IndexSynchronizer.
Un worker separato esegue ricerca/dettagli tramite submit; execute resta disponibile.
Le versioni attiva, precedente e ancora acquisite sono mantenute in RAM; al riavvio vengono caricate
attiva e precedente. Acquisizione e matching non leggono SQLite durante una transazione candidata.
Il lock database serializza writer e retention, separato dal lock delle versioni pubblicate;
la pulizia al rilascio viene differita se il writer occupa il database.
Trigger sovrapposti restituiscono stesso job_id, reused=true; nessun secondo writer.
SCANNING: totale byte sconosciuto; dopo discovery conteggiare byte dei nuovi/modificati completati.
Sole cancellazioni: fase esplicita senza divisione per zero; 100% solo dopo commit o NO_CHANGES.
Ricerche non leggono filesystem e non usano il candidato.
Le sessioni persistenti acquisiscono un lock OS esclusivo per tutta la sessione sullo storage condiviso;
la CLI Homework volatile non accede allo storage e non acquisisce il lock;
il crash rilascia il lock, senza affidarsi alla mera presenza di un file sentinel.
Seconda istanza: errore osservabile, niente apertura concorrente dello storage.
Chiusura normale attende job/letture e rilascia risorse; nessun cancel v1.

## 7. Pulizia e verifica

ClearLocalData richiede assenza di job, impedisce nuove letture e attende quelle in corso.
Elimina snapshot, settings, stato operativo, temporanei e log dell'app; torna allo stato senza directory.
Non elimina sorgenti; non promette cancellazione forense. Dettagli in [Privacy](SECURITY_AND_PRIVACY.md).
Test: [Test Strategy](TEST_STRATEGY.md), milestone M5–M7 e M9 in [Roadmap](ROADMAP.md).

## 8. Realizzazione M6

`control.sqlite3` contiene settings, ultimo controllo, selezione del database dati e registro dei
file posseduti. Il formato di controllo è v1; i normali sync mantengono la transazione M5 nel database
dati selezionato. I rebuild incompatibili usano `snapshot-<uuid>.sqlite3`: la selezione avviene solo
dopo commit/validazione del nuovo database. Anche l'incompatibilità logica usa questo percorso.
Gli orfani registrati vengono eliminati al riavvio; file estranei non vengono enumerati per cancellazione.
Errori di retention sono diagnostica riprovabile, separata dall'esito del commit.

Il database M5 `snapshots.sqlite3` viene registrato senza migrazione del contenuto. Se compatibile,
la directory viene recuperata dallo snapshot quando mancano settings. Uno storage M5 incompatibile
senza settings richiede selezione esplicita della sorgente: il backend segnala SnapshotUnavailable
e conserva il database fino al rebuild riuscito, senza interpretarne lo schema incompatibile.

ClearLocalData rimuove database dati registrati e relative sidecar, settings e stato operativo;
conserva il contenitore SQLite di controllo vuoto e il suo schema per il riuso della sessione.
M6 non produce log o altri temporanei applicativi. Nessuna garanzia di cancellazione forense.
Le acquisizioni già aperte completano; una barriera impedisce nuove letture durante la pulizia.
Questa sincronizzazione limitata non introduce worker né supporto generale a writer concorrenti.

## Allocazione ID (2026-11-07)

Gli ID nuovi provengono da un allocatore SQLite separato dagli snapshot. La prenotazione precede il candidato e rimane durevole in caso di rollback. Il contatore sopravvive a retention, rebuild, cambio directory e riavvio; ClearLocalData riuscita avvia una nuova vita. Storage precedente privo di allocatore richiede pulizia esplicita prima di nuovi job.
