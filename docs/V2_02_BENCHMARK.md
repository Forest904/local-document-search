# V2-02 — Metodo e baseline prestazionale

**Stato:** tre profili misurati; budget V2-D01 approvati il 7 novembre 2026. Questa relazione riguarda
il backend da sorgente della revisione `9766bb274dfcbd5e8bb0cd865b1fce5a40efe766`
con working tree modificato. I report grezzi e i corpus restano fuori Git.

## Ambiente e carico

- Windows 11 Home, build 26200; Python 3.12.2; `pypdf` 7.0.0 e
  `markdown-it-py` 4.2.0.
- AMD Ryzen AI 7 350 (8 core, 16 thread), RAM fisica 33.598.853.120 byte,
  SSD WD PC SN5000S da circa 1 TB. Batteria al 100% e in carica alla verifica;
  profilo energetico Windows `Balanced` (GUID `381b4222-f694-41f0-9685-ff5bb260df2e`).
- Seed 20261107. TXT/MD/PDF alternati; 20.000 termini sintetici, con frequenze
  non uniformi e marcatori deterministici. Profili: small 100 file/0,3 MB,
  adverse 1.000/30 MB, target 10.000/300 MB di testo atteso.
- Target generato: 315.458.322 byte di sorgenti e 299.923.100 byte di testo
  previsto. Il volume effettivamente estratto è verificato dal runner entro
  ±1% del target; il solo valore previsto non prova l'ingestione.

## Metodo

Comandi principali eseguiti dalla radice del repository (profili small e
adverse analoghi, con i rispettivi nomi):

```powershell
python experiments/v2_benchmark.py generate experiments/results/v2-target-final --profile target
python experiments/v2_benchmark.py verify experiments/results/v2-target-final
python experiments/run_v2_benchmark.py run experiments/results/v2-target-final experiments/results/v2-target-final-run2 --cycles 3
python experiments/run_v2_benchmark.py summary experiments/results/v2-target-final-run2/report.json
```

Verifiche: `python -m pytest -q` da `backend/` (327 passed, 6 skipped),
`python experiments/run_homework3.py` (PASS) e suite T08 mirata (5 passed).
Il manifest target contiene seed, 10.000 hash, dimensioni sorgente e testo
atteso; il report grezzo include revisione Git, stato dirty, hardware,
versioni e campioni delle query.

Il runner verifica tutti i file tramite SHA-256, crea una copia del corpus e
uno storage temporaneo indipendente per ciascuno dei tre cicli. Ogni fase
usa un processo Python nuovo: build, riapertura, no-change, query e sync
incrementale. Il sync target modifica, rimuove e aggiunge 100 file per tipo,
distribuiti sui formati. Misura durata della fase e picco working set/memoria
privata del processo Windows. La riapertura distingue composizione, tempo
dall'avvio del processo alla ricerca disponibile e sync automatico. Il tempo
di processo include startup Python e import; la composizione è una sottoparte.

Le query hanno cinque warm-up ciascuna, poi cento campioni per query con
ordine rimescolato a seed fisso, pagina 50. Le liste complete sono verificate
prima dei campioni; il p95 usa nearest-rank. Per i job si riportano i tre
valori, mediana e intervallo. I tempi delle verifiche funzionali e delle copie
non sono inclusi nei tempi delle operazioni. La cache del sistema operativo
non viene svuotata; la prova non è un avvio a cache fredda. Il profilo
diagnostico separato aggiunge overhead e misura intervalli inclusivi dei
reader, dell'aggiunta all'indice e della persistenza. Nella ricerca, lookup,
intersezione e verifica delle frasi sono aggregati in `query_clauses`;
analyzer, raccolta e ordinamento occupano il resto di `query_evaluation` e
non sono isolati esattamente.

## Risultati

Small (corpus ID `8c00fa957a4b3e10f8a529cfb2f33406c52352a693e130931bc010d771740058`)
e adverse (corpus ID `c02dcaae51638d8c061b2436d656b5e18d33ac2ee7af092901c4eb43e678ad61`)
hanno report `PASS` di tre cicli. I valori sono in secondi, nell'ordine dei
cicli; RAM è il massimo working set della fase, in MiB arrotondati.

