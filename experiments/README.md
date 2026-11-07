# Esperimenti v1 e baseline v2

## V2-01: corpus funzionale

Da radice repository, con il backend installato:

```powershell
python experiments/v2_corpus.py synthetic experiments/results/v2-synthetic
python experiments/v2_corpus.py fetch experiments/results/v2-real
python experiments/v2_corpus.py verify-real experiments/results/v2-real
python experiments/v2_corpus.py export-text experiments/results/v2-real experiments/results/v2-real-text-final
python experiments/v2_corpus.py validate-real experiments/results/v2-real
```

Il primo comando genera e verifica 13 sintetici TXT/MD/PDF. Usare una destinazione vuota per `synthetic` ed `export-text`. `fetch` usa la cache locale, confronta SHA-256 e non sostituisce file con hash diverso. `verify-real` controlla i 12 file del manifest senza rete; `export-text` produce i testi canonici per la revisione della ground truth secondo il [prompt](v2_corpus/ASTRA_GROUND_TRUTH_PROMPT.md). `validate-real` confronta le 36 query in [real_queries.json](v2_corpus/real_queries.json) e segnala esito incompleto se il file manca. I corpus e i testi esportati stanno in `experiments/results/`, ignorata da Git. [Esiti verificati V2-01](../docs/ROADMAP.md#v2-01--corpus-ibrido-e-validazione-funzionale).

La suite ordinaria include T20. Per ripetere T21 con la ground truth versionata:

```powershell
$env:LDS_V2_REAL_CORPUS='C:/percorso/assoluto/experiments/results/v2-real'
python -m pytest backend/tests/integration/test_v2_corpus.py -q
```

La suite reale è opt-in e non può passare con documenti mancanti, hash errati o ground truth assente. I report JSON riportano identificatore del corpus, hash delle query e revisione del codice; la revisione Git va associata anche allo stato del working tree nell'evidenza finale. Nessuna misura prodotta qui costituisce benchmark V2-02.

I runner esistenti sono il punto di partenza di [V2-01](../docs/ROADMAP.md): il runner Homework verifica query su sintetici, mentre il corpus M9 combina query attese e misure. La [specifica del corpus ibrido](../docs/TEST_DATASETS.md) definisce la nuova validazione funzionale; i budget prestazionali si decidono in V2-02.

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
[Evidenze e limiti M9](../docs/archive/v1/M9_VERIFICATION.md).

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
