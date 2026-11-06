# Verifica M1 — Fondazioni verificabili

**Data:** 6 novembre 2026. **Esito:** implementata e verificata localmente; CI remota da verificare.

## Ambiente e comandi

Windows, Python 3.12.2, pytest 8.3.5. Ambiente virtuale `backend/.venv`, dipendenze fissate in `backend/requirements-dev.txt`; nessuna dipendenza runtime esterna.

Dalla radice: `python -m venv backend/.venv`. Poi, da `backend/`:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python -m pytest
```

- Installazione editable e build isolata riuscite con le versioni fissate.
- `pip check`: `No broken requirements found.`
- Pytest: **73 raccolti, 73 superati**, nessuno saltato.
- `git diff --check`: nessun errore.

## Evidenze funzionali

- Identità, metadati, token, clausole e posting con invarianti di base; fingerprint senza hash.
- Snapshot coerenti: corrispondenza manifest/catalogo, esclusioni senza ID, posting senza riferimenti sconosciuti, posizioni coerenti con i conteggi e indipendenti per campo.
- Copie difensive e immutabilità di mappe annidate, posizioni, clausole e risultati.
- DTO di ricerca con default e validazione dei parametri; tre esiti reader distinti.
- Porte infrastrutturali tipizzate e composizione minima verificata con sostituti locali, senza I/O all'assemblaggio.
- Controllo AST di import assoluti, relativi e sotto `TYPE_CHECKING`; esempi sintetici dimostrano che le violazioni vengono rilevate.

## Confini e punti aperti

Il composition root M1 raccoglie le quattro dipendenze esplicite; non costruisce ancora servizi operativi. Il collegamento alla CLI resta M3, come concordato. Nessun framework DI.

La validazione dello snapshot controlla la struttura, non ricalcola token dal testo né decide compatibilità runtime. Allocazione degli ID, builder/draft, parser, analyzer e matching non sono implementati. Reader, repository, atomicità, sync, job e UI non sono verificati da questi test.

Il workflow GitHub Actions è configurato per push/pull request su Windows e Linux, Python 3.12. Non risultano remote Git configurati; nessuna esecuzione remota o prova locale Linux è stata effettuata. La CI non è dichiarata verde e resta una verifica da registrare dopo il push. Non sono stati effettuati commit o push.

Le versioni delle dipendenze sono fissate; il minor Python è 3.12, il patch dei runner CI può differire da 3.12.2. I runner hosted e le action non costituiscono un'immagine di sistema immutabile.

Nessun benchmark o corpus personale utilizzato. M2–M9 restano da implementare.
