# ADR 0004 — Snapshot immutabili e sync incrementale su metadati

- **Status:** Accepted (design); storage concreto ancora aperto
- **Context:** l'app deve conservare la ricerca fra sessioni, rispondere in background e mantenere una versione stabile durante gli aggiornamenti.
- **Decision:** active snapshot interrogabile + building snapshot privato. Diff con path relativo, size e `mtime_ns`; nessun hash. Sync su scelta directory, riapertura app, richiesta manuale. Commit/attivazione atomici; se nessun cambiamento non creare una nuova versione; single writer; ricerca consentita sul vecchio snapshot per la stessa directory.
- **Alternatives considered:** aggiornare l'indice in-place, ricostruire a ogni avvio, watcher sempre attivo, hash di tutti i contenuti.
- **Consequences:** crash-safe a livello contrattuale, ricerca consistente e aggiornamenti più rapidi; risultati temporaneamente obsoleti e possibili modifiche non rilevate se size/mtime invariati.
- **Open implementation details:** formato e struttura degli snapshot, recovery, retention, atomic rename/fsync, streaming e gestione memoria.
- **Related:** [Snapshots & Sync](../SNAPSHOTS_AND_SYNC.md), [Open Decisions](../OPEN_DECISIONS.md).
