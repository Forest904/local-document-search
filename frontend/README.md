# Desktop Luma

PySide6/Qt Quick, QML e backend v2 nello stesso processo. [Installazione e avvio](../README.md#avvio-dal-sorgente).

## Uso

Al primo avvio premi **Accetta e scegli una cartella**. La home appare quando l’indice è ricercabile; agli avvii successivi il catalogo viene recuperato e sincronizzato in background.

Invio o la lente eseguono la query; `termine*` cerca prefissi e `*termine` cerca suffissi. Digitare propone suggerimenti anche dopo `*`: selezionarne uno sostituisce la clausola con il termine completo e avvia la ricerca. I risultati mostrano estratti evidenziati, tempo di ricerca e pagine da 20. Clic sul titolo o Invio sul risultato apre il viewer interno per PDF, TXT e MD. Il viewer offre anche l'apertura nell'app Windows associata.

TXT e Markdown mostrano il sorgente in sola lettura, con numeri di riga, salto al primo match e a capo visivo selezionabile. **Ctrl+F** cerca letteralmente nel file aperto; **Escape** chiude Trova e poi torna ai risultati. Il limite del reader è 10 MiB, 100.000 righe e 100.000 caratteri per riga; oltre soglia si può usare l'app associata. [Dettagli V2-12](../docs/V2_12_TEXT_READER.md).

**Impostazioni**, accessibile dalla home, contiene campo, formati, ordine, cartella, sync, rebuild, diagnostiche, pulizia, lingua e tema. Filtri solo di sessione, azzerati al cambio cartella/riavvio; lingua e tema persistono. Il filtro sottocartella, il recupero del precedente e i dettagli completi restano API backend, senza controlli dedicati nella UI.

Nella barra di ricerca, `.txt`, `.md` e `.pdf` isolati da spazi applicano i rispettivi filtri formato all'invio; più estensioni selezionano più formati. Per esempio `contratto .pdf` cerca `contratto` nei PDF. Una sola estensione prepara il filtro senza cercare. Il riepilogo dei filtri offre un'icona × per ripristinare le opzioni.

Scorciatoie: **Ctrl+L** ricerca, **Ctrl+O** cartella, **F5** sync, **Esc** dai risultati alla home. Finestra minima 900×640 pixel logici. [Specifica UX](../docs/UX_WINDOWS.md).

## Sviluppo e verifiche

Dalla root, con l’ambiente del README:

```powershell
backend/.venv/Scripts/python.exe -m pip install -e "./backend[dev]" -e "./frontend[dev]"
backend/.venv/Scripts/python.exe -m pytest frontend/tests
```

I test usano `QT_QPA_PLATFORM=offscreen` per default; `windows` abilita il plugin nativo. Il probe `experiments/run_v2_desktop.py` usa corpus sintetico e storage temporaneo; catture e report restano fuori Git. Il rendering offscreen non prova font Windows, Narrator o avvio del pacchetto installato. [Evidenze desktop](../docs/V2_08_ACCEPTANCE.md#evidenze-desktop-precedenti-al-candidato).

QML in `src/local_document_search_desktop/qml/`; [asset e provenienza](src/local_document_search_desktop/assets/README.md), rigenerabili con `python scripts/dev/generate_luma_assets.py`.
