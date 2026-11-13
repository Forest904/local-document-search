# Esperimenti v1 e baseline v2

## V2-09: suffissi e suggerimenti

`compare_v2_vocab.py` misura lookup con vocabolario rovesciato, scansione e suggerimenti su 20.000 termini sintetici; salvare l'output sotto `experiments/results/` (ignorata da Git). Il runner V2-02 conserva le query precedenti e aggiunge una ricerca e un suggerimento per suffisso. Usare lo stesso comando di generazione e i tre cicli indicati sotto; registrare i risultati in [V2-09](../docs/V2_09_SUFFIX_SEARCH.md), senza sovrascrivere le evidenze V2-02 storiche.

```powershell
backend/.venv/Scripts/python.exe experiments/compare_v2_vocab.py --output experiments/results/v2-09-vocab.json
```

## V2-02: corpus e benchmark prestazionale

Da radice repository, con il backend installato, generare e verificare un corpus
in `experiments/results/` (esclusa da Git):

```powershell
python experiments/v2_benchmark.py generate experiments/results/v2-target --profile target
python experiments/v2_benchmark.py verify experiments/results/v2-target
python experiments/run_v2_benchmark.py run experiments/results/v2-target experiments/results/v2-target-run
python experiments/run_v2_benchmark.py summary experiments/results/v2-target-run/report.json

# Rivalutazione separata di un report compilato storico con i budget approvati:
python experiments/run_v2_benchmark.py reassess experiments/results/v2-022-compiled/report.json experiments/results/v2-022-reassessed.json

# Confronto compilato alternato: sei prove da un ciclo, poi aggregazione per versione.
# Indicare gli EXE estratti dagli ZIP identificati e un output nuovo.
python experiments/compare_compiled.py experiments/results/v2-target C:/percorso/021/LocalDocumentSearch.exe C:/percorso/022/LocalDocumentSearch.exe experiments/results/v2-compare-nuovo
```

I profili sono `small` (100), `adverse` (1.000) e `target` (10.000 file,
300 MB di testo estratto); `smoke` (12) serve ai test. Ogni formato TXT/MD/PDF
ricorre a turno. Il runner crea tre copie indipendenti del corpus e storage
temporanei fuori dal repository, con processi nuovi per build, riapertura,
no-change, query e sync incrementale. Nel profilo target il sync cambia 100
file, ne rimuove 100 e ne aggiunge 100. Gli hash nel manifest servono solo
a verificare il corpus sperimentale; il backend continua a usare path, size e
mtime_ns.

Il report grezzo contiene campioni query (100 per query, cinque warm-up),
tempi dei job, RAM e spazio storage. `--cycles`, `--samples`, `--warmups` e
`--timeout` consentono prove ridotte. Il p95 usa nearest-rank. La cache OS
non viene svuotata; la riapertura avviene in un processo nuovo ma non prova
un avvio a cache fredda. Il tempo `compose_seconds` misura la composizione
del backend; `search_ready_seconds` comprende processo Python, composizione e
initialize fino alla disponibilità della ricerca. `startup_sync_seconds`
misura separatamente il job avviato da initialize. I risultati sono di
backend sorgente, non del pacchetto installato.

Per una profilazione diagnostica separata dai tempi di riferimento:

```powershell
python experiments/run_v2_benchmark.py profile experiments/results/v2-small C:/percorso/storage-nuovo experiments/results/v2-profile.txt --phase build
```

`profile` produce testo e `.pstats`; l'overhead del profiler impedisce di
usare quei tempi come baseline. `diagnostic_seconds` somma le chiamate ai
reader, all'aggiunta nell'indice, alla persistenza e al caricamento; sono
durate inclusive e non una partizione esatta del job. La statistica cProfile
copre il thread principale, mentre il job di build gira nel worker; i timer
diagnostici coprono anche quel worker. `query_clauses` aggrega lookup,
intersezione e verifica delle frasi; la differenza rispetto a
`query_evaluation` include analyzer, raccolta dei match e ordinamento,
senza isolarli esattamente. Lo storage
del profilo build deve essere nuovo e fuori dal repo.

