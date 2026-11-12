# Prestazioni e verifiche backend v2

## Revisione budget del 12 novembre 2026

La revisione approvata prima delle nuove misure comparative stabilisce p95 ≤100 ms per query esatte, wildcard ordinarie e suggerimenti, p95 ≤200 ms per `frasecom*` nel contenuto e no-change ≤2 s. Build 300 s, riapertura 15 s, sync 60 s e RAM 2560 MiB restano invariati. Il massimo di tre cicli determina il gate. Le tabelle storiche sotto mantengono i limiti precedenti; nessun risultato precedente è sovrascritto.

### Confronto compilato 0.2.1 / 0.2.2 del 12 novembre 2026

ZIP locali estratti: 0.2.1 revisione `637f1359390e0ce24f1862d599a80af098e8b037`, SHA-256 ZIP `0f85668cf97f907864410168b15e4b2beb3f6e115b432f2efdd1c7d86d122011`, EXE `7c96817d6aa50528a7c17ad3ca225f6043c37f4be12b627f7aff513def7323f5`; 0.2.2 revisione `4263029e218f60eed1f1fe32f21e70a7cf08bb1c`, SHA-256 ZIP `fc92f27798f25a72022079d19693e95032e202e6c60f987197adb5af878b1f23`, EXE `19feaffc84a478aef29ae518c770a4c83cb4a4959a58f766ffba7c0a535e53f1`. Non sono gli asset GitHub 0.2.1. I manifest degli installer locali dichiarano le medesime revisioni; i rispettivi SHA-256 installer sono `6cad46a5810950c9b5ac60140d3ac6451abe60bbe0b47e6a4b382bd495313dcc` e `70b8d0f7a983f4f7dbfad0122f1129d9ad2af1c49b84d3e36b1606867808c4b6`.

Corpus target V2-02, ID `db18e157aa72b9f8395a3f338a2caa7395447e83e32e40c63297ca11d5136c2a`; Windows 11 build 26200, Ryzen AI 7 350, 32 GB RAM, SSD WD SN5000S. Sequenza alternata 0.2.1→0.2.2, 0.2.2→0.2.1, 0.2.1→0.2.2: tre cicli/versione, copie e storage indipendenti, processi nuovi, cinque warmup e cento campioni/query. Alimentazione collegata per tutte le prove, batteria dal 73% al 99%, profilo Balanced; cache OS non svuotata. Non è stato campionato il carico concorrente, quindi la sua influenza residua non è quantificata. `sequence.json`, sei report originali, campioni e aggregati sono conservati localmente in `experiments/results/v2-021-022-comparison-20261112/`, esclusa da Git. Tutti i report singoli hanno `status=PASS`.

| Massimo di tre cicli | 0.2.1 | 0.2.2 | Differenza 0.2.2 − 0.2.1 | Budget |
|---|---:|---:|---:|---:|
| Build | 161,259 s | 144,245 s | −17,014 s (−10,6%) | ≤300 s |
| Riapertura | 6,640 s | 6,358 s | −0,282 s (−4,2%) | ≤15 s |
| No-change | 0,700 s | 0,713 s | +0,013 s (+1,8%) | ≤2 s |
| Sync incrementale | 3,394 s | 4,139 s | +0,745 s (+22,0%) | ≤60 s |
| Query esatte p95 | 54,287 ms | 97,799 ms | +43,512 ms (+80,2%) | ≤100 ms |
| Wildcard ordinarie p95 | 24,319 ms | 50,051 ms | +25,732 ms (+105,8%) | ≤100 ms |
| `frasecom*` contenuto p95 | 33,743 ms | 68,263 ms | +34,520 ms (+102,3%) | ≤200 ms |
| Suggerimenti p95 | 0,204 ms | 0,319 ms | +0,115 ms (+56,3%) | ≤100 ms |
| Working set | 1366,383 MiB | 1365,789 MiB | −0,594 MiB | ≤2560 MiB |

P95 massimi per ciclo, nell'ordine esatte / wildcard ordinarie / `frasecom*` / suggerimenti, in ms: 0.2.1 ciclo 1 `54,287 / 23,623 / 30,722 / 0,204`, ciclo 2 `49,198 / 22,760 / 32,675 / 0,175`, ciclo 3 `54,157 / 24,319 / 33,743 / 0,185`; 0.2.2 ciclo 1 `61,371 / 24,935 / 30,462 / 0,191`, ciclo 2 `97,799 / 50,051 / 68,263 / 0,319`, ciclo 3 `72,526 / 33,465 / 42,986 / 0,304`. Build dei sei cicli: `132,136 / 127,285 / 141,614 / 161,259 / 128,746 / 144,245 s` nell'ordine della sequenza.

