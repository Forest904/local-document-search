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

## Candidato e prove locali

Candidato da revisione pulita `3b78203e6cfbb3be1b01d8bed82728c45b56ab00`.
CI GitHub `Backend and desktop`, run `42522632704`: **success** su Windows e
Ubuntu. Build `./scripts/package/build.ps1 -Release` completata con CPython
3.12.2, MSVC 2022 e Inno Setup 6.7.3. Installer
`LocalDocumentSearch-0.2.0-windows-x64-setup.exe`, SHA-256
`a13f53a76e6ef8a09f8efb023c6b32c4702f1b74ae699198b220e7e34dd883b3`.
Manifest con `dirty_worktree=false`, 319 file inventariati e 319 hash verificati
senza differenze nello staging e nell'installazione. Il file `.manifest.json`
esterno corrisponde all'hash dell'installer. La reinstallazione silenziosa sul
laptop ha restituito exit 0, senza riavvio. Diagnostica smoke dall'EXE installato:
`PASS`, un ciclo, due campioni; avvio UI con `LOCALAPPDATA` isolato rimasto
attivo per cinque secondi senza creare storage prima dell'informativa.
Il 9 novembre, in una prova interattiva dello stesso EXE installato su un altro
`LOCALAPPDATA` temporaneo, l'informativa è stata accettata, il corpus sintetico
M9 da 12 TXT/MD/PDF è stato indicizzato, `corpus comune` ha restituito **12
risultati** con estratti e il clic sul primo TXT ha aperto
`NomeSolo00000.txt` in Blocco note con il testo previsto. Questa prova non
copre apertura MD/PDF, carico o accessibilità con Narrator.

T08 dal pacchetto compilato sul laptop Windows 11 build 26200, Ryzen AI 7 350,
32 GB RAM, SSD WD SN5000S, Balanced e batteria in carica: corpus target
10.000 file, 299.948.099 byte estratti, tre cicli indipendenti, cinque warm-up
e cento campioni/query. Il run finale `report.json` è `PASS` con
`budget_status=PASS`: massimi build **215,01 s**, avvio fino alla ricerca
**9,53 s**, no-change **0,781 s**, sync 100/100/100 **5,04 s**, query p95
**97,52 ms**, working set **1.359,1 MiB**. Cache OS non svuotata e processi
nuovi per fase. Report grezzo in `%TEMP%/lds-v2-08-packaged-target-final/output/`.

Un run precedente dello stesso commit è stato interrotto dopo un ciclo
completo: il suo report resta `INCOMPLETE` e quel ciclo aveva p95 **103,48 ms**
per `"frasecomune consecutiva"` nel contenuto, sopra il budget di 100 ms.
Un ulteriore run da due cicli è `PASS` e `budget_status=PASS` (massimo p95
92,47 ms). I risultati indicano variabilità vicino al limite: il run finale
completo soddisfa T08, ma lo scostamento osservato rimane registrato.

La prova locale non include ancora wizard interattivo, apertura reale MD/PDF,
matrice reader/lifecycle sul programma installato, Narrator o PC pulito.
I report temporanei e i log di installazione restano fuori Git.

Kit copiato su chiavetta rimovibile `SANDISK`, percorso
`D:/LDS-V2-08-3b78203`: installer finale, `.sha256`, manifest, installer
0.2.0 precedente al candidato, installer 0.1.9 **solo di prova** per upgrade,
corpus e fixture sintetiche, scheda per il PC pulito e report benchmark.
`KIT-SHA256.txt` elenca 30 file: confronto SHA-256 con gli originali dopo la
copia, **0 differenze**. La lettera `D:` vale solo per il laptop di preparazione.
L'installazione e gli esiti sul PC pulito devono ancora essere restituiti
dall'utente prima di chiudere V2-08.

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
| T07 | PARZIALE locale | Estratti e apertura TXT reale; Unicode e MD/PDF sul pacchetto da provare |
| T08 | PASS locale con scostamento registrato | Run finale a tre cicli; p95 103,48 ms nel ciclo di un run interrotto |
| T09 | DA ESEGUIRE | Diff, A→B→A, rebuild, fault e recovery |
| T10 | DA ESEGUIRE | Cancel e pulizia rifiutata durante job |
| T11 | DA ESEGUIRE | Variazioni metadati durante ingestione |
| T12 | PARZIALE locale | Onboarding, indice e ricerca 12 risultati; carico e risposte obsolete da provare |
| T13 | DA ESEGUIRE | IT/EN, temi, DPI, tastiera, focus e Narrator |
| T14 | DA ESEGUIRE | Isolamento dati v1 e upgrade v2 |
| T15 | PARZIALE locale | Reinstallazione silenziosa exit 0; wizard/upgrade/downgrade e PC pulito da provare |
| T16 | DA ESEGUIRE | Disinstallazione con dati conservati/cancellati e lock |
| T17 | PARZIALE locale | Inventario e hash verificati; wizard, avvisi e offline su PC pulito da provare |
| T18 | PASS sorgente | CLI Homework senza Qt |
| T19 | PASS candidato locale | CI, commit pulito, manifest e hash dello stesso artefatto |
| T20 | PASS sorgente | Corpus sintetico riproducibile nella suite ordinaria |
| T21 | PASS sorgente opt-in | Corpus reale completo, 6 test mirati |
| M9-G01 | DA ESEGUIRE | Cambio directory e rebuild sul pacchetto |
| M9-G02 | DA ESEGUIRE | Pulizia rifiutata durante job sul pacchetto |
| M9-G03 | DA ESEGUIRE | Reader problematici sul pacchetto |
| M9-G04 | DA ESEGUIRE | Ricerca e apertura sotto carico sul pacchetto |
| M9-G05 | DA ESEGUIRE | Windows pulito senza tool di sviluppo |
| M9-G06 | DA ESEGUIRE | Account standard distinto |
| M9-G07 | PASS candidato locale | CI e artefatto da revisione pulita |

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
