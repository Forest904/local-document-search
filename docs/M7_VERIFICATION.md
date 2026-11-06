# Verifica M7 — Job e concorrenza

Verifica locale del 6 novembre 2026 su Windows 11 x64, Python 3.12.2.
Verifica finale nell'ambiente esistente `backend/.venv`, con installazione editable ripetuta.
CLI Homework invariata; nessun commit, push o esecuzione CI remota effettuati.

## Comandi ed esiti

Da `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q -ra
.\.venv\Scripts\python.exe -m pip check
```

- Installazione sviluppo riuscita, nessuna nuova dipendenza.
- Suite finale: **314 passed, 5 skipped**, 15,62 secondi; 21 nuovi casi M7.
- `pip check`: **No broken requirements found**.
- `git diff --check` dalla radice: nessun errore.
- Le prove preliminari hanno usato il Python presente nel PATH; la verifica finale usa
  esplicitamente l'interprete del progetto. Non è un'installazione in ambiente pulito.

## Evidenze

`backend/tests/integration/test_jobs_concurrency.py` usa fixture sintetiche temporanee, eventi
e barriere per controllare le interleaving; i timeout limitano i test, non determinano la correttezza.

- Venti trigger sovrapposti riusano lo stesso job; RunSynchronization attende lo stesso lavoro.
  Selezione/pulizia durante job e ID/trigger sconosciuti sono rifiutati.
- SCANNING indeterminata, fasi estrazione/analisi/commit, conteggi e byte monotoni;
  corpus vuoto, file vuoto, sole rimozioni, NO_CHANGES ed esclusioni completano senza divisioni per zero.
  Un commit sospeso o fallito non espone successo o progresso 100%.
- Una query e un recupero dettagli terminano su N durante un commit N+1 sospeso.
  Una query lunga conserva N attraverso due commit e la retention elimina N solo dopo il rilascio.
  Una richiesta accodata acquisisce lo snapshot all'esecuzione, non alla chiamata submit.
- Startup restituisce subito lo snapshot compatibile mentre la scansione resta sospesa.
  Errore di estrazione conserva lo snapshot; un nuovo job può riuscire e lo stato fallito resta consultabile.
- Cambio directory invalida nuovi dettagli della precedente ma lascia completare una query già avviata.
  ClearLocalData attende una query asincrona, rifiuta nuove acquisizioni e azzera lo stato operativo.
- Chiusura attende job e query, rifiuta nuove operazioni e conserva il lock fino alla fine;
  close ripetuto e fallimento di composizione non impediscono una successiva apertura.
- Secondo processo rifiutato senza alterare i database; il file di lock rimasto dopo chiusura non blocca.
  Terminazione esterna durante scansione rilascia il lock. `os._exit` prima/dopo commit verifica
  recovery rispettivamente del vecchio o nuovo snapshot completo.

I 25 casi lifecycle M6 ora attendono esplicitamente il job asincrono quando verificano l'esito finale;
continuano a verificare diff, incompatibilità, rebuild, errori, pulizia e crash di selezione database.
La suite completa include regressioni CLI, reader, ricerca, persistenza e confini degli import.

## Limiti

- Quattro skip richiedono privilegi Windows per creare symlink; uno richiede nomi distinti solo per case.
- Il ramo Windows del lock è verificato; il ramo POSIX resta da eseguire su Linux/CI.
- Arresti di processo, non perdita di alimentazione. Nessun benchmark o garanzia prestazionale.
- Attivo, precedente e versioni acquisite restano in RAM; al riavvio vengono caricati attivo e precedente.
  Stati e Future dei job sono conservati per la durata della sessione, non persistiti.
- `session.lock` e il contenitore di controllo vuoto restano dopo ClearLocalData;
  nessuna cancellazione forense. Gli adapter diretti richiedono un solo proprietario:
  il lock di sessione viene fornito da `compose_persistent_application`.
- UI responsiva, gestione delle risposte obsolete e pacchetto Windows restano M8/M9;
  CI remota non verificata. L'API usa Future e DTO, senza Qt o callback grafici.
