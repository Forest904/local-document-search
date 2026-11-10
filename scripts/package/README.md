# Build, installer e pubblicazione

La [release 0.2.0](https://github.com/Forest904/local-document-search/releases/tag/v0.2.0) distribuisce l’installer collaudato dal commit `3b78203`, checksum e manifest pubblico. [Accettazione](../../docs/V2_08_ACCEPTANCE.md), [audit del payload](../../docs/V2_07_INSTALLER.md).

## Build Windows x64

Prerequisiti: Windows 11 x64, **CPython 3.12.2 x64**, Visual Studio 2022 Build Tools con C++ x64 e Windows SDK, **Inno Setup 6.7.3**, Git e accesso ai download delle dipendenze. Lo script non installa tool di sistema o usa il Python generico del PATH. `ISCC.exe` è cercato nelle installazioni per utente e Program Files (x86); `LDS_ISCC` può indicarlo esplicitamente. Hash del compilatore fissato in `build.py`.

Dalla root, PowerShell:

```powershell
./scripts/package/build.ps1
# Interprete esplicito:
./scripts/package/build.ps1 -Python 'C:/percorso/python.exe'
# Candidato da checkout pulito, con controlli prima e durante la build:
./scripts/package/build.ps1 -Release
```

`-Release` rifiuta modifiche tracciate e file non tracciati. Il venv `build/package-venv` è separato dallo sviluppo; il lock fissa strumenti e dipendenze, i package locali sono installati senza editable. `pyside6-deploy --no-install` usa la configurazione standalone versionata; Nuitka può scaricare lo strumento di analisi DLL nella cache utente.

Output in `dist/`: `LocalDocumentSearch-0.2.0-windows-x64-setup.exe`, `.sha256`, `.manifest.json` e ZIP di prova `LocalDocumentSearch-0.2.0-windows-x64.zip` con checksum. Log, configurazione risolta e report Nuitka in `build/package/`.

La build pulisce solo `build/package`; per ricreare l’ambiente rimuovere manualmente il venv dedicato. Manifest e input tracciati rendono riproducibile la procedura, non garantiscono binari identici byte per byte.

## Payload e installer

Il manifest associa file a componente, versione, provenienza, licenza, avviso e sorgente applicabile, oltre a revisione, stato dirty, hash sorgenti, toolchain e comando. La verifica finale rifiuta attribuzioni/avvisi mancanti, dipendenze essenziali o sorgenti Qt assenti, hash errati, database nello staging e moduli Qt solo GPL.

Sono inclusi Python, runtime Microsoft, QML/asset Luma enumerati ricorsivamente e plugin Windows/SVG/ICO necessari. Restano solo import QML e dipendenze binarie effettive: Addons/Pdf/WebEngine nel lock non implicano distribuzione; designer e `.qmltypes` non sono runtime. L’inventario QtBase può includere componenti non usati. Mesa e runtime Microsoft sono distinti da Qt e dagli strumenti di build.

Installer per utente senza elevazione o download; wizard IT/EN, Start e desktop opzionale. Upgrade completo, reinstallazione ammessa, downgrade rifiutato. Chiudere l’app prima di installare/disinstallare. Dati v2 conservati per default anche in silenzioso; cancellazione solo esplicita nel wizard. Nessun updater online.

`TERMS-IT.txt` è il testo approvato nella sostanza dal titolare; `TERMS-EN.txt` è informativo. Il wizard mostra i termini senza casella di accettazione. `licenses/` conserva testi/avvisi; `licenses/upstream/SOURCES.json` identifica le fonti upstream e `licenses/SOURCES.json` gli archivi sorgente incorporati e verificati: QtBase, QtDeclarative, QtShaderTools, QtSvg, QtSCXML, PySide6 e Mesa. La build aggiunge licenze Python e delle distribuzioni installate. `QT_REPLACEMENT.txt` descrive sostituzione delle DLL e limiti; [politica e diritti](../../docs/SECURITY_AND_PRIVACY.md#distribuzione-e-diritti).

## Diagnostica e collaudo

Il payload include i tre script V2-02 in `diagnostics/`, attribuiti e verificati nel manifest. Generare il corpus sul PC di sviluppo con `experiments/v2_benchmark.py generate`, poi eseguire da PowerShell:

```powershell
& '<installazione>/LocalDocumentSearch.exe' --diagnostic '<corpus>' '<output-nuovo>' --storage-root '<storage-nuovo>' --cycles 3 --samples 100 --warmups 5
```

Corpus, output e storage devono essere distinti; lo storage personale v2 è rifiutato. Il runner verifica hash del corpus e script, crea copie per ciclo e processi compilati nuovi per fase. L’EXE è GUI: leggere `report.json`, non la console. Una fase fallita lascia `INCOMPLETE`; `budget_status` indica separatamente i sei limiti T08.

Per lo ZIP di prova, estrarre fuori repo in un percorso con spazi/Unicode e usare corpus sintetici. Nel solo processo rimuovere `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV`, `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH` e isolare `LOCALAPPDATA`; non alterare l’account. Verificare lo storage prima delle prove.

La [procedura del candidato](../../docs/V2_08_ACCEPTANCE.md#procedura-del-candidato) e gli [scenari T01–T21](../../docs/TEST_STRATEGY.md) coprono reader, ricerca/apertura, sync/lifecycle, fault, doppia istanza, dati v1 e sorgenti intatti, lingue, temi e accessibilità. Misurare il compilato separatamente dal backend sorgente. Un avvio sul PC di sviluppo non prova portabilità: servono Windows pulito e account standard distinto.

## Pubblicazione su GitHub

Il [workflow](../../.github/workflows/backend.yml) esegue i test su Windows/Ubuntu al push su `main`. Solo dopo test verdi, se il tag `v<versione>` manca, costruisce su `windows-2022` da checkout pulito, verifica hash/manifest, carica gli asset in draft e pubblica. Errori prima della pubblicazione bloccano la release; un upload fallito ripulisce draft e tag creati dal job. Un tag esistente evita una nuova build automatica. `workflow_dispatch` verifica la build senza pubblicare.

Per una nuova versione allineare backend/frontend e dipendenza backend, `INSTALLER_VERSION` in `build.py`, `AppVersion`/`OutputBaseFilename` in `installer.iss`, versioni in `payload_audit.py`, `ISTRUZIONI.txt` e titoli dei termini IT/EN:

```powershell
python scripts/package/release_metadata.py version
python scripts/package/release_metadata.py verify --revision <commit-SHA>
```

Il primo rifiuta discrepanze; il secondo verifica l’installer e genera `dist/public/` senza percorsi assoluti privati. Tag e manifest identificano il commit di build, non un merge/documentazione successivo. Installer e corpus restano fuori Git; toolchain incompatibile interrompe il job.

Verifica del 9 novembre 2026: run `42702410786` verde Windows/Ubuntu, build/pubblicazione saltate perché il tag esisteva; run manuale `42702437611` verde con build/verifica, senza pubblicazione. Il precedente `42700577845` falliva per percorso Build Tools fisso della licenza Microsoft: risolto tramite `vswhere`. Il binario manuale non sostituisce quello 0.2.0 collaudato.

Fonti della procedura: [pyside6-deploy](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html), [Nuitka](https://nuitka.net/user-documentation/user-manual.html), [Qt](https://doc.qt.io/qt-6/licensing.html).

## Nome pubblico e reinstallazione

Nome pubblico stabile: Local Document Search. Installazione in `%LOCALAPPDATA%/Programs/LocalDocumentSearch`, dati in `%LOCALAPPDATA%/LocalDocumentSearch/Data`. AppId e mutex rimangono invariati. Il numero tecnico di release resta nei metadati e nei nomi degli artefatti.

L'installer rifiuta la precedente installazione in `Programs/LocalDocumentSearchV2`, anche in modalit? silenziosa (messaggio nel log): disinstallarla conservando i dati e poi reinstallare. Nessuna migrazione: onboarding e indicizzazione ripartono; `LocalDocumentSearchV2` e i dati storici nella radice `LocalDocumentSearch` restano intatti. Gli aggiornamenti successivi usano il percorso neutro. La pulizia esplicita del disinstallatore riguarda soltanto `LocalDocumentSearch/Data`, con controllo di lock e reparse point anche negli antenati.
