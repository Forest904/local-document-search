# V2-07 — Installer offline: evidenze e limiti

Data: 8 novembre 2026. Versione applicativa e installer: 0.2.0.

La build riusa il payload standalone Qt Quick. Inno Setup 6.7.3 è bloccato
tramite SHA-256 di `ISCC.exe` nel codice di build. Il pacchetto EXE installa
per utente sotto `%LOCALAPPDATA%\Programs\LocalDocumentSearchV2`; dati e
preferenze restano in `%LOCALAPPDATA%\LocalDocumentSearchV2`.

L'installer ha wizard italiano/inglese, menu Start e desktop opzionale. La
stessa identità permette upgrade e reinstallazione; il downgrade è rifiutato.
Il programma aperto blocca installazione e disinstallazione. Quest'ultima
conserva i dati salvo scelta esplicita, non attiva in modalità silenziosa.
La pulizia rifiuta reparse point e controlla il lock di sessione. Lo script
di upgrade elimina solo file presenti nel vecchio manifest, assenti nel nuovo
e ancora identici al vecchio hash.

`BUILD-MANIFEST.json` registra revisione, stato dirty, sorgenti, toolchain,
file e gruppi di componenti effettivi. Accanto all'EXE si producono SHA-256
e manifest dell'installer, che lega compilatore, sorgenti e payload.

La bozza `TERMS-DRAFT.txt` non è approvata. V2-D08 richiede identità e
recapito del titolare, testo finale e approvazione. V2-D09 richiede la prova
sul payload finale della sostituibilità delle librerie Qt e dell'insieme degli
avvisi e sorgenti corrispondenti. Il compilatore Inno indica uso non
commerciale; un futuro uso commerciale della toolchain va verificato con la
[politica del produttore](https://jrsoftware.org/isorder.php).

## Prove locali

Revisione di partenza `1cdeaa1fbf65a8e7c90c3a912008022e9e29dc8b`,
working tree modificato; Windows 11 build 26200, Python 3.12.2, Inno Setup
6.7.3, compilatore SHA-256
`0a8757031b33777e4c9cbffee40f11a5062b36d25cbe144c1db73b6102b80ad7`.
`./scripts/package/build.ps1` e la ricompilazione finale dell'installer hanno
prodotto l'EXE da 50.176.343 byte, SHA-256
`80791de040996dc2bcb9cfcb5f479f7f73d12356b4bb7064ce3ecadd56158990`.
L'ultima build ha emesso `Successful compile` e scritto i manifest; il wrapper
PowerShell di `Start-Process -Wait` è rimasto in attesa dopo la conclusione di
Python ed è stato interrotto. Integrità e installazione dell'EXE sono state
verificate separatamente; l'exit code del wrapper non è conteggiato come PASS.
Tutti i 2.792 file del manifest sono stati ricontrollati con SHA-256; l'hash
dell'EXE corrisponde al manifest separato. La build ha escluso addon Qt
WebEngine, Multimedia e PDF non importati dalla UI; restano 221 librerie Qt
nel payload da valutare in V2-D09.

Installazione silenziosa senza elevazione: `exit 0`; avvio dell'EXE installato
con `LOCALAPPDATA` isolato: processo attivo e mutex rilevato. Reinstallazione
e upgrade da installer di prova 0.1.9: `exit 0`. Downgrade 0.2.0 → 0.1.9:
`exit 1`, versione installata 0.2.0 conservata. Con app aperta, installazione
respinta (`exit 1`) e processo lasciato in esecuzione. L'upgrade ha eliminato
un file sintetico obsoleto elencato nel vecchio manifest e ha conservato un
file sintetico estraneo. Disinstallazione silenziosa: `exit 0`, dati sintetici
conservati; pulizia esplicita successiva: `exit 0`. Con lock occupato, pulizia
respinta (`exit 1`) e dati conservati; retry riuscito.
Con l'EXE identificato dall'hash sopra, installazione e disinstallazione
silenziose hanno dato `exit 0`; con l'app aperta, disinstallazione respinta
(`exit 1`) lasciando il processo attivo. I dati sintetici sono stati
conservati e poi cancellati esplicitamente; l'installazione di prova è stata
rimossa dall'account di sviluppo.
Una copia dell'EXE avviata da `%TEMP%/lds v2 prova città/Installazione città.exe`
ha installato e disinstallato correttamente (`exit 0` per entrambe le operazioni).
La DLL `qt6core.dll` installata è stata sostituita da una copia con hash
verificato della medesima build: l'applicazione si è avviata, poi la DLL
originale è stata ripristinata. Questo prova la sostituibilità fisica della
DLL nello staging, non la compatibilità di una build Qt modificata. La
procedura e i sorgenti upstream identificati sono nel payload.

Suite: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`:
384 passed/6 skipped; `-m pytest frontend/tests -q`: 27 passed;
`-m pytest scripts/tests -q`: 19 passed;
`backend/.venv/Scripts/python.exe experiments/run_homework3.py`: PASS;
`backend/.venv/Scripts/python.exe -m pip check`: PASS. L'installer è stato
provato con `Start-Process -Wait` e opzioni Inno `/VERYSILENT
/SUPPRESSMSGBOXES /NORESTART`; log locali in `%TEMP%/lds-v2-07-*.log`.
L'installer è stato provato in modalità
silenziosa sul PC di sviluppo: il wizard interattivo, la scelta di cancellazione
nel disinstallatore, gli avvisi SmartScreen e i flussi completi di ricerca sul
programma installato non sono ancora stati verificati. Nella verifica UI si
sono raggiunte informativa e selezione cartella, ma l'automazione del dialogo
nativo non ha completato la selezione; nessun PASS è attribuito alla ricerca.
Il PC di sviluppo non
vale come Windows pulito né account standard distinto; anche queste prove e
il pacchetto da revisione pulita restano V2-08.
