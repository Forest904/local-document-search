# ADR 0009 — Desktop Python in-process e distribuzione portabile

- **Status:** Accepted (design), 2026-11-06; non implementato.
- **Context:** v1 personale Windows 11 x64 senza vincolo di stack né necessità di servizio separato.
- **Decision:** PySide6 Qt Widgets e backend nello stesso processo, tramite contratti applicativi; un worker sync, query fuori dal thread UI. Una istanza sullo storage, chiusura attende job. ZIP standalone tramite pyside6-deploy, dipendenze incluse, nessun Python preinstallato.
- **Alternatives considered:** WPF/WinUI con backend separato, IPC/HTTP, installer per utente.
- **Consequences:** meno integrazione e un solo stack; nessun isolamento del backend dal processo UI. Domain/application non dipendono da Qt. Versioni e configurazione build fissate durante M9.
- **Validation:** M7 runtime, M8 UX sotto carico, M9 avvio su Windows pulito.
- **Related:** [UX](../UX_WINDOWS.md), [Architettura](../ARCHITECTURE.md), [Roadmap](../ROADMAP.md).
