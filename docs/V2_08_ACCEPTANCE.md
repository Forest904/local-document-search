# V2-08 — Registro di accettazione della release 0.2.0

Stato: **aperto**. Il candidato deve essere identificato da commit pulito,
SHA-256 dell'installer e manifest dello stesso payload. Le prove storiche V2-07
e del redesign Luma non sono trasferite automaticamente.

Verifiche sul sorgente prima del commit candidato (Windows 11 build 26200,
CPython 3.12.2): suite congiunta backend/frontend/script **461 passed,
6 skipped**; corpus reale completo opt-in mirato **6 passed**; runner Homework
**PASS**; `pip check` **PASS**. Il runner V2-02 su corpus smoke, un ciclo e due
campioni, ha prodotto `PASS` con revisione di base `05e9c2a` e working tree
modificato: è solo un controllo funzionale del runner, non T08 né prova del
pacchetto. Report locali in `experiments/results/`, fuori Git.

## Procedura del candidato

1. Da branch dedicato e revisione pulita eseguire suite backend, frontend,
   script, Homework e corpus reale completo; acquisire commit e risultati CI.
2. Costruire con `./scripts/package/build.ps1 -Release`; verificare hash
   dell'installer e file del payload rispetto al manifest, licenze e risorse.
3. Generare `small`, `adverse` e `target` con `experiments/v2_benchmark.py`.
   Sul programma installato eseguire la diagnostica secondo
   [README packaging](../scripts/package/README.md). Per T08 usare tre cicli,
   cinque warm-up, cento campioni e il target 10.000/300 MB.
4. Usare `experiments/m9_corpus.py` e `error_fixtures()` per i casi reader;
   verificare separatamente directory/rebuild, lock, cancel, errori, recovery,
   query, suggerimenti, filtri, pagine, apertura e UI sotto carico. Usare solo
   directory sintetiche e storage di prova; registrare screenshot e log fuori Git.
5. Copiare sulla chiavetta installer, `.sha256`, `.manifest.json`, corpus sintetico,
   installer precedente identificato e scheda esiti. Ricalcolare gli hash sulla
   chiavetta. Sul PC pulito usare account standard senza Python/tool di sviluppo,
   rete disconnessa, e annotare versione Windows, hardware e avvisi osservati.

## Matrice dei gate

`DA ESEGUIRE` indica assenza di evidenza sul candidato finale; le prove sul
sorgente o su payload precedenti restano riferimenti, non PASS del candidato.

| Scenario | Stato candidato | Evidenza richiesta |
|---|---|---|
| T01 | DA ESEGUIRE | Installazione e uso offline su PC pulito/account distinto |
| T02 | DA ESEGUIRE | Matrice TXT/MD/PDF, file vuoti, protetti, misti, esclusioni/errori |
| T03 | DA ESEGUIRE | AND, frasi, BOTH e regressioni esatte |
| T04 | DA ESEGUIRE | Vocabolari dopo build/update/restart/recovery |
| T05 | DA ESEGUIRE | Prefissi e suggerimenti per snapshot e UI |
| T06 | DA ESEGUIRE | Filtri, ranking, totali e pagine |
| T07 | DA ESEGUIRE | Snippet, Unicode e apertura diretta |
| T08 | DA ESEGUIRE | Report compilato target, tre cicli e budget V2-D01 |
| T09 | DA ESEGUIRE | Diff, A→B→A, rebuild, fault e recovery |
| T10 | DA ESEGUIRE | Cancel e pulizia rifiutata durante job |
| T11 | DA ESEGUIRE | Variazioni metadati durante ingestione |
| T12 | DA ESEGUIRE | UI Luma responsiva sotto carico e risposte obsolete |
| T13 | DA ESEGUIRE | IT/EN, temi, DPI, tastiera, focus e Narrator |
| T14 | DA ESEGUIRE | Isolamento dati v1 e upgrade v2 |
| T15 | DA ESEGUIRE | Wizard IT/EN, reinstallazione, downgrade, runtime offline |
| T16 | DA ESEGUIRE | Disinstallazione con dati conservati/cancellati e lock |
| T17 | DA ESEGUIRE | Termini, inventario, sorgenti Qt, avvisi e offline |
| T18 | DA ESEGUIRE | CLI Homework senza Qt |
| T19 | DA ESEGUIRE | CI, commit pulito, manifest e hash dello stesso artefatto |
| T20 | DA ESEGUIRE | Corpus sintetico riproducibile |
| T21 | DA ESEGUIRE | Corpus reale completo opt-in |
| M9-G01 | DA ESEGUIRE | Cambio directory e rebuild sul pacchetto |
| M9-G02 | DA ESEGUIRE | Pulizia rifiutata durante job sul pacchetto |
| M9-G03 | DA ESEGUIRE | Reader problematici sul pacchetto |
| M9-G04 | DA ESEGUIRE | Ricerca e apertura sotto carico sul pacchetto |
| M9-G05 | DA ESEGUIRE | Windows pulito senza tool di sviluppo |
| M9-G06 | DA ESEGUIRE | Account standard distinto |
| M9-G07 | DA ESEGUIRE | CI e artefatto da revisione pulita |

## Scheda per il PC pulito

Annotare commit candidato, hash installer e hash verificato dopo la copia;
Windows build, CPU, RAM, disco, account standard, rete spenta e presenza di
Python/tool di sviluppo. Per ogni caso registrare `PASS`, `FAIL` o `NON ESEGUITO`,
passi riproducibili, messaggi e avvisi Windows. Installare 0.2.0, indicizzare
TXT/MD/PDF sintetici, cercare e aprire; provare aggiornamento da installer
precedente identificato, reinstallazione, downgrade e disinstallazione con
conservazione e poi cancellazione esplicita dei dati. Controllare che i sorgenti
di prova e gli eventuali dati v1 sintetici rimangano intatti. Riportare i tempi
del PC fisso separati da quelli del laptop di riferimento.
