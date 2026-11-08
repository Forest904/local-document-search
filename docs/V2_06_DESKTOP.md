# V2-06 — Verifica desktop Qt Quick

**Data:** 8 novembre 2026. **Revisione di partenza:**
`2ad36c1aeff3ecd0cc5c478ccd401e20861d9dd0`; working tree modificato.
Questa relazione riguarda il sorgente e il prototipo standalone, non
l'installer finale o l'accettazione V2-08.

## Implementazione

Il comando desktop esistente avvia `QGuiApplication` e QML nello stesso
processo del backend v2. Controller e modello Qt mantengono ricerca, suggerimenti,
anteprima e job fuori dal thread grafico e scartano risposte obsolete.
La UI espone filtri, rilevanza/percorso, paginazione, sync, cancel, retry,
rebuild e recovery. L'evidenziazione usa gli intervalli Unicode del backend:
il testo acquisito viene escapato prima del markup, senza caricare HTML dei
documenti. `DesktopPreferences` usa una tabella nel catalogo v2, separata
dagli snapshot; la pulizia confermata azzera lingua e tema. La CLI resta
indipendente da Qt.

## Ambiente e comandi

Windows 11 Home build 26200, Python 3.12.2 x64, PySide6 6.12.0,
pytest 8.3.5; Ryzen AI 7 350, 32 GB RAM. Risultati locali:

| Comando | Esito |
|---|---|
| `cd backend; .venv/Scripts/python.exe -m pytest -q` | 384 passed, 6 skipped |
| `cd frontend; ../backend/.venv/Scripts/python.exe -m pytest -q` | 27 passed |
| `backend/.venv/Scripts/python.exe -m pytest scripts/tests -q` | 17 passed |
| `backend/.venv/Scripts/python.exe -m pip check` | PASS |
| `backend/.venv/Scripts/python.exe experiments/run_homework3.py` | PASS |
| `backend/.venv/Scripts/python.exe experiments/run_v2_desktop.py experiments/results/v2-target/source experiments/results/v2-06-target` | PASS dal sorgente |

Il probe usa il corpus sintetico V2-02 già presente: 10.000 documenti,
299.923.100 byte attesi di testo estratto. Ha trovato 10.000 risultati
per `marcatoreuniversale`, completato 421 cicli ricerca/anteprima durante
rebuild e salvato quattro catture IT/EN × chiaro/scuro. Il build iniziale
è diventato ricercabile dopo 193,7 s; durata totale 375,6 s. Il massimo
intervallo campionato nel loop Qt è stato **635 ms**, incluse le catture
schermo: il probe dimostra funzionamento concomitante, ma non attribuisce
il massimo al solo carico del backend. Il probe non è il
benchmark T08 del pacchetto e non confronta p95 di ricerca o memoria.

La build con `python scripts/package/build.py` ha prodotto lo ZIP prototipo
`LocalDocumentSearch-v2-06-prototype-windows-x64.zip`, SHA-256
`ffcca1c43e2cfadee3eb7ea5f5ecbddc79834d52a8b49604b60873af0fea6487`.
Il manifest registra revisione, working tree modificato, toolchain,
pacchetti e hash dei file. L'archivio supera `testzip` e i 2.829 hash del
manifest corrispondono. Anche i 68 hash dei sorgenti corrispondono ai file correnti.
Estratto fuori dal repository e avviato con
`LOCALAPPDATA` temporaneo: finestra QML, informativa, selezione del corpus
small (100 file), indicizzazione, ricerca su Invio (100 risultati), snippet,
anteprima del primo documento e chiusura verificati via UI nativa.
L'albero di accessibilità Windows espone controlli, risultati e anteprima.
Non sono state eseguite installazione, update o disinstallazione.

## Controlli visivi e limiti

Su Windows il sorgente è stato aperto con una finestra nativa. La vista
iniziale espone nell'albero di accessibilità etichette, pulsanti, filtri,
lingua e tema; il focus iniziale è sul pulsante Continua. Le catture del
probe mostrano risultati, snippet ed evidenziazione dell'anteprima nei
quattro abbinamenti di lingua/tema. Il probe sul corpus small (100 file)
è passato anche con `QT_SCALE_FACTOR` 1, 1,5 e 2: rispettivamente 3, 3 e 4
cicli ricerca/anteprima durante rebuild, con intervalli massimi del loop
durante il rebuild di 50–53 ms. Le catture a 200% mostrano risultati e
anteprima leggibili; la sidebar richiede scrolling verticale. Sono stati
corretti lo spazio dei formati nella sidebar e le dimensioni iniziali della finestra; la
sidebar è scorrevole e la dimensione minima è 900×640 pixel logici.

Le coppie principali testo/sfondo misurano 6,59–15,43:1 con formula WCAG;
il testo sull'evidenziazione misura 10,86:1. `Ctrl+L`, Invio, selezione
del risultato e chiusura sono stati provati via UI nativa. QtTest verifica
anche il passaggio `Tab` dal campo query alla scelta del campo e il ritorno
alla query con `Ctrl+L`.

Restano da registrare prove manuali complete di tabulazione e Narrator (selezione cartella, risultati,
anteprima, job, errore e impostazioni). Le etichette di accessibilità e
i test Qt automatici non sostituiscono l'uso effettivo del lettore di
schermo. L'inventario del payload è un gate distinto;
le licenze e l'installer appartengono a V2-07. I documenti personali e gli
output del probe restano fuori Git.
