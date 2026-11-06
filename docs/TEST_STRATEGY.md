# Test Strategy & Acceptance Plan

**Stato:** test M1 implementati e verificati localmente: modelli, DTO, coerenza/immutabilità degli snapshot, composizione minima e confini degli import. [Evidenze M1](M1_VERIFICATION.md). M2 aggiunge 72 casi per analyzer, parser, builder, matching e pipeline in memoria: [evidenze M2](M2_VERIFICATION.md). M3 aggiunge test adapter, pipeline, fault injection e CLI reale: 194 test superati e 3 skip nella suite totale; [evidenze e limiti](M3_VERIFICATION.md). M4 verifica reader e pipeline multiformato: 234 test superati e 5 skip nella suite totale; [evidenze e limiti](M4_VERIFICATION.md). M5 aggiunge 34 casi su persistenza, retention, errori e recovery: 268 test superati e 5 skip nella suite totale; [evidenze M5](M5_VERIFICATION.md). M6 aggiunge 25 casi di sync/lifecycle: 293 test superati e 5 skip nella suite totale; [evidenze M6](M6_VERIFICATION.md). M7 aggiunge 21 casi su concorrenza, progresso, lock e arresto: [evidenze M7](M7_VERIFICATION.md). M8 aggiunge 24 test Qt, integrazione con backend reale e verifica visiva Windows: [evidenze M8](M8_VERIFICATION.md). M9 aggiunge test del packaging, corpus sintetico e misure locali; [evidenze e verifiche ancora aperte](M9_VERIFICATION.md).

## 1. Livelli

| Livello | Focus | Esempi |
|---|---|---|
| Unit | Funzioni pure di dominio | Normalizzazione, token/posizioni, AND, phrase, termini ripetuti |
| Contract | Ogni adapter rispetta la porta | Reader con 3 esiti, scanner no symlink, repository atomic activate |
| Integration | Collaborazione dei moduli | Snapshot iniziale, sync con ADD/MODIFY/REMOVE, errore rollback |
| E2E | CLI e sistema completo | Indicizzazione `.txt`, query da console, persistenza tra sessioni |
| Experiments | Relazione Homework 3 | ~10 query, numero file, tempo indicizzazione, motivazioni analyzer |

## 2. Casi unitari obbligatori

- **Tokenization:** Unicode, accenti, punteggiatura, underscore, apostrofi, CamelCase e lettere/cifre nel filename; input vuoto; token ripetuti.
- **Positioning:** zero-based, posizioni crescenti, stesso termine ripetuto, nessun offset tra nome e contenuto.
- **AND:** tutte le parole nello stesso campo, ordine non vincolante, documenti con una sola parola.
- **Phrase:** `"roma tre"` trova `Roma Tre` ma non `Roma ... tre`; gestire `"data data"`, frase più lunga del documento.
- **BOTH:** `machine` nel filename e `learning` nel content **non** soddisfano query `machine learning` se nessun campo contiene entrambi.
- **Manifest:** entry INDEXED ↔ IndexedDocument ↔ posting; entry EXCLUDED senza postings.
- **ID:** uguale basename in cartelle differenti deve produrre documenti distinti.

## 3. Reader fixtures

- TXT UTF-8 valido, contenuto vuoto, encoding errato → FAILED.
- Markdown titolo/paragrafo, code fence escluso, link/tabelle/alt immagini/codice inline inclusi, HTML grezzo e front matter esclusi.
- PDF digitale con testo estraibile; PDF solo immagine → EXCLUDED; PDF corrotto/protetto non leggibile → FAILED.
- File TXT/MD/PDF identici per nome in sottodirectory; file symlink e directory junction → esclusi dalla discovery.

Usare file sintetici di dimensioni minime, idealmente con permesso di redistribuzione. I file di prova non devono contenere dati personali dell'utente.

## 4. Test di sincronizzazione

