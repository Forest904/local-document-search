> Archivio v1 — fotografia documentale del 7 novembre 2026. Stati e risultati sono storici; non descrivono la v2. [Documentazione corrente](../../README.md).

# Verifica M6 — Sync e lifecycle

Verifica locale del 6 novembre 2026 su Windows, Python 3.12.2, ambiente `backend/.venv` esistente.
CLI Homework invariata; nessun commit, push o esecuzione CI remota effettuati.

## Comandi ed esiti

Da `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs
.\.venv\Scripts\python.exe -m pip check
```

- Suite finale: **293 passed, 5 skipped**, 12,64 secondi; 25 nuovi casi M6. Ultima riesecuzione con `-q`;
  la precedente con `-q -rs` ha riportato gli stessi conteggi e le motivazioni degli skip.
- `pip check`: **No broken requirements found**.
- `git diff --check` dalla radice: nessun errore.
- Python verificato con `--version`: 3.12.2.
- Non è stata ripetuta l'installazione in un ambiente pulito; verifica sull'ambiente sviluppo esistente.

## Evidenze

`backend/tests/integration/test_lifecycle_sync.py` usa esclusivamente fixture sintetiche temporanee.
Verifica diff misto, rename, ID preservati, riuso degli invariati senza reader/analyzer, immutabilità
della versione precedente, rimozione dei termini da entrambi gli indici, transizioni INDEXED/EXCLUDED,
corpus vuoto, sole rimozioni e limite accettato size/mtime identici.

Verifica inoltre riavvio NO_CHANGES, sorgente assente, selezione invalida, A→B→A, guardia durante sync,
rollback per estrazione/commit falliti, adozione dello storage M5, incompatibilità fisica/schema/processing,
fallimento della selezione persistente e distinzione dalla corruzione.
Due subprocess terminano con `os._exit(77)` prima/dopo la selezione del database candidato:
al riavvio è disponibile il riferimento precedente o quello nuovo completo, con pulizia degli orfani.

ClearLocalData viene verificato con lettura già acquisita, rifiuto delle nuove acquisizioni,
preservazione dei sorgenti/file estranei, errore di cancellazione e ripetizione riuscita.
La suite completa comprende anche le regressioni CLI, ricerca, reader e confini architetturali.

## Limiti

- Quattro skip richiedono privilegi Windows per creare symlink; uno richiede nomi distinti solo per case.
- Crash di processo simulati, non perdita di alimentazione; nessun benchmark o garanzia prestazionale.
- Nessun JobManager, worker async, lock multiprocesso o verifica generale di concorrenza M7.
- Lo storage M5 incompatibile senza settings richiede selezione esplicita della sorgente e conserva
  i dati fino al rebuild riuscito. Non viene interpretato uno schema fisico sconosciuto.
- ClearLocalData lascia il contenitore di controllo vuoto e riutilizzabile; non promette cancellazione
  forense. M6 non genera log o ulteriori temporanei applicativi.
- CI remota, UI e pacchetto Windows restano da verificare nelle rispettive milestone.
