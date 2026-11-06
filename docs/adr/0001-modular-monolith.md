# ADR 0001 — Modular monolith con Ports & Adapters

- **Status:** Accepted (design)
- **Context:** il prototipo per l'Homework 3 deve crescere in un backend per app Windows, senza duplicare logica di indexing o search.
- **Decision:** monorepo con backend Python modularizzato in `domain`, `application`, `infrastructure`, `interfaces`; futura UI Windows disaccoppiata. Domain puro e indipendente da I/O; Application definisce le porte; Infrastructure le implementa; frontend usa contratti applicativi.
- **Alternatives considered:** unico script (troppo accoppiato), microservizi e repository separate (complessità ingiustificata).
- **Consequences:** riuso fra CLI/UI, testabilità, un composition root futuro, disciplina sui confini. Nessun server HTTP necessario ora.
- **Open implementation details:** UI framework, IPC/API locale, packaging, dependency injection concreta.
- **Related:** [Architecture](../ARCHITECTURE.md), [Interface Contracts](../INTERFACE_CONTRACTS.md).
