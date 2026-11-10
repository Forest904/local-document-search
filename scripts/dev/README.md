# Avvio e riavvio in sviluppo

Su Windows, aprire la root in VS Code e scegliere **Terminal → Run Task → Local Document Search: avvia / riavvia**. Il desktop e il backend condividono un processo.

Servono Python >=3.12 **x64** (consigliato 3.12), PowerShell e PyPI o cache pip completa. Il task cerca prima Python 3.12 tramite `py`, poi una versione compatibile tramite `py`/`python`/`python3`. Crea `backend/.venv`, installa il [lock](requirements.lock.txt) e i pacchetti locali editable; non installa Python, tool di sistema o dipendenze opzionali di test. Non serve attivare manualmente il venv.

## Comportamento del riavvio

- Verifica versioni, dipendenze transitive, provenienza editable e fingerprint di lock, pyproject, interprete e checkout. Se coincidono salta pip e rete; altrimenti ripristina il setup necessario.
- Prima di modificare l’ambiente chiude le sessioni riconosciute: wrapper di questo checkout e avvii manuali standard dello stesso utente tramite modulo o entrypoint. Richiede chiusura normale, poi dopo **30 secondi** forza soltanto i processi identificati, ricontrollando identità e data di avvio.
- Non termina genericamente Python, processi di altri utenti o wrapper di altri checkout. Se una sessione non riconosciuta occupa lo storage, va chiusa esplicitamente.
- Un mutex serializza il setup del checkout. Il task termina quando la finestra è pronta; chiudere il terminale non chiude l’app. Non elimina documenti, indici o preferenze.

Al primo avvio dell’app seguire l’[informativa e la selezione cartella](../../frontend/README.md#uso).

## Uso senza VS Code

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/dev/start.ps1
# Interprete iniziale esplicito e attesa più lunga prima dell’arresto forzato:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/dev/start.ps1 -Python "C:\Python312\python.exe" -CloseTimeoutSeconds 120
# Solo chiusura:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/dev/stop-app.ps1 -Repository "$PWD"
```

`-Python` vale alla creazione del venv; un ambiente incompatibile produce errore, senza essere cancellato. Bypass riguarda solo il processo PowerShell. Download/setup falliti terminano con codice non zero; errori desktop in `runtime/desktop-stderr.log`.

## Manutenzione

`start.ps1` orchestra `environment.ps1`, `dependencies.py`, `stop-app.ps1` e `start-app.ps1`. `windows-processes.ps1` verifica l’identità dei processi; `run_desktop.py` evita di ereditare le pipe del task. PID/token e log sono in `runtime/`, fuori Git; un PID da solo non autorizza l’arresto. Il fingerprint è nel venv. Solo `.vscode/tasks.json` è versionato.

Per aggiornare le dipendenze, allineare lock e pyproject incluse le transitive, poi verificare un avvio pulito. Con gli extra dev installati:

```powershell
backend/.venv/Scripts/python.exe -m pytest scripts/tests -q
```

Verifica storica su Windows 11/Python 3.12.2: 10 test automatici; avvio caldo senza pip, riavvio con nuovo PID, checkout con spazi e venv nuovo, ripristino di `mdurl`, finestra nascosta e arresto forzato circoscritto, processo Python estraneo preservato, avvio manuale riconosciuto e task concluso con GUI aperta. Il cold start usava la cache pip: non prova un Windows senza Python o indisponibilità di rete.
