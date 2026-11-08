# V2-04 — Storage e lifecycle

**Chiusura locale: 8 novembre 2026.** Revisione di partenza `7047752ee70e90dbbe4af3db82b180f5209e9e70`, working tree modificato; la revisione finale va registrata dopo il commit. Corpus e report grezzi restano fuori Git. La prova sul pacchetto installato resta V2-08.

## Implementazione e prove funzionali

`compose_v2_application` usa `%LOCALAPPDATA%/LocalDocumentSearchV2` e rifiuta uno storage v1 esplicito. SQLite v2 conserva manifest per snapshot e versioni immutabili di testo e posting per documento; i documenti invariati riusano la versione persistita. I posting sono JSON compresso con zlib e vengono convalidati alla riapertura. Lo staging viene riletto e confrontato con una digest dei record scritti prima del commit atomico. Il precedente della stessa directory è caricato su richiesta e le letture acquisite conservano la versione fino al rilascio.

La composizione v2 usa due processi reader con massimo quattro richieste in volo e un writer nel processo principale. Il job verifica `size` e `mtime_ns` prima e dopo ingestione; cancel prima del commit scarta il candidato e termina in `CANCELLED`, mentre la richiesta dopo l'inizio del commit è rifiutata. Rebuild e recupero del precedente richiedono un'operazione esplicita. La CLI Homework e la composizione persistente v1 non usano il nuovo formato.

Test sul sorgente: `python -m pytest -q` da `backend/`: **370 passed, 6 skipped**. La suite reale opt-in completa: **6 passed**; `python experiments/run_homework3.py`: **PASS**. I test v2 mirati coprono no-change, sync e riapertura, riuso e retention, cambio directory, pulizia rifiutata durante job, matrice reader, metadati variati, cancel prima e dopo staging, commit fallito, crash di processo prima del commit, corruzione del candidato, recovery e rebuild espliciti. I test frontend non sono stati raccolti in questo ambiente perché manca PySide6 (`ModuleNotFoundError`); la nuova UI e il collaudo installato appartengono a V2-06/V2-08.

## Budget V2-D01

Ambiente: Windows 11 build 26200, Python 3.12.2, Ryzen AI 7 350, 32 GB RAM, SSD WD SN5000S, profilo Balanced; cache OS non svuotata. Il runner usa il corpus sintetico V2-02, verifica gli hash, crea storage separato e processi nuovi per ciascuna fase. Small, adverse e target hanno **tre cicli `PASS`** ciascuno. Il target ha estratto **299.948.099 byte** per ciclo. La tabella riporta il massimo dei tre cicli; per le query, il massimo dei p95 nearest-rank di tutti i casi.

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
