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
`backend/.venv` e lo stesso comando. Al primo avvio leggere l'informativa e scegliere **Accetta e scegli una cartella**.
La stessa pagina mostra progresso reale e consigli. La home **Luma** si apre
quando l'indice è disponibile. Le aperture successive recuperano automaticamente
il catalogo v2 e sincronizzano in background mantenendo la ricerca disponibile.

Premere **Invio** o **Cerca**. `termine*` cerca prefissi espliciti; i suggerimenti
non avviano ricerche. I risultati mostrano percorso, formato ed estratto: clic
sul titolo o Invio apre direttamente il file nell'app Windows associata.

**Impostazioni** contiene filtri, ordinamento, cartella, sync, rebuild, recupero,
diagnostiche, pulizia, lingua e tema. I filtri valgono solo nella sessione e
si azzerano al cambio cartella; un riepilogo segnala le restrizioni attive.
Italiano/inglese e tema chiaro/scuro persistono. La pulizia richiede conferma
e non tocca sorgenti o dati v1.

**Scorciatoie:** Ctrl+L ricerca, Ctrl+O selezione cartella, F5 sync, Tab controlli,
Invio ricerca/apertura risultato. Finestra minima 900×640 pixel logici.

Componenti QML separati in `qml/`, asset originali in `assets/`, rigenerazione
con `python scripts/dev/generate_luma_assets.py` dalla root.

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

[Redesign Luma e verifiche](../docs/LUMA_DESKTOP.md)
