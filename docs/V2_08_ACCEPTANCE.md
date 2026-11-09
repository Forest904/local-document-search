# V2-08 — Registro di accettazione della release 0.2.0

Stato: **completato il 9 novembre 2026** sul candidato identificato da commit
pulito, SHA-256 dell'installer e manifest dello stesso payload. Le prove
storiche V2-07 e del redesign Luma non sono state trasferite automaticamente.

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

La prova interattiva locale descritta sopra non includeva wizard, apertura
MD/PDF, matrice reader/lifecycle o Narrator; questi casi sono stati verificati
separatamente sul PC pulito, come registrato sotto. I report temporanei e i
log di installazione restano fuori Git.

Kit copiato su chiavetta rimovibile `SANDISK`, percorso
`D:/LDS-V2-08-3b78203`: installer finale, `.sha256`, manifest, installer
0.2.0 precedente al candidato, installer 0.1.9 **solo di prova** per upgrade,
corpus e fixture sintetiche, scheda per il PC pulito e report benchmark.
`KIT-SHA256.txt` elenca 30 file: confronto SHA-256 con gli originali dopo la
copia, **0 differenze**. La lettera `D:` vale solo per il laptop di preparazione.
La scheda `RISULTATI.txt` compilata è stata restituita sulla stessa chiavetta.
La sua modifica rispetto a `KIT-SHA256.txt` è attesa: il kit fu inventariato
prima del collaudo. L'hash dell'installer è stato ricontrollato dopo il ritorno
e corrisponde al valore sopra; la scheda riporta inoltre la verifica sul PC
pulito come `si`, senza trascrivere il digest numerico.

## Collaudo sul PC pulito

Scheda restituita il 9 novembre 2026 per il candidato `3b78203`: Windows 11
build `26200.9445`, AMD Ryzen 5 2600X 3,60 GHz, 32 GB RAM, disco con 137 GB
usati su 466 GB. Account standard di test distinto e vergine, rete disconnessa,
Python e tool di sviluppo assenti. Nessun avviso Windows o errore segnalato.
I tempi di questo PC non sono stati misurati e non sono confrontati con il
benchmark del laptop di riferimento.

La scheda registra `PASS` per installazione, upgrade dall'installer 0.1.9 di
prova, reinstallazione 0.2.0, avvio e prima indicizzazione, TXT/MD/PDF e reader
problematici, ricerca/suggerimenti/filtri/pagine/apertura, cambio cartella,
rebuild, cancel, lock e recovery, IT/EN, temi, DPI, tastiera e Narrator,
disinstallazione con dati conservati e poi cancellati, sorgenti e dati v1
intatti. L'utente ha confermato in seguito i casi puntuali: TXT/MD vuoti,
PDF protetto/senza testo/misto, symlink/junction esclusi, pulizia rifiutata
durante job, snapshot precedente dopo errore e doppia istanza; flussi completi
con tastiera e Narrator per selezione cartella, ricerca, risultati, apertura,
Impostazioni, focus e dialoghi nelle due lingue e nei temi; blocco del
downgrade, termini IT/EN e sostituzione con DLL Qt ricostruita sul candidato.
Le conferme sono resoconti manuali dell'utente; la scheda raggruppa i casi
anziché registrarli uno per riga. Non sono stati segnalati fallimenti.

## Pubblicazione successiva

Il tag Git `v0.2.0` punta al commit candidato `3b78203`, non al successivo
commit di merge. La [Release GitHub v0.2.0](https://github.com/Forest904/local-document-search/releases/tag/v0.2.0)
distribuisce l'installer collaudato, il checksum e un manifest pubblico senza
percorsi assoluti del laptop. L'EXE è stato scaricato dalla Release: 158.370.246
byte e SHA-256 `a13f53a76e6ef8a09f8efb023c6b32c4702f1b74ae699198b220e7e34dd883b3`,
uguale all'originale sulla chiavetta. `/releases/latest` indirizza a `v0.2.0`.

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

`PASS sorgente` indica la suite della revisione candidata; `PASS PC pulito`
indica la scheda restituita e, per i dettagli non trascritti, la conferma
successiva dell'utente. Il benchmark compilato è distinto dalla UI manuale.

| Scenario | Stato | Evidenza |
|---|---|---|
| T01 | PASS PC pulito | Installazione e uso offline con account standard distinto, senza tool di sviluppo |
| T02 | PASS sorgente + PC pulito | Reader TXT/MD/PDF, vuoti e problematici; esclusione symlink/junction confermata |
| T03 | PASS sorgente | Suite backend: AND, frasi, BOTH e regressioni query esatte |
| T04 | PASS sorgente | Suite backend: vocabolari dopo build, update, restart e recovery |
| T05 | PASS sorgente + PC pulito | Prefissi per campo/snapshot nella suite; suggerimenti UI nel collaudo |
| T06 | PASS sorgente + PC pulito | Filtri/ranking/totali/pagine nella suite; filtri e pagine sul pacchetto |
| T07 | PASS sorgente + PC pulito | Snippet/highlight Unicode nella suite; estratti e apertura file sul pacchetto |
| T08 | PASS pacchetto, scostamento registrato | Tre cicli target entro budget; p95 103,48 ms in un ciclo del run interrotto, che resta INCOMPLETE |
| T09 | PASS sorgente + PC pulito | Diff, A→B→A e fault nella suite; cambio cartella, rebuild, snapshot precedente e recovery sul pacchetto |
| T10 | PASS sorgente + PC pulito | Cancel e commit nella suite; cancel e pulizia rifiutata durante job sul pacchetto |
| T11 | PASS sorgente | Variazione dei metadati durante ingestione; limite size+mtime identici documentato |
| T12 | PASS sorgente + PC pulito | Controller/QML e prova locale; ricerca e apertura sotto carico sul pacchetto, risposte obsolete nella suite |
| T13 | PASS PC pulito | IT/EN, temi, DPI, tastiera, focus, dialoghi e Narrator sui flussi principali |
| T14 | PASS sorgente + PC pulito | Isolamento v1 nella suite; upgrade e sorgenti/dati v1 intatti sul PC pulito |
| T15 | PASS PC pulito | Wizard, upgrade 0.1.9 di prova, reinstallazione, downgrade bloccato, avvio offline |
| T16 | PASS PC pulito | Disinstallazione con conservazione e cancellazione esplicita; lock e pulizia durante job |
| T17 | PASS candidato + PC pulito | Inventario/licenze/manifest, termini IT/EN, DLL Qt sostituita, assenza di avvisi e rete |
| T18 | PASS sorgente | CLI Homework senza Qt, runner PASS |
| T19 | PASS candidato | CI Windows/Ubuntu, commit pulito, manifest e hash dell'installer ricontrollato |
| T20 | PASS sorgente | Corpus sintetico riproducibile nella suite ordinaria |
| T21 | PASS sorgente opt-in | Corpus reale completo, 6 test mirati |
| M9-G01 | PASS PC pulito | Cambio directory e rebuild sul pacchetto |
| M9-G02 | PASS PC pulito | Pulizia rifiutata durante job sul pacchetto |
| M9-G03 | PASS PC pulito | PDF problematici e TXT/MD vuoti sul pacchetto |
| M9-G04 | PASS PC pulito | Ricerca e apertura sotto carico sul pacchetto |
| M9-G05 | PASS PC pulito | Windows pulito senza Python/tool di sviluppo, offline |
| M9-G06 | PASS PC pulito | Account standard distinto e vergine |
| M9-G07 | PASS candidato | CI e artefatto da revisione pulita |

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
