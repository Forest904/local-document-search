# Esperimenti Homework 3

`run_homework3.py` crea otto TXT sintetici in una directory temporanea, esegue dieci query e due regressioni in una sessione CLI reale, confronta gli attesi espliciti e stampa misure/trascrizione in JSON. Nessun dato personale o snapshot è versionato.

Dalla radice, dopo l'installazione del backend:

```powershell
backend/.venv/Scripts/python experiments/run_homework3.py
```

Su Linux usare `backend/.venv/bin/python`. Il runner restituisce codice 1 se i risultati differiscono. Il corpus è deterministico, i tempi no. Il tempo copre il build iniziale completo, senza avvio del processo e validazione iniziale dell'argomento directory.

Risultati locali in `experiments/results/` (ignorata da Git). [Relazione M3](../docs/homework-3/REPORT.md), [matrice query](../docs/homework-3/QUERY_TEST_PLAN.md).
