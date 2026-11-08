# Desktop Qt Quick v2

PySide6/Qt Quick con QML e backend v2 nello stesso processo. Il comando
`local-document-search-desktop` conserva l'avvio; la CLI Homework resta nel
pacchetto backend senza dipendenze Qt.

## Avvio e uso

Da root con Python 3.12 x64:

```powershell
python -m pip install -e "./backend[dev]" -e "./frontend[dev]"
local-document-search-desktop
```

Il task VS Code **Local Document Search: avvia / riavvia** usa l'ambiente
`backend/.venv` e lo stesso comando. Al primo avvio leggere l'informativa,
premere **Continua**, scegliere una cartella e attendere la prima indicizzazione.
Le aperture successive recuperano lo snapshot e avviano il sync automatico.
La ricerca resta disponibile sullo snapshot precedente della stessa cartella
durante il sync o se la sorgente è temporaneamente assente.

Premere **Invio** per cercare. Scrivere `termine*` per un prefisso esplicito;
i suggerimenti durante digitazione non avviano la ricerca. La sidebar offre
campo, formati TXT/MD/PDF, cartella relativa ricorsiva e ordine. La rilevanza
è predefinita; il percorso è l'alternativa. Selezionare un risultato per
l'anteprima del testo acquisito, poi **Apri file** per l'applicazione Windows
predefinita. L'anteprima non riproduce il layout PDF.

**Scorciatoie:** `Ctrl+L` mette a fuoco la ricerca, `Ctrl+O` apre la selezione
cartella, `F5` avvia il sync, `Invio` esegue la ricerca o seleziona un risultato
attivo, `Tab` attraversa i controlli. La finestra ha dimensione minima
900×640 pixel logici e sidebar scorrevole.

Italiano e tema chiaro sono iniziali. Lingua e tema si salvano nello storage
v2 separatamente dagli snapshot. **Elimina dati locali** richiede conferma
e azzera anche queste preferenze; non modifica sorgenti o dati v1.
Il job può essere annullato prima del commit. Rebuild e recupero della versione
precedente sono operazioni esplicite.

## Verifiche

```powershell
cd frontend
../backend/.venv/Scripts/python.exe -m pytest
```

I test Qt usano `QT_QPA_PLATFORM=offscreen` per default; impostare
`QT_QPA_PLATFORM=windows` per controlli nativi. Il probe
`experiments/run_v2_desktop.py` usa un corpus sintetico esistente, storage
temporaneo e report/catture fuori Git. Le prove del prototipo standalone sono
distinte dal futuro installer V2-07 e dall'accettazione V2-08.

[Rapporto V2-06](../docs/V2_06_DESKTOP.md) · [UX](../docs/UX_WINDOWS.md)
