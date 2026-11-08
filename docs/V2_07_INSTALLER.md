# V2-07 — Installer offline: audit e collaudo locale

Data: 8 novembre 2026. Versione 0.2.0; revisione
`8780a1012ef226af294e813d77993ae49cc0c4c6` con working tree modificato.
Ambiente: Windows 11 build 26200 x64, CPython 3.12.2, MSVC 2022
19.44.35228.0, CMake 4.3.3, Ninja 1.13.2, Inno Setup 6.7.3.
SHA-256 di `ISCC.exe`:
`0a8757031b33777e4c9cbffee40f11a5062b36d25cbe144c1db73b6102b80ad7`.
EXE finale `dist/LocalDocumentSearch-0.2.0-windows-x64-setup.exe`:
156.112.098 byte, SHA-256
`71EC6896F8521B331570C268FC102E177CB3B989F9E7A8F5F6EF3E9A629674C8`.

L'installer è per utente, senza elevazione o download, in
`%LOCALAPPDATA%\Programs\LocalDocumentSearchV2`. Lo storage v2 è separato in
`%LOCALAPPDATA%\LocalDocumentSearchV2`. I contratti di ricerca e la CLI
Homework non sono cambiati.

## Payload e diritti

La build conserva gli import QML richiesti e la chiusura delle dipendenze PE.
Esclude moduli solo GPL, stili opzionali, file del designer e `.qmltypes`.
`BUILD-MANIFEST.json` elenca 242 file, ciascuno con componente, versione,
provenienza, licenza, avviso e fonte o sorgente applicabile. I 242 hash, le
sette sorgenti e l'hash dell'EXE sono stati ricalcolati senza differenze;
inventario e manifest contano gli stessi file. Sono presenti 47 binari Qt e
nessun modulo Qt solo GPL. La build fallisce per file non attribuiti, avvisi
o archivi sorgente mancanti, hash sorgenti errati e dipendenze PE Qt assenti.

Gli archivi QtBase, QtDeclarative, QtShaderTools, QtSvg, QtSCXML, PySide6 e
Mesa sono incorporati in `sources/` e verificati con gli SHA-256 fissati in
`scripts/package/licenses/SOURCES.json`. Licenze e avvisi installati coprono
anche CPython, OpenSSL, libffi, SQLite, Mesa llvmpipe, runtime Visual C++ e
pacchetti Python. L'inventario distingue gli strumenti di build dal payload
e registra per il runtime Microsoft la provenienza binaria, senza dichiarare
disponibili i sorgenti proprietari. I termini IT/EN coincidono byte per byte
con i testi del payload. Il wizard li mostra senza casella di accettazione.

## Prova di sostituzione LGPL

L'archivio QtBase 6.12.0 è stato estratto sotto `%TEMP%/lds-qt612-rebuild`.
Dopo `vcvars64.bat` in ambiente MSVC x64:

```text
cmake -G Ninja -S <qtbase-src> -B <build> -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=<install> -DQT_BUILD_EXAMPLES=OFF -DQT_BUILD_TESTS=OFF
cmake --build <build> --target Qt6Core.dll --parallel 4
```

Configurazione e collegamento sono riusciti; log in
`%TEMP%/lds-qt612-rebuild/configure.log` e `build-core.log`. SHA-256 DLL
originale `F57ED38AFD95D0306CCA9D88D997F639F70C7628A4F1F064EAE291D579487121`,
DLL ricostruita `AFC3090B7A8F5228710D72715E8CA05B34B16CB455C712C1094829CE8A243074`.
La seconda è stata sostituita solo in una copia dell'installazione. L'app
copiata è rimasta responsiva e la query `meteorite azzurro` ha restituito
`alfa.txt`, `beta.md` e `gamma.pdf` sintetici. La prova dimostra la
sostituibilità con quella build compatibile, non con qualsiasi modifica Qt.

## Collaudo locale

Sul candidato 0.2.0: reinstallazione `exit 0`; installer e disinstallatore
con app aperta `exit 1` lasciandola viva; upgrade da 0.1.9 di prova `exit 0`
con rimozione del file obsoleto presente nel vecchio manifest; downgrade a
0.1.9 rifiutato `exit 1`, versione 0.2.0 conservata; file estraneo conservato.
La disinstallazione silenziosa `exit 0` ha conservato i dati v2. Con lock
occupato, la pulizia `exit 1` ha conservato il marker; retry `exit 0`.
La scelta di cancellazione nella disinstallazione interattiva ha rimosso
applicazione e dati v2. Hash dello storage v1 e dei documenti sintetici
invariati. Il wizard IT/EN ha mostrato i rispettivi termini; quello italiano
ha completato la reinstallazione. L'icona desktop era facoltativa e
inizialmente deselezionata; selezionandola sono stati creati i collegamenti
Desktop e Start. Schermate locali in `build/v2-07-evidence/`, ignorate da Git.
Nessuna elevazione, richiesta di rete o avviso SmartScreen è stato osservato
su questo PC; altri sistemi possono avere avvisi diversi.

Suite: `backend/.venv/Scripts/python.exe -m pytest backend/tests frontend/tests scripts/tests -q`:
435 passati, 6 saltati; `scripts/tests`: 24 passati nella prova mirata.
`experiments/run_homework3.py` e `pip check` negli ambienti
sviluppo e packaging: PASS. L'EXE finale identificato sopra si è installato
silenziosamente con `exit 0`; sull'installazione risultante i 242 file del
manifest hanno SHA-256 corretti, con 242 attribuzioni, 47 binari Qt e sette
archivi sorgente. L'app installata ha indicizzato il corpus sintetico e la
query `meteorite azzurro` ha restituito `alfa.txt`, `beta.md`, `gamma.pdf`.
Le prove di reinstallazione, upgrade e disinstallazione sopra documentate
sono state eseguite sul candidato immediatamente precedente; l'ultima build
ha corretto soltanto l'attribuzione sorgente di `qwindows.dll` nel manifest.

## Gate

V2-D08: termini italiani approvati nella sostanza dal titolare Luca Foresti;
traduzione inglese informativa, testi distribuiti corrispondenti. V2-D09:
il titolare ha approvato esplicitamente l'8 novembre 2026 l'audit documentato
del payload 0.2.0, dopo la presentazione di inventario e prove. La verifica
documentata non è un parere legale indipendente. V2-07 è chiusa per il
collaudo locale sull'account corrente. Windows pulito,
account standard distinto, revisione pulita e accettazione pubblica restano
V2-08. L'uso attuale di Inno Setup è dichiarato non commerciale dal titolare;
la valutazione va rifatta se cambia il contesto.
