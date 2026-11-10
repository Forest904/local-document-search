# Prestazioni e verifiche backend v2

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