| Scenario | Expected |
|---|---|
| Prima indicizzazione | Snapshot creato, catalogo e posting coerenti |
| Riavvio su filesystem invariato | Nessun nuovo snapshot |
| Un nuovo `.txt` | Nuovo documento ricercabile dopo commit |
| Contenuto modificato | Vecchi termini rimossi, nuovi termini ricercabili |
| File eliminato | Non compare nella nuova versione, può comparire nella precedente finché attiva |
| File rinominato | REMOVED + ADDED |
| Modifica con stesso size + mtime | Non rilevata (limitazione accettata) |
| PDF senza testo | Manifest EXCLUDED, assente dai due indici |
| Errore encoding | FAILED, precedente attivo preservato |
| Crash prima di activate | Precedente preservato prima del commit; durante commit SQLite espone solo vecchio o nuovo completo |
| Due richieste sync concorrenti | Un solo writer/job |
| Ricerca durante build | Risultato completo della versione N, non mix N/N+1 |

## 5. Test del progresso

- Fase SCANNING: byte totali sconosciuti, percentuale indeterminata.
- Dopo scansione: byte pesati sui file nuovi/modificati completati, andamento monotono (ove applicabile).
- Sync con sole cancellazioni: evitare divisione per zero.
- 100% e successo solo dopo commit, oppure sync NO_CHANGES riuscita.
- Nessun job blocca il thread UI; questo verrà testato quando esisterà il frontend.

## 6. Benchmark

Misurare separatamente **tempo totale di sincronizzazione**, eventuale tempo di estrazione, tokenizzazione, build e commit. Usare un clock monotono (es. `perf_counter` in implementazione), contare file scoperti / validi / esclusi e byte; annotare hardware, ambiente, corpus e versione analyzer. Prima di confrontare prestazioni, distinguere indicizzazione iniziale, riapertura senza cambiamenti e update incrementale.

La prima consegna richiede il numero di file indicizzati, tempi e ~10 query: [QUERY_TEST_PLAN](homework-3/QUERY_TEST_PLAN.md), [REPORT_TEMPLATE](homework-3/REPORT_TEMPLATE.md).

## 7. Definition of Done

Una funzionalità è completata solo se: contratto implementato, invarianti coperti, test automatici verdi, errori osservabili, documentazione e ADR aggiornati. La verifica M1 riguarda le sole fondazioni; non dimostra ricerca, ingestione, atomicità di un repository o comportamento concorrente.

## 8. Accettazione delle decisioni v1

Le righe M1–M3 sono coperte dai test locali con i limiti M3 documentati (symlink reali e nomi distinti solo per case saltati su questo Windows; junction reale verificata). Le righe M4 sono coperte dalle fixture sintetiche e dalla pipeline multiformato ([evidenze](M4_VERIFICATION.md)); le righe M5 sono coperte con i limiti dei crash test documentati in [Verifica M5](M5_VERIFICATION.md). Le letture protette M5 sono verificate tramite acquisizioni esplicite nella stessa sessione; la concorrenza reale è verificata in M7. Le righe M6 sono verificate con i limiti in [Verifica M6](M6_VERIFICATION.md). Le righe M7 sono verificate con thread e processi reali su Windows ([evidenze](M7_VERIFICATION.md)); M8 è verificata con test Qt e smoke visivo, con i limiti di [Verifica M8](M8_VERIFICATION.md); M9 ha evidenze locali; Windows senza Python resta da verificare ([dettagli](M9_VERIFICATION.md)).

