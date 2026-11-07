> Archivio v1 — fotografia documentale del 7 novembre 2026. Stati e risultati sono storici; non descrivono la v2. [Documentazione corrente](../../README.md).

# Security & Privacy v1

**Stato:** policy approvata; M5 verifica storage per utente, confini dei percorsi e pulizia dei dati del repository senza toccare sorgenti ([evidenze](M5_VERIFICATION.md)). M6 implementa ClearLocalData nel backend ([evidenze](M6_VERIFICATION.md)); lock tra processi verificato in M7; informativa prima dello startup, pulizia confermata e attesa della chiusura implementate in M8 ([evidenze](M8_VERIFICATION.md)). Distribuzione da verificare in M9.

## Dati e storage

Elaborazione locale, nessun upload, OCR o accesso web dei reader.
Testo estratto persistito: può restare anche quando il sorgente non è accessibile.
UI e istruzioni devono informare l'utente prima dell'indicizzazione persistente.
Su Windows usare %LOCALAPPDATA%/LocalDocumentSearch, fuori dal repository e dalla directory indicizzata.
Usare protezioni standard dell'account; nessuna cifratura applicativa aggiuntiva nella v1.
Per backend/test su altri sistemi iniettare una directory applicativa/temporanea esplicita,
senza portare dipendenze Windows nel dominio.

## Retention e pulizia

Attivo e precedente della sola directory corrente, con letture già iniziate protette.
Cambio directory elimina vecchia cache quando non in uso; dettagli in [Snapshot](SNAPSHOTS_AND_SYNC.md).
ClearLocalData disponibile a job fermo, con conferma UI dell'eliminazione dei dati applicativi.
Blocca nuove letture, attende quelle in corso e rimuove dati/settings/log/temporanei dell'app.
Non tocca documenti sorgente e non promette cancellazione forense dei blocchi di disco.
Se la pulizia fallisce, riportare errore e consentire ripetizione, senza dichiarare completamento.

## Accesso e diagnostica

Lock OS esclusivo dello storage tra CLI/desktop; nessun server HTTP/IPC o porta di rete.
Non seguire symlink/junction/reparse point durante discovery.
Log senza testo, query personali o percorsi assoluti; diagnostica con categorie e percorsi relativi.
Errori mostrati localmente non devono riversare contenuti sensibili nei log condivisibili.
Mai committare corpus personali, snapshot o testo estratto; fixture sintetiche.
Parser trattano documenti come input non fidati: test per file corrotti e risorse insufficienti.

## Distribuzione

Pacchetto per account standard Windows 11 x64, senza privilegi amministrativi o Python installato.
Includere avvisi/licenze delle dipendenze; nessun cloud, telemetry o updater introdotto implicitamente.
Verifica operativa e pulizia del pacchetto in M9; [Roadmap](ROADMAP.md).

## Stato distribuzione (2026-11-07)

Il pacchetto locale M9 esiste; la prova finale dopo le correzioni è in corso. Per decisione esplicita dell'utente, la prova su Windows pulito e account standard distinto è rinviata alle versioni successive. La CLI Homework resta volatile e non acquisisce il lock delle sessioni persistenti. I report dei job mostrano categorie e percorsi relativi, senza testo, query o percorsi assoluti nei log.
