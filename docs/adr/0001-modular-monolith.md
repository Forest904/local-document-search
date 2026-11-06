# ADR 0001 — Modular monolith con Ports & Adapters

- **Status:** Accepted (design)
- **Context:** il prototipo per l'Homework 3 deve crescere in un backend per app Windows, senza duplicare logica di indexing o search.
- **Decision:** monorepo con backend Python modularizzato in `domain`, `application`, `infrastructure`, `interfaces`; futura UI Windows disaccoppiata. Domain puro e indipendente da I/O; Application definisce le porte; Infrastructure le implementa; frontend usa contratti applicativi.
- **Alternatives considered:** unico script (troppo accoppiato), microservizi e repository separate (complessità ingiustificata).
- **Consequences:** riuso fra CLI/UI, testabilità, un composition root futuro, disciplina sui confini. Nessun server HTTP necessario ora.
- **v1 clarification (2026-11-06):** framework UI, chiamate in-process senza IPC/HTTP e packaging sono definiti in [ADR 0009](0009-desktop-runtime.md). La composizione concreta resta un dettaglio interno da implementare in M1/M3, senza framework di dependency injection obbligatorio.
- **Related:** [Architecture](../ARCHITECTURE.md), [Interface Contracts](../INTERFACE_CONTRACTS.md).
