# Test Strategy & Acceptance Plan

**Stato:** piano di verifica, nessun test implementato. I test dovranno dimostrare **correttezza** prima delle ottimizzazioni.

## 1. Livelli

| Livello | Focus | Esempi |
|---|---|---|
| Unit | Funzioni pure di dominio | Normalizzazione, token/posizioni, AND, phrase, termini ripetuti |
| Contract | Ogni adapter rispetta la porta | Reader con 3 esiti, scanner no symlink, repository atomic activate |
| Integration | Collaborazione dei moduli | Snapshot iniziale, sync con ADD/MODIFY/REMOVE, errore rollback |
| E2E | CLI e sistema completo | Indicizzazione `.txt`, query da console, persistenza tra sessioni |
| Experiments | Relazione Homework 3 | ~10 query, numero file, tempo indicizzazione, motivazioni analyzer |

## 2. Casi unitari obbligatori

- **Tokenization:** Unicode, accenti, punteggiatura, underscore, apostrofi, CamelCase se approvato; input vuoto; token ripetuti.
- **Positioning:** zero-based, posizioni crescenti, stesso termine ripetuto, nessun offset tra nome e contenuto.
- **AND:** tutte le parole nello stesso campo, ordine non vincolante, documenti con una sola parola.
- **Phrase:** `"roma tre"` trova `Roma Tre` ma non `Roma ... tre`; gestire `"data data"`, frase più lunga del documento.
- **BOTH:** `machine` nel filename e `learning` nel content **non** soddisfano query `machine learning` se nessun campo contiene entrambi.
- **Manifest:** entry INDEXED ↔ IndexedDocument ↔ posting; entry EXCLUDED senza postings.
- **ID:** uguale basename in cartelle differenti deve produrre documenti distinti.

## 3. Reader fixtures

- TXT UTF-8 valido, contenuto vuoto, encoding errato → FAILED.
- Markdown titolo/paragrafo, code fence escluso, link/tabelle nei termini definiti dal contratto finale.
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
| Crash prima di activate | Precedente attivo preservato (verifica dipendente dalla scelta storage) |
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

Una funzionalità è completata solo se: contratto implementato, invarianti coperti, test automatici verdi, errori osservabili, documentazione e ADR aggiornati. Lo scaffold presente non soddisfa ancora questa DoD.
