# Backend — CLI TXT M3

Python >=3.12, senza dipendenze runtime esterne. Motore proprietario con indici posizionali filename/content, build completo su snapshot in memoria e sessione di ricerca console. [Evidenze M3](../docs/M3_VERIFICATION.md).

## Installazione e verifica

Da `backend/`, PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest
```

Per riprodurre anche le versioni transitive dell'ambiente di sviluppo usare `python -m pip install -r requirements-dev.txt`. Su Linux attivare `.venv` con `source .venv/bin/activate`; gli altri comandi restano uguali. GitHub Actions configura installazione e test su Windows/Linux, Python 3.12; non è stata verificata la CI remota in questa esecuzione.

## Sessione console

```powershell
local-document-search "C:\percorso\documenti"
# Alternativa equivalente:
python -m local_document_search.interfaces.cli "C:\percorso\documenti"
```

Directory relativa o assoluta; scansione ricorsiva dei soli TXT, suffissi case-insensitive, nessun link/junction/reparse point attraversato. Radici link o con componenti link sono rifiutate. Decodifica UTF-8 rigorosa con BOM ammesso; errore di scansione, lettura o encoding interrompe il build senza pubblicare un indice parziale.

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
- Infrastructure: discovery, reader TXT e `InMemorySnapshotRepository`.
- Interfaces: CLI e `compose_cli`; `compose_application` conserva il cablaggio esplicito M1.

Ogni sessione usa una directory e un writer sincrono. Nessuna persistenza o rilettura dei file durante le query; i risultati riflettono il build iniziale. Settings, diff, job asincroni e UI sono rinviati. pypdf/markdown-it-py, SQLite e PySide6 non vengono installati.

Per le dieci query e le misure, dalla radice eseguire `backend/.venv/Scripts/python experiments/run_homework3.py` (Linux: `.venv/bin/python`). [Relazione](../docs/homework-3/REPORT.md).