Il secondo ciclo storico 0.2.2 arriva a 2,201 ms dal limite delle query esatte. Il candidato finale aggiornato ha maggiore margine, ma la differenza fra sessioni richiede cautela nel generalizzare i numeri ad altri PC o carichi.

Il peggioramento delle query rispetto alla 0.2.1 rimane senza causa accertata. Fra le due revisioni il backend non cambia e gli script diagnostici incorporati hanno SHA-256 identico; ciò non dimostra che runtime, scheduling e carico concorrente siano identici. La 0.2.2 storica aveva raggiunto 172,797 ms su `frasecom*` e 1,520 s no-change, mentre qui i massimi sono 68,263 ms e 0,713 s: la variazione fra sessioni è sostanziale. Le soglie revisionate accettano esplicitamente il rallentamento entro i limiti, con indagine futura non bloccante. La verifica di correttezza completa di `frasecom*` richiede il runner aggiornato nel candidato finale.

I runner incorporati nei due compilati storici verificano gli altri attesi completi e misurano `frasecom*`, ma non confrontano la lista completa di quel prefisso con l'atteso. Il candidato finale aggiunge tale controllo nel compilato; resta questo limite nella prova comparativa storica 0.2.1/0.2.2.

Profilazione diagnostica separata, eseguita sul sorgente corrente con gli storage dopo il sync dei cicli 0.2.1 e 0.2.2: `profile-021-nochange.txt/.pstats` e `profile-022-nochange.txt/.pstats` nella stessa directory locale. cProfile ha misurato rispettivamente 2,546 e 2,596 s nell'operazione no-change; la composizione ha impiegato 18,114 e 18,099 s, soprattutto nel caricamento snapshot. I tempi profilati hanno overhead marcato e non sono misure dei compilati né sostituiscono il gate. Una profilazione query sullo storage già sincronizzato è stata respinta dal controllo degli attesi (100 file rimossi): non è usata per attribuire la regressione. Per approfondire, profilare una copia dello storage prima del sync, misurare il carico concorrente e ripetere in condizioni controllate; le differenze osservate restano senza causa dimostrata.

La profilazione query ripetuta con storage sorgente fresco è in `profile-source-queries.txt/.pstats`, sempre fuori Git. Include la verifica completa di 10.000 risultati prima dei campioni: cProfile attribuisce a quella verifica circa 204 s su 222 s della fase, con costo concentrato nella generazione degli intervalli di evidenziazione. Non isola quindi il costo delle query campionate né spiega il divario fra compilati. Per una futura indagine servono profili per singolo caso campionato, separati dalla verifica completa, nelle due revisioni compilate e con carico concorrente monitorato.

### Candidato finale con diagnostica aggiornata

Build release pulita dal commit locale in worktree separato `800ff756012c96a31f27d3baf11fc459ebaf47a1`; ZIP SHA-256 `2bd51f8be58327f10c29133755be0ef7a787113455aa514d5f7c7e19b1b66610`, installer SHA-256 `be9ce4c280d73e7e108c6e41a6e658fa396dc53199a3c9810dcaf29f82fd38ab`. Il payload contiene il controllo completo degli attesi per `frasecom*`. Report compilato `experiments/results/v2-022-final-800ff75/report.json` (SHA-256 `f78dc9abe5688f0dd550abd3d8f101fcb4ae34cf56d66b1bfdc6160ae2283a6e`), fuori Git: stesso corpus target, tre cicli, cinque warmup e cento campioni; `status=PASS`, `budget_status=PASS`, cinque fasi complete per ciclo. Profilo Balanced, alimentazione collegata; cache OS non svuotata.

Installer, ZIP, manifest e checksum del candidato sono conservati in `dist/candidates/800ff756/`, fuori Git, senza sovrascrivere gli artefatti storici. Gli hash delle copie sono stati ricontrollati.

