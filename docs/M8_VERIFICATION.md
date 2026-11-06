# Verifica M8 — Desktop completo

Data: 6 novembre 2026. Verifica locale su Windows 11 x64 (build 26200), Python 3.12.2,
PySide6 6.12.0 e pytest 8.3.5. Nessuna esecuzione remota della CI verificata.

## Implementazione

Pacchetto `frontend/` separato, launcher `local-document-search-desktop`, Qt Widgets in italiano.
Composizione, startup, selezione, polling, pulizia e chiusura passano da un worker desktop;
ricerca e dettagli utilizzano le Future M7. Nessun algoritmo IR duplicato, IPC o accesso UI allo storage.

Informativa visibile prima di Continua e del sync automatico, selezione ricorsiva, ricerca con Invio,
pagine da 50, anteprima in testo semplice, apertura tramite URL locale e applicazione predefinita.
Polling 200 ms senza accumulo, indicatore animato, progresso, check 1,5 s, errori riprovabili,
pulizia confermata a job fermo e chiusura con attesa. Risposte obsolete ignorate; cambio snapshot
durante paginazione riporta alla prima pagina. CLI e contratti backend invariati.

## Comandi ed esiti

Ambiente virtuale locale: `backend/.venv`.

```powershell
# Da backend/
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q

# Da root/
backend/.venv/Scripts/python.exe -m pip install -e "./frontend[dev]"
backend/.venv/Scripts/python.exe -m pip check

# Da frontend/
../backend/.venv/Scripts/python.exe -m pytest -q
```

- Backend: **314 passed, 5 skipped**; skip di piattaforma già documentati in M7.
- Frontend: **24 passed**, nessuno skip.
- Installazioni editable e `pip check`: riusciti.
- Ambiente virtuale temporaneo separato con il solo backend: installazione riuscita,
  PySide6 assente verificato con `importlib.util.find_spec`, import CLI e `--help` riusciti.
- Dopo l'ultima correzione della gestione startup/anteprima: 4 test pertinenti superati (20 deselected).
- CI estesa: prima verifica backend/CLI senza Qt, poi installazione frontend e test Qt offscreen.

## Evidenze automatiche

- Informativa precedente alla composizione; Invio senza ricerca automatica; campo convertito da Qt al tipo del contratto.
- Zero risultati, pagine della stessa versione, nuova versione e ritorno alla prima, invalidazione durante tale ritorno.
- Successi/errori tardivi dopo cambio query, campo o directory; anteprima tardiva ignorata e recupero versione rimossa.
- Polling non accodato quando lo stato è lento; check non riavviato per lo stesso job; errore e controlli durante lavoro.
- Conferma/annullamento pulizia, errore riprovabile, startup fallito ripetibile e storage incompatibile senza sorgente recuperabile.
- Worker reali bloccati con eventi durante build, ricerca e anteprima: timer Qt continuano a eseguire;
  chiusura attende il rilascio. Anche la composizione in corso viene attesa.
- Corpus sintetico reale di 55 TXT: 50+5 risultati, testo completo letterale, riavvio no-change,
  snapshot invariato, seconda sessione rifiutata, pulizia con tutti i sorgenti preservati.
- Sorgente spostata dopo indicizzazione: avviso visibile e ricerca sullo snapshot conservato.
- Apertura file: assente, URL locale con spazi, richiesta al servizio desktop e fallimento del servizio.
- Controllo statico dei confini frontend; backend senza dipendenza dichiarata da Qt.

## Verifica visiva e limiti

Finestra nativa Windows ispezionata con computer-use, corpus temporaneo di 55 TXT e 1 Markdown:
informativa leggibile, Continua, ripristino e sync no-change, query `machine "learning"` con Invio,
56 risultati, testo completo del primo risultato, seconda pagina con 6 righe e chiusura regolare.
Layout a 1100×720 senza sovrapposizioni osservate. Corpus e storage sono fuori dal repository.

L'apertura nell'applicazione esterna è verificata automaticamente al confine QDesktopServices,
non tramite una matrice di applicazioni associate. Qt segnala l'invio della richiesta, non garantisce
che il programma esterno riesca poi a leggere il documento ([documentazione Qt](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDesktopServices.html)).
I test con worker rallentati dimostrano la gestione asincrona, non un benchmark di latenza o memoria.
Nessuna soglia prestazionale inventata; corpus di scala, packaging standalone, licenze di distribuzione
e Windows senza Python restano M9. Linux/offscreen configurato in CI, non verificato localmente su Linux.

Durante una ripetizione nativa successiva all'ispezione di accessibilità, Windows ha emesso una
diagnostica COM `0x8001010d`; il processo ha comunque concluso con 24 passed ed exit code 0.
I test automatici ora scelgono offscreen per isolarsi dalla sessione desktop; la verifica visiva
rimane nativa e separata. Il primo run nativo da 22 test era terminato senza tale diagnostica.
Il run completo offscreen successivo ha concluso con 24 passed senza diagnostiche COM.
