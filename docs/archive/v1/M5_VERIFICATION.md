> Archivio v1 — fotografia documentale del 7 novembre 2026. Stati e risultati sono storici; non descrivono la v2. [Documentazione corrente](../../README.md).

# Verifica M5 — Snapshot persistenti

Data: 6 novembre 2026. Verifica locale, nessuna esecuzione CI remota verificata.

## Ambiente e comandi

Windows 11 x64 (`10.0.26200`), Python 3.12.2, SQLite 3.43.1. Verifica finale con l’interprete della virtualenv `backend/.venv`; nessuna nuova dipendenza runtime.

Da `backend/`:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q -rs
.\.venv\Scripts\python -m pip check
```

Installazione riuscita; **268 test superati, 5 saltati**; `pip check`: nessun requisito incompatibile. I 5 skip preesistenti riguardano 4 creazioni di symlink senza privilegio Windows e nomi distinti soltanto per maiuscole/minuscole. I 34 casi M5 sono stati eseguiti, senza skip. Eseguiti anche test mirati durante lo sviluppo, controllo `git diff --check` e verifica dei link locali nei documenti modificati (nessun collegamento mancante).

## Evidenze

- **OD-01/02:** adapter SQLite con schema relazionale v1, foreign keys abilitate, journal DELETE e synchronous FULL. Una transazione salva, rilegge/valida il candidato e aggiorna il riferimento attivo. Un osservatore SQLite vede soltanto il vecchio snapshot fino al commit; RAM pubblicata dopo commit.
- **Round-trip / OD-11:** manifest INDEXED/EXCLUDED, identità, timestamp/versioni, catalogo e testo, conteggi e posting esatti. Fixture canoniche sintetiche TXT/MD/PDF, Unicode, testo vuoto e termini ripetuti; stesso esito delle query nei tre campi dopo riapertura. Caricamento con analyzer disabilitati e sorgenti assenti; nessuna rilettura o ricostruzione.
- **OD-03:** contratti comuni a repository volatile e SQLite; staging invisibile, attivazione validata, scarto ripetibile, ID conservati non sovrascrivibili. Tre versioni con N protetta fino al rilascio, anche dopo eccezione; poi `SnapshotUnavailable`. Cambio directory al livello repository invalida nuove acquisizioni vecchie, preservando quelle già iniziate. Non costituisce implementazione del lifecycle M6.
- **OD-04:** fault injection su scrittura, validazione, commit e memoria; `SQLITE_FULL` sia simulato sia realmente prodotto tramite `PRAGMA max_page_count`. `BuildIndex` conserva `ResourceFailure`, l’attivo resta valido e il tentativo successivo riesce.
- **Recovery:** sottoprocessi terminati prima del commit, all’ingresso dell’istruzione COMMIT e dopo commit prima della pubblicazione RAM. Ulteriori terminazioni esterne in competizione con il commit accettano vecchio o nuovo snapshot completo; controlli di integrità e ricerca al riavvio. Dopo commit persistito si ricarica il nuovo attivo.
- **Retention:** errore di pulizia diagnosticato senza annullare il successo; riapertura riprova ed elimina le versioni superflue. Versioni/schema incompatibili e dati corrotti, incluso il riferimento attivo mancante, rifiutati senza riscrivere il database. Un ID versione vuoto non ripiega sull’attivo.
- **Storage/privacy:** percorso per utente, directory esplicita per test, rifiuto storage sotto repository o sorgente. `clear()` rifiuta candidato/letture attive, elimina le righe applicative e preserva sorgenti/file estranei. Tutti i database di test sono temporanei fuori dal repository.

## Confini e limiti

CLI Homework e composition root restano in memoria. SQLite è utilizzabile esplicitamente dal backend; `GetDocument` usa il DTO già esistente e la versione esatta, senza fallback.

Le acquisizioni sono verificate nella stessa sessione mediante contesti sovrapposti; M5 non dichiara sicurezza multithread/multiprocesso. Il test con osservatore SQLite verifica soltanto la visibilità transazionale, non abilita una seconda istanza applicativa. Single-writer operativo, lock OS e worker restano M7.

Il trace callback interrompe l’ingresso nel COMMIT; la terminazione esterna può arrivare prima o dopo la sua conclusione. Questi test non determinano l’istante fisico di flush e non simulano guasti hardware o perdita di alimentazione. Le garanzie di durabilità dipendono anche da SQLite, filesystem e dispositivo. Disco pieno testato con limite SQLite, senza esaurire il disco dell’utente.

`clear()` conserva il file/schema SQLite e non promette cancellazione forense: la cancellazione completa di settings/log/temporanei e database appartiene a ClearLocalData M6. Rebuild per schema incompatibile con catalogo di controllo, sync incrementale, startup e settings restano M6; verifiche sul pacchetto e misure di scala restano M9. Nessun benchmark di prodotto inventato, nessun commit o push eseguito.