## V2-01: corpus funzionale

Da radice repository, con il backend installato:

```powershell
python experiments/v2_corpus.py synthetic experiments/results/v2-synthetic
python experiments/v2_corpus.py fetch experiments/results/v2-real
python experiments/v2_corpus.py verify-real experiments/results/v2-real
python experiments/v2_corpus.py export-text experiments/results/v2-real experiments/results/v2-real-text-final
python experiments/v2_corpus.py validate-real experiments/results/v2-real
```

Il primo comando genera e verifica 13 sintetici TXT/MD/PDF. Usare una destinazione vuota per `synthetic` ed `export-text`. `fetch` usa la cache locale, confronta SHA-256 e non sostituisce file con hash diverso. `verify-real` controlla i 12 file del manifest senza rete; `export-text` produce i testi canonici per la revisione della ground truth secondo il [metodo di preparazione](../docs/TEST_DATASETS.md#acquisizione-e-ground-truth). `validate-real` confronta le 36 query in [real_queries.json](v2_corpus/real_queries.json) e segnala esito incompleto se il file manca. I corpus e i testi esportati stanno in `experiments/results/`, ignorata da Git. [Esiti verificati V2-01](../docs/TEST_DATASETS.md#verifica-v2-01).

La suite ordinaria include T20. Per ripetere T21 con la ground truth versionata:

```powershell
$env:LDS_V2_REAL_CORPUS='C:/percorso/assoluto/experiments/results/v2-real'
python -m pytest backend/tests/integration/test_v2_corpus.py -q
```

La suite reale è opt-in e non può passare con documenti mancanti, hash errati o ground truth assente. I report JSON riportano identificatore del corpus, hash delle query e revisione del codice; la revisione Git va associata anche allo stato del working tree nell'evidenza finale. Nessuna misura prodotta qui costituisce benchmark V2-02.

## Homework 3

HW3-01: `homework3_corpus.py` prepara il corpus personale in `experiments/results/homework3/` (ignorata da Git). Eseguire `inventory SOURCE OUTPUT.json`, poi `prepare SOURCE DESTINAZIONE_NUOVA` e `verify DESTINAZIONE`. Manifest, sorgenti copiati ed estratti sono locali. I PDF senza testo estraibile sono esclusioni ammesse; `complete` riguarda la preparazione. `verify` controlla anche gli originali esclusi e la corrispondenza con l'inventario. Nessuna soglia minima di testo è applicata alle slide. Il registro `metadata/manual_review.json` conserva separatamente la revisione e la decisione dell'utente.

I sintetici correnti sono `synthetic-small-003`, `synthetic-medium-003` e `synthetic-large-003`: paragrafi originali IT/EN, seed 20261113, schema 2, 100/1.000/10.000 TXT. [Protocollo, risultati e limiti](../docs/homework-3/HW3_01_CORPUS.md). Per riprodurli, scegliere tre destinazioni nuove con un suffisso comune libero a partire da 002; non cancellare o sovrascrivere i precedenti. Il profilo non modifica gli ID condivisi.

```powershell
backend/.venv/Scripts/python.exe experiments/homework3_corpus.py synthetic experiments/results/homework3/synthetic-small-NNN --profile small
backend/.venv/Scripts/python.exe experiments/homework3_corpus.py synthetic experiments/results/homework3/synthetic-medium-NNN --profile medium
backend/.venv/Scripts/python.exe experiments/homework3_corpus.py synthetic experiments/results/homework3/synthetic-large-NNN --profile large
backend/.venv/Scripts/python.exe experiments/homework3_corpus.py verify-nested experiments/results/homework3/synthetic-small-NNN experiments/results/homework3/synthetic-medium-NNN experiments/results/homework3/synthetic-large-NNN --output experiments/results/homework3/verification-NNN.json
```

Sostituire `NNN` con il suffisso scelto. Il controllo congiunto legge tutti i file, verifica conteggi, byte UTF-8, hash, tolleranza e metadati, quindi confronta percorsi/hash per ID. È opt-in e separato dalla suite ordinaria. `verify DESTINAZIONE` resta disponibile per un singolo corpus e per i manifest storici schema 1. Famiglie e termini assenti sono metadati di costruzione fuori da `txt/`, non il futuro set di query HW3-02.

`run_homework3.py` crea otto TXT sintetici in una directory temporanea, esegue dieci query e due regressioni in una sessione CLI reale, confronta gli attesi espliciti e stampa misure/trascrizione in JSON. Nessun dato personale o snapshot è versionato.

Dalla radice, dopo l'installazione del backend:

```powershell
backend/.venv/Scripts/python experiments/run_homework3.py
```

Su Linux usare `backend/.venv/bin/python`. Il runner restituisce codice 1 se i risultati differiscono. Il corpus è deterministico, i tempi no. Il tempo copre il build iniziale completo, senza avvio del processo e validazione iniziale dell'argomento directory.

Risultati locali in `experiments/results/` (ignorata da Git). [Relazione M3](../docs/homework-3/REPORT.md), [matrice query](../docs/homework-3/QUERY_TEST_PLAN.md).

## M9: corpus multiformato e misure

Dalla radice su Windows, con il backend installato:

```powershell
backend/.venv/Scripts/python experiments/m9_corpus.py experiments/results/m9-corpus
backend/.venv/Scripts/python experiments/run_m9.py experiments/results/m9-corpus "$env:TEMP/LocalDocumentSearch-M9/backend-storage" experiments/results/m9-backend.json
```

Generare in una destinazione vuota e usare uno storage nuovo **fuori dal repository**.
Il corpus contiene 3.000 file, 1.000 per formato, circa 30 MB di testo e seed 20261106.
Il manifest elenca dimensioni, hash dei file sintetici e risultati attesi per sette query.
Gli hash appartengono soltanto al corpus di prova: il sync del prodotto rimane path/size/mtime.
Le fixture non valide e il PDF senza testo sono nella cartella separata `errors/`.
Per uno smoke rapido: `--count 60 --text-bytes 300` al generatore.

Il runner controlla i risultati, misura build, riapertura, no-change, un'aggiunta/modifica/rimozione
e cinque ripetizioni delle query dopo warm-up. Ripristina i byte originali dei file modificati
anche in caso di errore; i timestamp possono cambiare. Lo storage finale riflette il sync
incrementale precedente al ripristino, quindi non va riutilizzato per misure di primo avvio.
Il picco memoria Win32 riguarda l'intero processo; i tempi delle fasi interne non sono separati.
La riapertura è nello stesso processo con cache del sistema operativo calda.

Per osservare il pacchetto estratto, con PATH/Python/Qt ripuliti e LOCALAPPDATA isolato:

```powershell
backend/.venv/Scripts/python experiments/launch_m9_package.py 'C:/percorso estratto/LocalDocumentSearch.exe' "$env:TEMP/LocalDocumentSearch-M9/gui"
```

Il launcher resta attivo fino alla chiusura della GUI e salva un JSON per processo
con PID, esito e picco memoria campionato ogni 100 ms. La durata della sessione include
le attese dell'operatore: **non** è un tempo di build o query. Per la seconda istanza
usare la stessa workspace; per uno storage indipendente usarne una nuova.
[Evidenze e limiti M9](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/M9_VERIFICATION.md).

## Fault injection separata dal pacchetto

L'harness in `fault_harness.py` è un eseguibile di prova separato. Il runner usa
storage temporaneo isolato, verifica recovery e riacquisizione del lock, e non modifica
il pacchetto distribuito. Per la verifica sorgente:

```powershell
$env:PYTHONPATH='backend/src'
backend/.venv/Scripts/python.exe experiments/run_fault_harness.py backend/.venv/Scripts/python.exe experiments/fault_harness.py
```

Per quella compilata, creare l'harness con l'interprete packaging e Nuitka 4.1.1,
quindi passare `build/fault-harness/fault_harness.dist/fault_harness.exe` al runner.
Le tre prove `race` terminano il processo in competizione con COMMIT: accettano soltanto
uno snapshot vecchio o nuovo completo, senza attribuire il kill a un punto interno preciso.
