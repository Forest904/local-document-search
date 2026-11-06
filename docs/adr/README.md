# Architecture Decision Records

Un ADR descrive una decisione di progetto e i compromessi che comporta. Qui **Accepted** significa che la direzione è stata concordata nella progettazione, **non** che l'implementazione è pronta.

| ADR | Titolo | Stato |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modular monolith / Ports & Adapters | Accepted |
| [0002](0002-canonical-document.md) | Un file, testo canonico unico, testo persistito | Accepted |
| [0003](0003-positional-index.md) | Due indici invertiti posizionali proprietari | Accepted (dettagli analyzer aperti) |
| [0004](0004-snapshot-sync.md) | Snapshot immutabili e sincronizzazione incrementale | Accepted (storage fisico aperto) |
| [0005](0005-ingestion-policy.md) | Policy TXT/Markdown/PDF, errori e symlink | Accepted |
| [0006](0006-application-interfaces.md) | Contratti inbound/outbound e single JobManager | Accepted (trasporto aperto) |

Per decisioni future usare [TEMPLATE.md](TEMPLATE.md) e aggiornare [OPEN_DECISIONS](../OPEN_DECISIONS.md).
