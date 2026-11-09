# Packaging Qt Quick V2-07 — ZIP di prova e installer Windows x64

`build.ps1` produce anche `dist/LocalDocumentSearch-0.2.0-windows-x64-setup.exe`
e i relativi `.sha256` e `.manifest.json`. Richiede Inno Setup 6.7.3: il
compilatore `ISCC.exe` è cercato nell'installazione per utente o in Program
Files (x86); `LDS_ISCC` può specificare un percorso diverso. L'hash del
compilatore è bloccato in `build.py`.

Per il candidato V2-08 usare `./scripts/package/build.ps1 -Release` da una
revisione Git pulita. Questa modalità rifiuta modifiche tracciate o file non
tracciati prima e durante la build. Il payload include i tre script del benchmark
V2-02 in `diagnostics/`, attribuiti e verificati nel manifest.

L'eseguibile installato espone la diagnostica da PowerShell:

```powershell
& '<installazione>/LocalDocumentSearch.exe' --diagnostic '<corpus>' '<output-nuovo>' --storage-root '<storage-nuovo>' --cycles 3 --samples 100 --warmups 5
```

Il corpus è generato con `experiments/v2_benchmark.py generate` sul PC di
sviluppo. Corpus, output e storage devono essere directory distinte; lo storage
personale v2 è rifiutato. Il runner verifica gli hash del corpus e dei propri
script nel payload, crea copie per ciclo e avvia un processo compilato nuovo
per fase. `report.json` resta `INCOMPLETE` se una fase fallisce; `budget_status`
indica separatamente se i sei limiti T08 sono rispettati. L'eseguibile è GUI:
consultare `report.json` nell'output anziché attendersi output nella console.

L'EXE installa per utente, senza elevazione o download. Wizard IT/EN, menu
Start e desktop opzionale; upgrade completo nella stessa installazione,
reinstallazione ammessa e downgrade rifiutato. Chiudere l'applicazione prima
di installare o disinstallare. I dati v2 restano nel profilo, salvo scelta
esplicita nel wizard di disinstallazione; la modalità silenziosa li conserva.
`TERMS-IT.txt` contiene i termini italiani approvati nella sostanza dal titolare;
`TERMS-EN.txt` è una traduzione informativa. Il wizard li mostra prima
dell'installazione senza casella di accettazione.
`QT_REPLACEMENT.txt` descrive la prova di sostituzione delle DLL Qt e i suoi
limiti; `licenses/upstream/SOURCES.json` identifica le fonti upstream con hash.
La build incorpora gli archivi sorgente QtBase, QtDeclarative, QtShaderTools,
QtSvg, QtSCXML, PySide6 e Mesa; li verifica con SHA-256 prima della compilazione
dell'installer. `BUILD-MANIFEST.json` associa ogni file del payload a componente,
versione, provenienza, licenza, avviso e sorgente quando disponibile. Un file
senza attribuzione o avviso interrompe la build. Mesa llvmpipe e il runtime
Microsoft restano distinti dai moduli Qt e dagli strumenti usati solo in build.

La procedura genera anche uno ZIP di prova del payload Qt Quick. Il collaudo pubblico resta V2-08. M9 resta [parzialmente accettata](../../docs/BASELINE.md).

Da PowerShell, nella radice del repository:

```powershell
./scripts/package/build.ps1
# Oppure specificare il percorso completo di CPython 3.12.2 x64:
./scripts/package/build.ps1 -Python 'C:/percorso/python.exe'
```

Prerequisiti di build: Windows 11 x64, CPython 3.12.2 x64, Visual Studio 2022
Build Tools con C++ x64 e Windows SDK, Inno Setup 6.7.3, Git e accesso ai download delle dipendenze.
La toolchain verificata è registrata nel report M9 e nel manifest dell'artefatto.
Il comando non usa il Python generico del PATH e non installa strumenti di sistema.

`build/package-venv` è separato dall'ambiente di sviluppo. Il lock fissa gli strumenti
Python e tutte le dipendenze; backend e frontend vengono installati senza editable.
`pyside6-deploy --no-install` usa la configurazione versionata in modalità standalone.
Nuitka può scaricare il proprio strumento di analisi DLL nella cache utente.
Il pacchetto include i runtime Microsoft necessari; non ha updater online.

Output di prova: `dist/LocalDocumentSearch-v2-06-prototype-windows-x64.zip` e relativo `.sha256`; l'installer EXE è descritto sopra.
Log, configurazione risolta e report Nuitka restano in `build/package/`.
Lo ZIP include istruzioni, licenze, report compilatore e `BUILD-MANIFEST.json`:
revisione, stato dirty, hash dei sorgenti, versioni, toolchain, comando e hash dei file.
Lo SHA256 esterno identifica lo ZIP, evitando un riferimento circolare nel manifest.
Il controllo finale rifiuta dipendenze essenziali mancanti, database nello
staging, moduli Qt solo GPL, sorgenti Qt assenti e file non attribuiti.

La build pulisce soltanto `build/package`; non tocca corpus, dati app o ambiente di sviluppo.
Riproducibilità indica input/versioni e procedura tracciati, non ZIP identici byte per byte.
Per una build da zero eliminare manualmente l'ambiente dedicato e rieseguire il comando.

## Licenze e ambito

La distribuzione v1 era personale e non includeva una licenza del progetto. La politica pubblica v2 è [documentata separatamente](../../docs/SECURITY_AND_PRIVACY.md#distribuzione-e-diritti).
`licenses/` contiene testi originali LGPL/GPL e avvisi QtBase 6.12.0 con provenienza
in `SOURCES.json`; durante la build si aggiungono le licenze delle distribuzioni installate
e Python. L'inventario QtBase include anche componenti non usati dal programma.
I pacchetti Qt Addons/Pdf/WebEngine appartengono al lock di build di PySide6;
la build conserva solo gli import QML e la chiusura delle dipendenze binarie
effettive. I file del designer QML e i metadati `.qmltypes` non sono runtime.

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
pagine da 50, estratti e apertura diretta, add/modify/remove, restart/no-change,
errori con snapshot precedente, doppia istanza, chiusura durante job,
arresto forzato e recovery, sorgente assente e pulizia dei soli dati app.
Misurare il processo compilato separatamente dal benchmark backend.
Esiti e limiti del prototipo Qt Quick: [V2_06_DESKTOP](../../docs/V2_06_DESKTOP.md).
La prova M9 v1 resta [storica](../../docs/archive/v1/M9_VERIFICATION.md).

La prova su Windows pulito/account standard distinto appartiene a V2-08.
L'avvio del prototipo sul PC di sviluppo non dimostra portabilità su ambiente pulito.

## Risorse Luma

La build enumera ricorsivamente i componenti QML, copia QML e asset nel payload
e verifica che ogni risorsa prevista sia presente. Conserva i plugin Windows,
SVG, ICO e SVG icon engine con le rispettive dipendenze. L'icona Luma è usata
per finestra, eseguibile e installer. Le nuove prove sono nel
[rapporto Luma](../../docs/LUMA_DESKTOP.md), separate dal collaudo storico V2-07.
