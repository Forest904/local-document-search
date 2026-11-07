# V2-03 — confronto delle strutture e verifica retrieval

## Metodo e scelta V2-D02

`python experiments/compare_v2_vocab.py --output experiments/results/v2-03-vocab.json`
confronta il dizionario, una tupla ordinata cercata con `bisect` e un albero
binario bilanciato costruito sperimentalmente. Usa i 20.000 termini deterministici
di `experiments/v2_benchmark.py`, il vocabolario del carico V2-02. Ogni tempo
è la mediana di 100 operazioni (10 per build e ricostruzione), in µs. La memoria
è il picco incrementale `tracemalloc` durante la costruzione, dopo aver creato
la sorgente condivisa. Ricostruzione significa rifare la struttura dalle chiavi
già caricate; il caricamento SQLite è misurato separatamente dal runner T08.

Windows 11 build 26200, Python 3.12.2, Ryzen AI 7 350, 32 GB RAM, SSD WD
SN5000S; revisione di partenza `fa9f73eb72f17509a6bbfa401f58abc0ac35895c`,
working tree modificato. Cache OS non svuotata. Risultati grezzi fuori Git in
`experiments/results/v2-03-vocab.json`.

| Struttura | Build µs | Picco aggiuntivo byte | Lookup esatto µs | Prefisso selettivo µs | Prefisso ampio µs | Ricostruzione µs |
|---|---:|---:|---:|---:|---:|---:|
| Dizionario, scansione prefisso | 104,0 | 415.152 | 0,1 | 941,1 | 945,2 | 105,3 |
| Tupla ordinata, `bisect` | 168,8 | 320.040 | 0,1 tramite dizionario | 0,4 | 0,4 | 172,0 |
| Albero bilanciato | 3.180,0 | 1.439.656 | 0,5–0,6 | 1,2 | 3.658,5 | 3.684,6 |

La tupla è la scelta V2-D02: intervalli rapidi, minore memoria aggiuntiva e
ricostruzione più economica dell'albero. Il dizionario resta la via per i termini
esatti. Il confronto è un microbenchmark del vocabolario; non sostituisce T08 e
non prova da solo i costi su 10.000 documenti caricati da SQLite.

Il primo ciclo T08 dopo l'aggiunta dei prefissi ha mostrato p95 304,6 ms per
la frase comune e 272,7–287,4 ms per query con molti match, oltre il budget
100 ms. L'evaluator costruiva e ordinava tutti i risultati prima di applicare
la pagina da 50. Il percorso applicativo ora calcola il totale completo e
costruisce solo la pagina, usando l'ordine per percorso fissato nello snapshot.
Su un microbenchmark separato di 10.000 documenti sintetici, il percorso
dominio completo ha mediana 30,1 ms e p95 57,6 ms, contro 3,1 ms e 5,0 ms
per la sola prima pagina. Sono misure diagnostiche, non il gate T08.

## Verifica T03–T05, T08 e T18

Il runner `experiments/run_v2_benchmark.py` conserva il metodo V2-02 e aggiunge
tre prefissi e un caso di suggerimento. Controlla gli attesi dei prefissi con
i marcatori del generatore prima di misurare, cinque warm-up e cento campioni
mescolati deterministicamente per ciascuno dei tre cicli. Le query esatte
restano nel confronto, così come build, avvio, no-change, sync e memoria.

I test sintetici coprono campi, BOTH, frasi, snapshot, riapertura SQLite,
grammatica e limiti di 256/257 espansioni. La suite reale è opt-in e richiede
il corpus verificato.

Comando dalla radice: `python experiments/run_v2_benchmark.py run
experiments/results/v2-target-final experiments/results/v2-03-target-optimized
--cycles 3 --samples 100 --warmups 5`. Report grezzo fuori Git in
`experiments/results/v2-03-target-optimized/report.json`, stato `PASS` per
completezza e correttezza dei tre cicli. Corpus ID
`3d29323c75500f1fe2492691ac6b655c414d2c6478adb81b1b84ea37cea5a2ef`,
299.948.099 byte estratti per ciclo. Windows 11 build 26200, Python 3.12.2,
Ryzen AI 7 350, 32 GB RAM, SSD WD SN5000S, alimentazione Balanced e batteria
in carica; cache OS non svuotata, processo e storage nuovi per ciclo. Revisione
di partenza `fa9f73eb72f17509a6bbfa401f58abc0ac35895c`, working tree
modificato; non è una prova da revisione pulita o su pacchetto installato.

| Metrica | Ciclo 1 | Ciclo 2 | Ciclo 3 | Budget V2-D01 |
|---|---:|---:|---:|---:|
| Max query p95, ms | 36,5 | 35,3 | 34,4 | ≤100 |
| Build, s | 729,4 | 741,0 | 742,0 | ≤300 |
| Avvio fino a ricerca, s | 109,6 | 109,8 | 109,7 | ≤15 |
| Sync no-change, s | 0,708 | 0,764 | 0,709 | ≤1 |
| Sync 100/100/100, s | 256,9 | 258,4 | 263,7 | ≤60 |
| Picco working set, MiB | 4127 | 4126 | 4126 | ≤2560 |

**Gate retrieval V2-03 soddisfatto:** massimo dei p95 36,5 ms. I budget
build, avvio, sync incrementale e RAM non sono raggiunti: rimangono criteri
per V2-04 e V2-08, non sono convertiti in `PASS` dal report del runner. Il
no-change rientra nel budget. Rispetto alla baseline V2-02, i tempi di build,
avvio e sync sono tutti più alti in questa sessione; il metodo non isola una
causa, quindi non si attribuisce lo scarto alla nuova struttura.

Verifiche finali: `python -m pytest -q` da `backend/`: 351 passed, 6 skipped;
suite reale opt-in `test_v2_corpus.py` con corpus verificato: 6 passed;
`python experiments/run_homework3.py`: PASS. T03, T04, parte backend di T05
e T18 sono coperti. La digitazione nella UI appartiene a V2-06; storage fisico,
cancel e prova sul pacchetto appartengono alle milestone successive.
