# Avvio e riavvio del desktop attuale da VS Code

Il task avvia il desktop Qt Widgets v1; la [UI Qt Quick v2](../../docs/UX_WINDOWS.md) non è ancora implementata.

Su Windows, aprire la root del repository e scegliere **Terminal → Run Task →
Local Document Search: avvia / riavvia**. È un solo task: backend e frontend condividono
il processo desktop, senza server, porte o due comandi separati.

## Primo avvio

Prerequisiti: Python >=3.12 **x64** (consigliato 3.12), PowerShell Windows e accesso a PyPI
o a una cache pip completa per installare i pacchetti. Non servono attivazione manuale del venv,
installazione globale dei requirements o VS Code Python Extension.

Il task cerca prima Python 3.12 tramite `py`, poi una versione >=3.12 disponibile tramite
`py`/`python`/`python3`. Crea `backend/.venv`, installa le versioni runtime e build del lock,
poi i due pacchetti locali in modalità editable. Le dipendenze opzionali di test non sono necessarie
all'avvio e non vengono installate automaticamente. Non installa Python o strumenti di sistema.

La finestra mantiene l'informativa M8: premi **Continua** per aprire il backend persistente e
sincronizzare la cartella salvata; alla prima sessione scegli la cartella dei documenti.

## Avvii successivi e riavvio

- Riusa il venv, controllando versioni installate, dipendenze transitive e provenienza dei pacchetti editable.
- Confronta anche lock, `pyproject.toml`, versione Python e percorso del checkout con l'ultimo setup riuscito.
- Se tutto coincide, **salta pip e la rete**. Le modifiche al codice sorgente sono già visibili grazie agli editable.
- Se un pacchetto manca o ha una versione diversa, ripristina il lock. Cambi di configurazione o checkout
  provocano la reinstallazione dei pacchetti editable. Un errore impedisce di dichiarare pronto l'ambiente.
- Prima di modificare l'ambiente chiude le sessioni desktop riconosciute, anche nascoste o in background.
  Identifica il wrapper di questo checkout e gli avvii manuali standard `-m local_document_search_desktop.main`
  o `local-document-search-desktop.exe` dello stesso utente. Non termina genericamente tutti i processi Python.
- Richiede la chiusura normale della finestra, che attende job e letture. Dopo **30 secondi** forza
  l'arresto dei soli processi identificati ancora presenti, verificandone nuovamente identità e data di avvio.
  Uno snapshot non completato non viene pubblicato; il recovery persistente resta quello M5–M7.
- Avvia una nuova sessione e termina il task solo quando la finestra esiste. Puoi quindi rilanciare
  lo stesso task per riavviare. Terminare il terminale del task non equivale a chiudere l'app.

Non vengono eliminati documenti, impostazioni o indici. Processi di altri utenti, altri wrapper di checkout
e modalità di avvio personalizzate non riconosciute restano intatti: se occupano lo storage, il backend
mostra il suo errore di lock e occorre chiuderli esplicitamente.
Un mutex impedisce due preparazioni contemporanee dello stesso checkout, anche fuori da VS Code.

## Script e responsabilità

| File | Responsabilità |
|---|---|
| `start.ps1` | Master: serializza e orchestra ambiente → arresto → dipendenze → avvio |
| `environment.ps1` | Cerca Python e crea/valida il virtualenv |
| `dependencies.py` | Controlla installazioni e configura soltanto ciò che serve |
| `requirements.lock.txt` | Versioni runtime/build riproducibili per lo sviluppo Windows |
| `windows-processes.ps1` | Identità dei processi, parsing degli argomenti e chiusura delle finestre |
| `stop-app.ps1` | Arresto ordinato, timeout e arresto forzato circoscritto |
| `start-app.ps1` | Lancia il desktop e verifica che la finestra sia pronta |
| `run_desktop.py` | Lancia senza ereditare le pipe del task, registra il PID effettivo e richiama il desktop |

Solo `.vscode/tasks.json` è versionato; le impostazioni personali VS Code restano ignorate.
PID/token e diagnostica locale sono in `runtime/`, esclusa da Git. Il PID registrato non è mai
usato da solo per decidere quale processo terminare. Il fingerprint del setup è nel virtualenv.

## Esecuzione senza VS Code

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/dev/start.ps1
# Bootstrap con un interprete esplicito, timeout maggiore per job lunghi:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/dev/start.ps1 -Python "C:\Python312\python.exe" -CloseTimeoutSeconds 120
# Solo chiusura:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/dev/stop-app.ps1 -Repository "$PWD"
```

`-Python` seleziona l'interprete quando il venv non esiste. Un ambiente esistente ma incompatibile
produce un errore esplicito; non viene cancellato automaticamente. La policy Bypass vale soltanto
per il processo PowerShell del task, senza modificare le impostazioni permanenti.
Se manca Python o un download fallisce, il task termina con codice non zero e un messaggio diagnostico.
Errori del desktop sono in `runtime/desktop-stderr.log`.

Per aggiornare dipendenze, allineare `requirements.lock.txt` ai due `pyproject.toml`, includendo
le dipendenze transitive, e verificare un avvio pulito. Il lock di sviluppo non sostituisce
la verifica del pacchetto distribuito.

## Verifiche

Con l'ambiente di sviluppo/test installato:

```powershell
backend/.venv/Scripts/python.exe -m pytest scripts/tests -q
```

Verificati localmente su Windows 11 / Python 3.12.2: 10 test automatici; avvio caldo con pip saltato;
riavvio con cambio PID; copia pulita in un percorso con spazi, creazione venv, installazione e finestra pronta.
Verificati anche ripristino reale di `mdurl` dopo disinstallazione nel venv temporaneo e successivo
avvio caldo senza pip; chiusura di finestra nascosta, timeout con arresto forzato su una finestra
sintetica che rifiuta la chiusura e conservazione di un processo Python estraneo in parallelo.
Verificata la sostituzione di una sessione avviata manualmente tramite modulo Python.
Una regressione automatica verifica che il processo del task termini con GUI ancora aperta e
output catturato: il lancio non eredita le pipe del task. Backend e frontend non sono stati modificati.
Il cold start ha usato la cache pip locale: non simula indisponibilità di rete o un Windows senza Python.

Il task usa il formato process documentato nello [schema ufficiale VS Code](https://code.visualstudio.com/docs/reference/tasks-appendix).
