# ADR 0009 — Desktop Python in-process e distribuzione portabile

- **Status:** Accepted (design), 2026-11-06; non implementato.
- **Context:** v1 personale Windows 11 x64 senza vincolo di stack né necessità di servizio separato.
- **Decision:** PySide6 Qt Widgets e backend nello stesso processo, tramite contratti applicativi; un worker sync, query fuori dal thread UI. Una istanza sullo storage, chiusura attende job. ZIP standalone tramite pyside6-deploy, dipendenze incluse, nessun Python preinstallato.
- **Alternatives considered:** WPF/WinUI con backend separato, IPC/HTTP, installer per utente.
- **Consequences:** meno integrazione e un solo stack; nessun isolamento del backend dal processo UI. Domain/application non dipendono da Qt. Versioni e configurazione build fissate durante M9.
- **Pagination clarification (2026-11-06):** ogni ricerca usa lo snapshot attivo. Se una pagina successiva restituisce uno snapshot_id diverso da quello della lista visualizzata, la UI scarta la pagina e ripete la stessa query/campo con offset=0; ignora risposte superate da una nuova query o directory. Nessun parametro snapshot_id in SearchRequest; dettagli nei [Contratti](../INTERFACE_CONTRACTS.md).
- **Validation:** M7 runtime, M8 UX sotto carico, M9 avvio su Windows pulito.
- **Related:** [UX](../UX_WINDOWS.md), [Architettura](../ARCHITECTURE.md), [Roadmap](../ROADMAP.md).

- **M7 implementation clarification (2026-11-06, approvata):** lock OS per tutte le sessioni persistenti prima dell’apertura dei database; la CLI Homework volatile rimane invariata ed esente dal lock. Un worker sync e un worker letture, chiusura con attesa e rifiuto di nuove operazioni. Runtime verificato con thread/processi su Windows; ramo POSIX, UI e packaging restano da verificare nei rispettivi ambienti. [Evidenze M7](../M7_VERIFICATION.md).