Massimi dei tre cicli: build **131,868 s**, riapertura **5,705 s**, no-change **0,617 s**, sync **3,140 s**; p95 esatte **55,684 ms**, wildcard ordinarie **22,338 ms**, `frasecom*` **29,058 ms**, suggerimenti **0,199 ms**; working set **1.432.920.064 byte**. Tutti i budget rivisti sono rispettati. L'accettazione prestazionale T08 è chiusa per questo artefatto identificato, con il rallentamento storico non spiegato registrato come limite accettato. Il collaudo del nuovo installer e l'accessibilità nativa restano gate separati per la dichiarazione complessiva «production ready».

Evidenze storiche V2-02–V2-05: ogni sezione identifica revisione, ambiente e limiti. Il collaudo del binario distribuito è nel [registro V2-08](V2_08_ACCEPTANCE.md). Corpus e report grezzi restano fuori Git.

## V2-02

**Stato:** tre profili misurati; budget V2-D01 approvati il 7 novembre 2026. Questa relazione riguarda il backend da sorgente della revisione `9766bb274dfcbd5e8bb0cd865b1fce5a40efe766` con working tree modificato. I report grezzi e i corpus restano fuori Git.

### Ambiente e carico

- Windows 11 Home, build 26200; Python 3.12.2; `pypdf` 7.0.0 e
  `markdown-it-py` 4.2.0.
- AMD Ryzen AI 7 350 (8 core, 16 thread), RAM fisica 33.598.853.120 byte,
  SSD WD PC SN5000S da circa 1 TB. Batteria al 100% e in carica alla verifica; profilo energetico Windows `Balanced` (GUID `381b4222-f694-41f0-9685-ff5bb260df2e`).
- Seed 20261107. TXT/MD/PDF alternati; 20.000 termini sintetici, con frequenze
  non uniformi e marcatori deterministici. Profili: small 100 file/0,3 MB, adverse 1.000/30 MB, target 10.000/300 MB di testo atteso.
- Target generato: 315.458.322 byte di sorgenti e 299.923.100 byte di testo
  previsto. Il volume effettivamente estratto è verificato dal runner entro ±1% del target; il solo valore previsto non prova l'ingestione.

### Metodo

Comandi principali eseguiti dalla radice del repository (profili small e adverse analoghi, con i rispettivi nomi):

```powershell
python experiments/v2_benchmark.py generate experiments/results/v2-target-final --profile target
python experiments/v2_benchmark.py verify experiments/results/v2-target-final
python experiments/run_v2_benchmark.py run experiments/results/v2-target-final experiments/results/v2-target-final-run2 --cycles 3
python experiments/run_v2_benchmark.py summary experiments/results/v2-target-final-run2/report.json
```

Verifiche: backend **327 passed, 6 skipped**, Homework **PASS**, T08 mirata **5 passed**. Manifest e report registrano seed, hash, dimensioni, revisione/stato dirty, ambiente e campioni.

