# Distribuzione personale Windows x64 (M9)

Da PowerShell, nella radice del repository:

```powershell
./scripts/package/build.ps1
# Oppure specificare il percorso completo di CPython 3.12.2 x64:
./scripts/package/build.ps1 -Python 'C:/percorso/python.exe'
```

Prerequisiti di build: Windows 11 x64, CPython 3.12.2 x64, Visual Studio 2022
Build Tools con C++ x64 e Windows SDK, Git e accesso ai download delle dipendenze.
La toolchain verificata è registrata nel report M9 e nel manifest dell'artefatto.
Il comando non usa il Python generico del PATH e non installa strumenti di sistema.

`build/package-venv` è separato dall'ambiente di sviluppo. Il lock fissa gli strumenti
Python e tutte le dipendenze; backend e frontend vengono installati senza editable.
`pyside6-deploy --no-install` usa la configurazione versionata in modalità standalone.
Nuitka può scaricare il proprio strumento di analisi DLL nella cache utente.
Il pacchetto include i runtime Microsoft necessari; nessun installer o updater.

Output: `dist/LocalDocumentSearch-0.1.0-windows-x64.zip` e relativo `.sha256`.
Log, configurazione risolta e report Nuitka restano in `build/package/`.
Lo ZIP include istruzioni, licenze, report compilatore e `BUILD-MANIFEST.json`:
revisione, stato dirty, hash dei sorgenti, versioni, toolchain, comando e hash dei file.
Lo SHA256 esterno identifica lo ZIP, evitando un riferimento circolare nel manifest.
Il controllo finale rifiuta dipendenze essenziali mancanti e database nello staging.

La build pulisce soltanto `build/package`; non tocca corpus, dati app o ambiente di sviluppo.
Riproducibilità indica input/versioni e procedura tracciati, non ZIP identici byte per byte.
Per una build da zero eliminare manualmente l'ambiente dedicato e rieseguire il comando.

## Licenze e ambito

Uso personale concordato: nessuna pubblicazione e nessuna licenza del progetto aggiunta.
`licenses/` contiene testi originali LGPL/GPL e avvisi QtBase 6.12.0 con provenienza
in `SOURCES.json`; durante la build si aggiungono le licenze delle distribuzioni installate
e Python. L'inventario QtBase include anche componenti non usati dal programma.
I pacchetti Qt Addons/Pdf/WebEngine appartengono al lock di build di PySide6;
non vengono inclusi automaticamente tutti nel prodotto.

Fonti: [pyside6-deploy](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html),
[Nuitka](https://nuitka.net/user-documentation/user-manual.html),
[licenze Qt](https://doc.qt.io/qt-6/licensing.html).

## Accettazione locale

Estrarre lo ZIP fuori dal repository, in un percorso con spazi e Unicode. Avviare
con `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV`, `QT_PLUGIN_PATH` e `QML2_IMPORT_PATH`
rimossi dall'ambiente del solo processo; impostare `LOCALAPPDATA` su una directory
di prova esterna al repository. Non alterare le variabili dell'account.
Usare soltanto corpus sintetici e verificare che lo storage sia quello isolato.

Percorsi da registrare: informativa, selezione, TXT/MD/PDF, ricerca per campo/AND/frasi,
pagine da 50, anteprima e apertura, add/modify/remove, restart/no-change,
errori con snapshot precedente, doppia istanza, chiusura durante job,
arresto forzato e recovery, sorgente assente e pulizia dei soli dati app.
Misurare il processo compilato separatamente dal benchmark backend.
Esiti e limiti effettivi: [M9_VERIFICATION](../../docs/M9_VERIFICATION.md).

Per decisione dell'utente del 2026-11-07 la prova Windows pulito/account standard distinto è rinviata alle versioni successive. M9 richiede il collaudo dello ZIP finale sul PC attuale; la prova locale non dimostra portabilità su ambiente pulito.