| Profilo | Build | Avvio fino a ricerca | No-change | Incrementale | Max query p95 | Max RAM |
|---|---|---|---|---|---|---|
| Small, 100 | 0,550 / 0,365 / 0,368 | 0,380 / 0,359 / 0,346 | 0,009 / 0,009 / 0,008 | 0,158 / 0,169 / 0,160 | 0,000541 | 53 MiB |
| Adverse, 1.000 | 42,518 / 42,076 / 41,592 | 6,321 / 6,302 / 6,259 | 0,052 / 0,069 / 0,050 | 12,448 / 12,253 / 12,406 | 0,005272 | 469 MiB |

Il backend ha estratto rispettivamente 299.590 e 29.994.709 byte in ciascun
ciclo. Il sync automatico dopo riapertura impiega circa 0,020 s su small e
0,062 s su adverse; il costo di caricamento è molto maggiore. La
profilazione di small, effettuata separatamente, attribuisce circa 0,37 s
ai reader, 0,17 s all'aggiunta nell'indice e 0,23 s alla persistenza, con
overhead del profiler e durata inclusiva.

Il target (corpus ID `3d29323c75500f1fe2492691ac6b655c414d2c6478adb81b1b84ea37cea5a2ef`)
ha completato tre cicli `PASS`, ciascuno con 299.948.099 byte di testo
estratto. I valori sono in secondi; il massimo query p95 è quello della
frase frequente nel contenuto. RAM è il massimo working set, in MiB.

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

Lo storage dopo build è 3,612 GB; dopo il sync 7,216–7,271 GB. Il costo
dominante è la costruzione completa; la riapertura impiega circa 70 s a
caricare lo snapshot, mentre il no-change richiede meno di 0,5 s dopo il
caricamento. Il sync incrementale mantiene un costo elevato nonostante solo
300 path cambino. Le query comuni e la frase su tutti i documenti sono le
più lente; quelle selettive restano sotto 0,004 s p95 nei tre cicli. Queste
osservazioni motivano il lavoro su retrieval e storage delle milestone
successive, senza attribuire causalità a un singolo componente non isolato.

## Budget approvati V2-D01

Questi valori sono **approvati**. Si applicano al profilo target
e all'hardware/metodo sopra, su tre cicli `PASS`. Il criterio è il massimo
dei tre valori per ogni job, il massimo dei p95 per tutte le query e il
massimo working set di ogni fase. I numeri sono obiettivi per V2-03/V2-04 e
V2-08, non risultati già raggiunti dal backend v1.

| Metrica | Baseline peggiore | Budget approvato | Motivo |
|---|---:|---:|---|
| Query p95 | 247 ms | ≤ 100 ms | Risposta interattiva anche per query comuni |
| Avvio fino a ricerca disponibile | 70,6 s | ≤ 15 s | Riapertura utilizzabile senza lunga attesa |
| Build iniziale | 440,1 s | ≤ 300 s | Ridurre il costo del primo indice a 5 minuti |
| Sync incrementale 100/100/100 | 162,2 s | ≤ 60 s | Limitare l'attesa di aggiornamento |
| Sync no-change | 0,438 s | ≤ 1 s | Margine per i controlli v2 senza regressione rilevante |
| Picco RAM working set | 4125 MiB | ≤ 2560 MiB | Ridurre l'impronta su PC con 8 GB RAM |

Le misure sono su Windows con cache OS non svuotata e working tree modificato;
non provano il pacchetto installato né la cache fredda. Il corpus è sintetico:
non cattura la variabilità di PDF reali, antivirus o carichi concomitanti. Le
tre ripetizioni descrivono la variabilità locale, non un intervallo statistico
universale. Un errore o timeout resta un report incompleto. V2-D01 è chiusa;
la prova sul pacchetto rimane V2-08.