Metodo comune: [T08](TEST_STRATEGY.md#metodo-e-criteri) e [comandi del runner](../experiments/README.md#v2-02-corpus-e-benchmark-prestazionale). Tre cicli con copie e storage indipendenti; nuovi processi per fase; cinque warm-up e cento campioni/query, pagina 50, p95 nearest-rank. Liste complete verificate prima dei campioni; tempi di copie e controlli esclusi. Cache OS non svuotata. Il profiler separato misura durate inclusive e aggrega lookup/intersezione/frasi: non isola ogni costo né fornisce tempi di riferimento.

### Risultati

Small (corpus ID `8c00fa957a4b3e10f8a529cfb2f33406c52352a693e130931bc010d771740058`) e adverse (corpus ID `c02dcaae51638d8c061b2436d656b5e18d33ac2ee7af092901c4eb43e678ad61`) hanno report `PASS` di tre cicli. I valori sono in secondi, nell'ordine dei cicli; RAM è il massimo working set della fase, in MiB arrotondati.

| Profilo | Build | Avvio fino a ricerca | No-change | Incrementale | Max query p95 | Max RAM |
|---|---|---|---|---|---|---|
| Small, 100 | 0,550 / 0,365 / 0,368 | 0,380 / 0,359 / 0,346 | 0,009 / 0,009 / 0,008 | 0,158 / 0,169 / 0,160 | 0,000541 | 53 MiB |
| Adverse, 1.000 | 42,518 / 42,076 / 41,592 | 6,321 / 6,302 / 6,259 | 0,052 / 0,069 / 0,050 | 12,448 / 12,253 / 12,406 | 0,005272 | 469 MiB |

Il backend ha estratto rispettivamente 299.590 e 29.994.709 byte in ciascun ciclo. Il sync automatico dopo riapertura impiega circa 0,020 s su small e 0,062 s su adverse; il costo di caricamento è molto maggiore. La profilazione di small, effettuata separatamente, attribuisce circa 0,37 s ai reader, 0,17 s all'aggiunta nell'indice e 0,23 s alla persistenza, con overhead del profiler e durata inclusiva.

Il target (corpus ID `3d29323c75500f1fe2492691ac6b655c414d2c6478adb81b1b84ea37cea5a2ef`) ha completato tre cicli `PASS`, ciascuno con 299.948.099 byte di testo estratto. I valori sono in secondi; il massimo query p95 è quello della frase frequente nel contenuto. RAM è il massimo working set, in MiB.

| Metrica target | Ciclo 1 | Ciclo 2 | Ciclo 3 | Mediana | Intervallo |
|---|---:|---:|---:|---:|---:|
| Build iniziale | 439,040 | 433,009 | 440,126 | 439,040 | 7,117 |
| Avvio fino a ricerca | 70,346 | 68,973 | 70,584 | 70,346 | 1,611 |
| Sync automatico dopo riapertura | 0,443 | 0,439 | 0,451 | 0,443 | 0,012 |
| Sync no-change | 0,425 | 0,438 | 0,435 | 0,435 | 0,013 |
| Sync incrementale 100/100/100 | 161,723 | 161,368 | 162,170 | 161,723 | 0,802 |
| Max query p95 | 0,2474 | 0,2474 | 0,2442 | 0,2474 | 0,0032 |
| Picco RAM build (MiB) | 4101 | 4101 | 4101 | 4101 | 0 |
| Picco RAM sync incrementale (MiB) | 4125 | 4123 | 4123 | 4123 | 2 |

Lo storage dopo build è 3,612 GB; dopo il sync 7,216–7,271 GB. Build, caricamento e sync restano costosi; query selettive sotto 0,004 s p95, quelle comuni più lente. Il metodo non isola causalità per componente.

### Budget approvati V2-D01

Budget V2-D01 sul target e sull’hardware indicato: massimo dei tre cicli, massimo p95 fra tutte le query e massimo working set. Sono obiettivi, non risultati della baseline v1.

| Metrica | Baseline peggiore | Budget approvato | Motivo |
|---|---:|---:|---|
| Query p95 | 247 ms | ≤ 100 ms | Risposta interattiva anche per query comuni |
| Avvio fino a ricerca disponibile | 70,6 s | ≤ 15 s | Riapertura utilizzabile senza lunga attesa |
| Build iniziale | 440,1 s | ≤ 300 s | Ridurre il costo del primo indice a 5 minuti |
| Sync incrementale 100/100/100 | 162,2 s | ≤ 60 s | Limitare l'attesa di aggiornamento |
| Sync no-change | 0,438 s | ≤ 1 s | Margine per i controlli v2 senza regressione rilevante |
| Picco RAM working set | 4125 MiB | ≤ 2560 MiB | Ridurre l'impronta su PC con 8 GB RAM |

Limiti comuni V2-02–04: sorgente con working tree modificato, cache OS non svuotata e corpus sintetico. Non provano cache fredda, PDF arbitrari, altri carichi/hardware o il binario installato. Tre cicli descrivono variabilità locale; errore/timeout resta incompleto. La verifica del pacchetto è in [V2-08](V2_08_ACCEPTANCE.md).

## V2-03

### Metodo e scelta V2-D02

`python experiments/compare_v2_vocab.py --output experiments/results/v2-03-vocab.json` confronta il dizionario, una tupla ordinata cercata con `bisect` e un albero binario bilanciato costruito sperimentalmente. Usa i 20.000 termini deterministici di `experiments/v2_benchmark.py`, il vocabolario del carico V2-02. Ogni tempo è la mediana di 100 operazioni (10 per build e ricostruzione), in µs. La memoria è il picco incrementale `tracemalloc` durante la costruzione, dopo aver creato la sorgente condivisa. Ricostruzione significa rifare la struttura dalle chiavi già caricate; il caricamento SQLite è misurato separatamente dal runner T08.

Stesso ambiente V2-02, base `fa9f73eb72f17509a6bbfa401f58abc0ac35895c` con working tree modificato; grezzi in `experiments/results/v2-03-vocab.json`.

| Struttura | Build µs | Picco aggiuntivo byte | Lookup esatto µs | Prefisso selettivo µs | Prefisso ampio µs | Ricostruzione µs |
|---|---:|---:|---:|---:|---:|---:|
| Dizionario, scansione prefisso | 104,0 | 415.152 | 0,1 | 941,1 | 945,2 | 105,3 |
| Tupla ordinata, `bisect` | 168,8 | 320.040 | 0,1 tramite dizionario | 0,4 | 0,4 | 172,0 |
| Albero bilanciato | 3.180,0 | 1.439.656 | 0,5–0,6 | 1,2 | 3.658,5 | 3.684,6 |

La tupla è la scelta V2-D02: intervalli rapidi, minore memoria aggiuntiva e ricostruzione più economica dell'albero. Il dizionario resta la via per i termini esatti. Il confronto è un microbenchmark del vocabolario; non sostituisce T08 e non prova da solo i costi su 10.000 documenti caricati da SQLite.

Il primo ciclo T08 dopo l'aggiunta dei prefissi ha mostrato p95 304,6 ms per la frase comune e 272,7–287,4 ms per query con molti match, oltre il budget 100 ms. L'evaluator costruiva e ordinava tutti i risultati prima di applicare la pagina da 50. Il percorso applicativo ora calcola il totale completo e costruisce solo la pagina, usando l'ordine per percorso fissato nello snapshot. Su un microbenchmark separato di 10.000 documenti sintetici, il percorso dominio completo ha mediana 30,1 ms e p95 57,6 ms, contro 3,1 ms e 5,0 ms per la sola prima pagina. Sono misure diagnostiche, non il gate T08.

### Verifica T03–T05, T08 e T18

Il runner conserva il metodo V2-02, aggiungendo tre prefissi e un suggerimento con attesi dai marcatori del generatore. Le query esatte e le fasi di build, avvio, no-change, sync e memoria restano nel confronto.

I test sintetici coprono campi, BOTH, frasi, snapshot, riapertura SQLite, grammatica e limiti di 256/257 espansioni. La suite reale è opt-in e richiede il corpus verificato.

Comando dalla radice: `python experiments/run_v2_benchmark.py run experiments/results/v2-target-final experiments/results/v2-03-target-optimized --cycles 3 --samples 100 --warmups 5`. Report grezzo fuori Git in `experiments/results/v2-03-target-optimized/report.json`, stato `PASS` per completezza e correttezza dei tre cicli. Corpus ID `3d29323c75500f1fe2492691ac6b655c414d2c6478adb81b1b84ea37cea5a2ef`, 299.948.099 byte estratti per ciclo. Ambiente e revisione sono quelli indicati sopra, Balanced e batteria in carica; non è una prova da revisione pulita o su pacchetto installato.

| Metrica | Ciclo 1 | Ciclo 2 | Ciclo 3 | Budget V2-D01 |
|---|---:|---:|---:|---:|
| Max query p95, ms | 36,5 | 35,3 | 34,4 | ≤100 |
| Build, s | 729,4 | 741,0 | 742,0 | ≤300 |
| Avvio fino a ricerca, s | 109,6 | 109,8 | 109,7 | ≤15 |
| Sync no-change, s | 0,708 | 0,764 | 0,709 | ≤1 |
| Sync 100/100/100, s | 256,9 | 258,4 | 263,7 | ≤60 |
| Picco working set, MiB | 4127 | 4126 | 4126 | ≤2560 |

**Retrieval V2-03 entro budget**, come il no-change; build, avvio, sync incrementale e RAM fuori budget. Il PASS del runner indica completezza/correttezza, non conformità a tutti i limiti. Il metodo non attribuisce il peggioramento rispetto a V2-02 alla sola struttura nuova.

Verifiche finali: `python -m pytest -q` da `backend/`: 351 passed, 6 skipped; suite reale opt-in `test_v2_corpus.py` con corpus verificato: 6 passed; `python experiments/run_homework3.py`: PASS. T03, T04, parte backend di T05 e T18 sono coperti. La digitazione nella UI appartiene a V2-06; storage fisico, cancel e prova sul pacchetto appartengono alle milestone successive.

## V2-04

**Chiusura locale: 8 novembre 2026.** Revisione di partenza `7047752ee70e90dbbe4af3db82b180f5209e9e70`, working tree modificato; la revisione finale va registrata dopo il commit. Corpus e report grezzi restano fuori Git. La prova sul pacchetto installato resta V2-08.

### Implementazione e prove funzionali

Storage separato v2 con riuso di versioni immutabili e posting zlib, staging riletto/confrontato tramite digest prima del commit. Due processi reader, massimo quattro richieste in volo e un writer. Cancel, controllo metadati, rebuild/recovery espliciti e isolamento v1 verificati; [contratto corrente](ARCHITECTURE.md#snapshot-e-sincronizzazione).

Test sul sorgente: `python -m pytest -q` da `backend/`: **370 passed, 6 skipped**. La suite reale opt-in completa: **6 passed**; `python experiments/run_homework3.py`: **PASS**. I test v2 mirati coprono no-change, sync e riapertura, riuso e retention, cambio directory, pulizia rifiutata durante job, matrice reader, metadati variati, cancel prima e dopo staging, commit fallito, crash di processo prima del commit, corruzione del candidato, recovery e rebuild espliciti. I test frontend non sono stati raccolti in questo ambiente perché manca PySide6 (`ModuleNotFoundError`); la nuova UI e il collaudo installato appartengono a V2-06/V2-08.

### Budget V2-D01

Stesso ambiente/metodo V2-02, Balanced. Small, adverse e target: **tre cicli PASS** ciascuno; target **299.948.099 byte estratti** per ciclo. Tabella: massimo dei tre cicli e dei p95 di tutti i casi.

| Metrica target | Massimo V2-04 | Budget |
|---|---:|---:|
| Build iniziale | 143,801 s | ≤300 s |
| Avvio processo fino a ricerca disponibile | 8,243 s | ≤15 s |
| Sync incrementale 100/100/100 | 9,368 s | ≤60 s |
| Sync no-change | 0,472 s | ≤1 s |
| Query p95 | 22,6 ms | ≤100 ms |
| RAM, massimo working set del processo principale | 1296 MiB | ≤2560 MiB |
| RAM, albero dei processi campionato | 1353 MiB | ≤2560 MiB |

Lo storage dopo build è 364.134.400 byte (347 MiB), contro circa 3,612 GB nella baseline V2-02; dopo sync è 366.551.040 byte. Il campionamento dell'albero include il writer e i reader figli ogni 500 ms durante build e sync; non è una misura esatta del picco tra campioni. Il picco del processo principale è fornito dal contatore Windows del runner. Anche l'albero campionato resta ampiamente sotto budget. I tre cicli small hanno build massimo 0,858 s; adverse 14,477 s. Le misure descrivono questo hardware e la cache osservata, non il pacchetto installato né un avvio a cache fredda.

Comandi dalla radice del repository:

```powershell
python experiments/run_v2_benchmark.py run experiments/results/v2-small experiments/results/v2-04-small-final --cycles 3
python experiments/run_v2_benchmark.py run experiments/results/v2-adverse experiments/results/v2-04-adverse-final --cycles 3
python experiments/run_v2_benchmark.py run experiments/results/v2-target-final experiments/results/v2-04-target-accepted --cycles 3
python experiments/run_v2_benchmark.py summary experiments/results/v2-04-target-accepted/report.json
```

Il report finale è `experiments/results/v2-04-target-accepted/report.json`; il campionamento dell'albero è in `experiments/results/v2-04-tree-memory-accepted.json`. Le prove esplorative precedenti non sono usate come evidenza del gate. Modifiche del sorgente che conservano dimensione e `mtime_ns` possono restare invisibili fino a un rebuild; non sono previsti hash dei sorgenti né controlli filesystem durante la ricerca.

## V2-05

Chiusura locale dell’8 novembre 2026, base `b91e2a33ff2de8faf08f4dcadb7314f92576fb83` con working tree modificato: backend **380 passed, 6 skipped**, corpus reale opt-in mirato **6 passed**, Homework **PASS**. Filtri, ranking su posting, snippet/highlight Unicode e richieste per snapshot implementati; V2-D05/D06 risolte in [ADR 0010](adr/0010-v2-retrieval.md). T05–T07/T18 coperti sul backend.

Probe small: 100 file, 299.521 byte estratti, un ciclo, 10 campioni/query e 2 warm-up; **PASS**, peggior p95 18,7 ms. Comando dalla root:

```powershell
python experiments/run_v2_benchmark.py run experiments/results/v2-small experiments/results/v2-05-small-probe-fast --cycles 1 --samples 10 --warmups 2
```

Report locale fuori Git; prova limitata al backend, non al target 10.000/300 MB o al pacchetto. La revisione di base con modifiche locali non identifica un commit finale riproducibile.
