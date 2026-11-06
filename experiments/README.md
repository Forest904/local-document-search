# Esperimenti Homework 3

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
[Evidenze e limiti M9](../docs/M9_VERIFICATION.md).

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
