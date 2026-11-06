# Architecture Decision Records

Un ADR descrive una decisione di progetto e i compromessi che comporta. Qui **Accepted** significa che la direzione è stata concordata nella progettazione, **non** che l'implementazione è pronta.

| ADR | Titolo | Stato |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modular monolith / Ports & Adapters | Accepted |
| [0002](0002-canonical-document.md) | Un file, testo canonico unico, testo persistito | Accepted |
| [0003](0003-positional-index.md) | Due indici invertiti posizionali proprietari | Accepted; dettagli in 0007 |
| [0004](0004-snapshot-sync.md) | Snapshot immutabili e sincronizzazione incrementale | Accepted; dettagli in 0008 |
| [0005](0005-ingestion-policy.md) | Policy TXT/Markdown/PDF, errori e symlink | Accepted |
| [0006](0006-application-interfaces.md) | Contratti inbound/outbound e single JobManager | Accepted; dettagli in 0009 |
| [0007](0007-analysis-and-readers.md) | Analyzer, clausole miste e reader v1 | Accepted (design) |
| [0008](0008-sqlite-snapshots.md) | SQLite, RAM e ciclo di vita snapshot | Accepted (design) |
| [0009](0009-desktop-runtime.md) | PySide6 in-process e ZIP portabile | Accepted (design) |

Gli ADR 0007–0009 completano i dettagli dei precedenti. M1–M8 sono implementate e verificate localmente; packaging e misure M9 sono documentati nella [verifica M9](../M9_VERIFICATION.md). Le correzioni e il collaudo finale sono in corso.

Per decisioni future usare [TEMPLATE.md](TEMPLATE.md) e aggiornare [OPEN_DECISIONS](../OPEN_DECISIONS.md).
