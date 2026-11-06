# Desktop Windows — M8

Interfaccia italiana PySide6 Qt Widgets, nello stesso processo del backend M7.
Un pacchetto separato mantiene Qt fuori dall'installazione della CLI Homework.

## Installazione e avvio

Per setup e riavvio automatici usa il task VS Code **Local Document Search: avvia / riavvia**:
[istruzioni e script](../scripts/dev/README.md). Backend e frontend sono nello stesso processo.

Da root del repository, con Python >=3.12 e un ambiente virtuale attivo:

```powershell
python -m pip install -e "./backend[dev]" -e "./frontend[dev]"
python -m pip check
local-document-search-desktop
```

In alternativa: `python -m local_document_search_desktop.main`.
La distribuzione senza Python e il congelamento delle versioni appartengono a M9.
Ambiente verificato M8: Windows 11 x64, Python 3.12.2, PySide6 6.12.0.

## Uso

- Leggi l'informativa e premi **Continua**: recupera l'ultima cartella e avvia il sync automatico.
- **Scegli cartella** avvia la prima indicizzazione ricorsiva di TXT, Markdown e PDF testuali.
- Scegli Nome, Contenuto o Entrambi; premi Invio per cercare termini AND e frasi tra virgolette.
- Usa Precedente/Successiva per le pagine da 50; seleziona un risultato per il testo completo.
- **Apri file** usa l'applicazione predefinita di Windows. File assente: messaggio e proposta Sync.
- **Sync** controlla i cambiamenti; non è presente un watcher. Durante il job resta consultabile l'indice precedente della stessa cartella.
- **Elimina dati locali** richiede conferma ed è disabilitato durante il job. Non elimina i sorgenti.
- La chiusura attende job e letture senza bloccare la finestra; nessun cancel.

Il testo estratto è persistito in `%LOCALAPPDATA%/LocalDocumentSearch`, anche quando il sorgente
diventa assente. Nessun cloud, cifratura aggiuntiva, ranking, snippet o highlighting.
Un'altra istanza sullo stesso storage viene rifiutata; chiudila e riprova Continua.

## Test e confini

```powershell
cd frontend
python -m pytest
```

I test usano `QT_QPA_PLATFORM=offscreen` per impostazione predefinita.
Per finestre native Windows: `$env:QT_QPA_PLATFORM = "windows"` prima di pytest.
I test usano QtTest, Future controllate, worker reali e storage temporaneo; nessun corpus personale.
Widget/controller dipendono dai contratti applicativi. Solo `composition.py` collega il backend
persistente e l'adapter di apertura file; nessun accesso UI allo storage o agli indici.

[Verifica M8](../docs/M8_VERIFICATION.md) · [UX](../docs/UX_WINDOWS.md) · [Roadmap](../docs/ROADMAP.md)

Distribuzione personale Windows standalone M9: [build e istruzioni](../scripts/package/README.md),
[evidenze e criterio Windows pulito ancora aperto](../docs/M9_VERIFICATION.md).
