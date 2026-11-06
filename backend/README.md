# Backend — CLI multiformato e persistenza M5

Python >=3.12; dipendenze runtime pypdf 7.0.0 e markdown-it-py 4.2.0. Motore proprietario con indici posizionali filename/content, build completo su snapshot in memoria e sessione di ricerca console. [Evidenze M4](../docs/M4_VERIFICATION.md).

## Installazione e verifica

Da `backend/`, PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Per riprodurre anche le versioni transitive dell'ambiente di sviluppo usare `python -m pip install -r requirements-dev.txt`. Su Linux attivare `.venv` con `source .venv/bin/activate`; gli altri comandi restano uguali. GitHub Actions crea una virtualenv isolata e usa esplicitamente il suo interprete per installazione, `pip check` e test su Windows/Linux, Python 3.12. Questo evita conflitti con pacchetti preinstallati sul runner, come `pipx`; non è stata verificata la CI remota in questa esecuzione.

## Sessione console

```powershell
local-document-search "C:\percorso\documenti"
# Alternativa equivalente:
python -m local_document_search.interfaces.cli "C:\percorso\documenti"
```

Directory relativa o assoluta; scansione ricorsiva di TXT, Markdown e PDF, suffissi case-insensitive, nessun link/junction/reparse point attraversato. Radici link o con componenti link sono rifiutate. TXT/Markdown: decodifica UTF-8 rigorosa con BOM ammesso; errore di scansione, lettura o encoding interrompe il build senza pubblicare un indice parziale.

Markdown: testo da token CommonMark con tabelle, link/alt e codice inline; esclusi blocchi di codice, front matter iniziale chiuso e token HTML grezzi. PDF: testo in ordine di pagina, nessun OCR; senza testo non-whitespace viene escluso, mentre corruzione o password necessaria fanno fallire il build. TXT/MD vuoti restano ricercabili per nome. Nessun accesso agli URL dei documenti.

Esempi:

```text
nome Report2026
contenuto roma tre
contenuto "roma tre"
entrambi machine "deep learning"
"nome"
```

I prefissi minuscoli non quotati selezionano il campo; senza prefisso vale BOTH. AND e frasi devono essere soddisfatti interamente nello stesso campo. `"nome"` cerca il termine letterale. Errori di query non terminano la sessione; non esistono comandi riservati `exit`/`quit`.

La console stampa conteggi, tempo del build e tutti i risultati ordinati per percorso relativo, con campi corrispondenti. Il servizio usa pagine da 50; la CLI le scorre automaticamente. Uscita con EOF (Windows: Ctrl+Z poi Invio; Unix: Ctrl+D) o Ctrl+C.

Codici: `0` EOF/help, `1` errore operativo (anche directory assente), `2` argomenti invalidi, `130` Ctrl+C.

## Confini e limiti

- Domain: analyzer, parser, builder e matching puri, snapshot immutabili.
- Application: `BuildIndex`, `BuildResult`, `SearchDocuments`, DTO e porte.
- Infrastructure: discovery, reader TXT/Markdown/PDF, `InMemorySnapshotRepository` e `SqliteSnapshotRepository`.
- Interfaces: CLI e `compose_cli`; `compose_application` conserva il cablaggio esplicito M1.

Ogni sessione usa una directory e un writer sincrono. La CLI non persiste l’indice e non rilegge i file durante le query; i risultati riflettono il build iniziale. Settings, diff, job asincroni e UI sono rinviati. SQLite usa la standard library; PySide6 non viene installato.

Per le dieci query e le misure, dalla radice eseguire `backend/.venv/Scripts/python experiments/run_homework3.py` (Linux: `.venv/bin/python`). [Relazione](../docs/homework-3/REPORT.md).


## Backend persistente M5

Il testo estratto viene conservato localmente anche se il sorgente viene eliminato: scegliere uno storage privato dell’account, esterno al repository e alla directory indicizzata. Nessuna cifratura applicativa aggiuntiva. La CLI Homework resta volatile; l’uso persistente è esplicito nel backend:

```python
from local_document_search.application.contracts import SearchRequest
from local_document_search.application.search import GetDocument, SearchDocuments
from local_document_search.application.synchronization import BuildIndex
from local_document_search.infrastructure.filesystem import TextFileDiscovery, resolve_directory
from local_document_search.infrastructure.readers.text import TextReader
from local_document_search.infrastructure.sqlite_snapshot_storage import SqliteSnapshotRepository

root = resolve_directory("C:/documenti")
# Default Windows: %LOCALAPPDATA%/LocalDocumentSearch.
# Su altri sistemi passare una directory applicativa esplicita come primo argomento.
with SqliteSnapshotRepository(source_directory=root) as snapshots:
    if snapshots.load_active() is None:
        BuildIndex(TextFileDiscovery(), TextReader(), snapshots).execute(root)
    elif snapshots.load_active().root_directory != root:
        raise ValueError("Usare soltanto la directory dello snapshot attivo")
    result = SearchDocuments(snapshots).execute(SearchRequest("roma"))
    if result.results:
        details = GetDocument(snapshots).execute(result.results[0].document_id, result.snapshot_id)
```

L’esempio costruisce solo TXT; i reader multiformato esistenti possono essere iniettati nello stesso `BuildIndex`. Non esegue sync o controllo dei cambiamenti. La riapertura del repository non richiede i sorgenti; `resolve_directory` nell’esempio serve alla scelta iniziale della radice.

Un solo proprietario della sessione e un writer, senza uso concorrente fra thread/processi. `acquire()` protegge le versioni dalle pulizie; `load_active()` restituisce il valore immutabile senza prenotare la retention. Restano attivo e precedente della directory corrente, oltre alle letture in corso. `clear()` elimina solo le righe possedute, non l’intero storage applicativo né i documenti originali; non garantisce cancellazione forense. Lock, settings, rebuild e ClearLocalData completo sono rinviati a M6–M7. [Verifica M5](../docs/M5_VERIFICATION.md).