| Milestone | Scenario | Risultato atteso |
|---|---|---|
| M0 | OD-01…OD-23, link, prerequisiti | Copertura completa, nessun link locale rotto o dipendenza futura |
| M1 | Import domain/application | Nessun import di Qt, SQLite o parser; violazioni intercettate dal controllo |
| M2 | Report2026Finale.txt, HTTPServer.md | Token nome report/2026/finale e http/server; nessun suffisso indicizzato |
| M2 | l'acqua, caffè, caffe | Apostrofo separatore; accenti preservati; nessuna stop word rimossa |
| M2 | machine "deep learning" in content | Match se machine e frase adiacente sono nello stesso campo |
| M2 | machine nel nome, deep learning nel contenuto | Nessun match BOTH della query mista |
| M2 | Query vuota, "", sola punteggiatura, virgolette aperte | InvalidInput, nessuna clausola silenziosamente scartata |
| M2 | Query txt su Report.txt con contenuto vuoto | Nessun match nome per la sola estensione |
| M3 | UTF-8 con BOM / byte non validi | BOM rimosso / job fallito senza candidato parziale |
| M3 | Basename duplicati, case/Unicode distinti, hard link | Identità per percorso, nessuna fusione distruttiva |
| M3 | Root link, file symlink, junction/reparse point | Radice link rifiutata; discovery non attraversa i link |
| M4 | Markdown vuoto dopo esclusioni | Documento valido, ricercabile per nome |
| M4 | Front matter chiuso/non chiuso e token HTML | Esclusione secondo policy, nessuna esecuzione HTML o accesso URL |
| M4 | PDF misto, whitespace-only, con password necessaria | Testo disponibile / EXCLUDED / FAILED |
| M5 | Round-trip catalogo/testo/posting | Stessi contenuti e risultati, nessuna rilettura sorgenti |
| M5 | Arresto prima/durante/dopo commit | Vecchio o nuovo snapshot completo; RAM riallineata al persistito al restart |
| M5 | Errore scrittura, disco pieno, ResourceFailure simulato | Nessun riferimento a candidato parziale |
| M5–M7 | Tre versioni e lettura ancora su N | N protetta fino al rilascio; poi SnapshotUnavailable se eliminata |
| M6 | NO_CHANGES | Stesso snapshot_id; ultimo controllo operativo aggiornato |
| M6 | Schema/processing incompatibile, sorgente presente/assente | Rebuild / errore; mai ricerca incompatibile, vecchi dati preservati fino al successo |
| M6 | Crash durante rebuild di schema fisico | Vecchio database preservato finché il riferimento non seleziona quello nuovo completo |
| M6 | Cambio A→B→A | Nessun risultato della directory errata, A reindicizzata al ritorno |
| M6 | ClearLocalData durante job | Richiesta rifiutata, nessuna pulizia avviata |
| M6 | ClearLocalData, anche con errore di cancellazione | Solo dati app rimossi; errore osservabile e ripetibile, sorgenti intatti |
| M7 | Sync sovrapposti / seconda istanza | Stesso job_id e reused=true / rifiuto accesso storage |
| M7 | Chiusura normale / kill durante job | Attesa del job / recovery e lock rilasciato dal sistema |
| M8 | Query lenta seguita da altra query/cambio cartella | Risposta superata non sovrascrive lo stato corrente |
| M8 | Invio, paginazione, polling, check | Ricerca esplicita, pagine 50, polling 200 ms, check 1,5 s |
| M8 | Pagina successiva sullo stesso snapshot N | Offset richiesto mantenuto, ordine e totale riferiti a N |
| M8 | Pagina successiva restituisce N+1 dopo lista su N | Risposta scartata; stessa query/campo ripetuta con offset=0, lista e totale dalla nuova prima pagina |
| M8 | Cambio query/campo/directory durante ritorno alla prima pagina | Risposta precedente ignorata, nessuna sovrascrittura dello stato corrente |
| M8 | Query senza match / offset oltre il totale | Lista vuota e snapshot_id valido; totale 0 / totale effettivo; cambio versione applica comunque il ritorno alla prima pagina |
| M8 | Apri file assente / anteprima versione rimossa | Messaggio e proposta Sync / invito a ripetere ricerca |
| M8 | Build/query/anteprima sotto carico | UI utilizzabile, nessun lavoro pesante nel thread grafico |
| M9 | ZIP su Windows 11 x64 pulito, account standard | Avvio senza Python, indicizzazione, ricerca, restart e pulizia funzionanti |

## 9. Misure e verifica della consegna

Generare un corpus sintetico deterministico di alcune migliaia di documenti e decine di MB di testo;
registrare seed/configurazione, formati, dimensioni, hardware e versioni. Nessun dato personale.
Misurare memoria massima del processo, tempo build iniziale, caricamento, no-change sync,
sync incrementale e query. Distinguere tempi di estrazione, analisi e commit dove misurabili.
Nessuna soglia quantitativa prestazionale è stata approvata; pubblicare risultati e limiti reali.
Ripetere i percorsi di accettazione sul pacchetto distribuito; conservare log sintetici e istruzioni.
La verifica documentale non sostituisce questi test. Non segnare M1–M9 complete prima delle evidenze.
