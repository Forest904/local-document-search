# Backend e CLI

Python >=3.12; motore di ricerca condiviso con il desktop, senza dipendenze Qt. Dipendenze runtime e versioni sono nel [pyproject.toml](pyproject.toml).

## Installazione e test

Da `backend/`, con un ambiente virtuale attivo:

```powershell
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Per bloccare anche le dipendenze transitive usare `python -m pip install -r requirements-dev.txt`. La [CI](../.github/workflows/backend.yml) verifica Windows e Linux.

### Organizzazione dei test

`tests/unit/` copre dominio, DTO, analyzer/parser, matching, snapshot e confini degli import; `tests/integration/` copre composizione, reader/storage, sync, concorrenza, fault e CLI come processo reale. Fixture sintetiche in directory temporanee pytest: `test_multiformat.py` genera PDF testuali, immagini, pagine miste e password con pypdf, senza binari versionati. Test di link/nomi distinti dichiarano skip motivati dove non supportati; corpus reale opt-in e completo. [Strategia](../docs/TEST_STRATEGY.md), [corpus](../docs/TEST_DATASETS.md); nessun documento personale.

## Sessione console

```powershell
local-document-search "C:/percorso/documenti"
# Alternativa:
python -m local_document_search.interfaces.cli "C:/percorso/documenti"
```

La CLI indicizza ricorsivamente TXT, Markdown e PDF testuali, poi accetta query:

```text
nome Report2026
contenuto roma tre
contenuto "roma tre"
entrambi machine "deep learning"
"nome"
```

I prefissi minuscoli non quotati selezionano il campo; senza prefisso vale BOTH. `"nome"` cerca il termine letterale. AND e frasi devono corrispondere interamente nello stesso campo. Gli errori di query non chiudono la sessione; `exit` e `quit` non sono comandi riservati.

L’indice viene ricostruito in memoria a ogni avvio. Durante la ricerca i sorgenti non vengono riletti; la CLI stampa tutti i risultati per percorso, scorrendo le pagine da 50. Esci con EOF (Windows: Ctrl+Z, Invio; Unix: Ctrl+D) o Ctrl+C. Codici: `0` EOF/help, `1` errore operativo, `2` argomenti invalidi, `130` Ctrl+C.

Reader, encoding, esclusioni ed errori seguono la [specifica di analisi](../docs/INDEXING_AND_ANALYSIS.md). Un errore di build non pubblica un indice parziale. Per le dieci query Homework e le due regressioni, dalla root: `python experiments/run_homework3.py`. [Relazione](../docs/homework-3/REPORT.md).

## API persistente

`compose_v2_application(storage)` è la composizione usata dal desktop; `compose_persistent_application(storage)` conserva quella v1. [Contratti e DTO](../docs/INTERFACE_CONTRACTS.md), [storage e retention](../docs/ARCHITECTURE.md#snapshot-e-sincronizzazione).

```python
from local_document_search.application.contracts import SearchRequest
from local_document_search.interfaces.composition import compose_v2_application

def main():
    with compose_v2_application() as app:
        state = app.initialize.execute()
        if state.active_directory is None:
            app.select_directory.execute("C:/Documenti")
        app.synchronize.execute()
        response = app.search.submit(SearchRequest("machine learning")).result()
        print(response.total_matches)

if __name__ == "__main__":
    main()
```

Salvare l’esempio in un file: la protezione `__main__` serve ai processi reader su Windows. L’attesa bloccante è adatta a script; la UI usa polling e Future pronte. Per test e sistemi non Windows passare uno storage esplicito esterno a sorgenti e repository. Il lock precede l’apertura dei database; una seconda sessione riceve `StorageFailure`. Il context manager attende job e letture prima di chiudere.

Testo estratto e indici persistono anche se il sorgente scompare; non c’è cifratura applicativa aggiuntiva. [Privacy](../docs/SECURITY_AND_PRIVACY.md).
