# ADR 0004 — Snapshot immutabili e sync incrementale su metadati

- **Status:** Accepted (design); storage consolidato in ADR 0008
- **Context:** l'app deve conservare la ricerca fra sessioni, rispondere in background e mantenere una versione stabile durante gli aggiornamenti.
- **Decision:** active snapshot interrogabile + building snapshot privato. Diff con path relativo, size e `mtime_ns`; nessun hash. Sync su scelta directory, riapertura app, richiesta manuale. Commit/attivazione atomici; se nessun cambiamento non creare una nuova versione; single writer; ricerca consentita sul vecchio snapshot per la stessa directory.
- **Alternatives considered:** aggiornare l'indice in-place, ricostruire a ogni avvio, watcher sempre attivo, hash di tutti i contenuti.
- **Consequences:** crash-safe a livello contrattuale, ricerca consistente e aggiornamenti più rapidi; risultati temporaneamente obsoleti e possibili modifiche non rilevate se size/mtime invariati.
- **v1 clarification (2026-11-06):** SQLite e snapshot completi, attivo/precedente, RAM senza spill, rebuild per incompatibilità. Protocollo in [ADR 0008](0008-sqlite-snapshots.md) e [Snapshot](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/SNAPSHOTS_AND_SYNC.md).
- **Related:** [Snapshots & Sync](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/SNAPSHOTS_AND_SYNC.md), [Open Decisions](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/OPEN_DECISIONS.md).

> Per v2: [ADR 0012](0012-v2-lifecycle-storage.md) aggiunge cancel e controllo dei sorgenti, conservando gli snapshot atomici.
