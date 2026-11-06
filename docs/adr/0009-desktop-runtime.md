# ADR 0009 — Desktop Python in-process e distribuzione portabile

- **Status:** Accepted, 2026-11-06; runtime M7 e desktop M8 implementati e verificati localmente; distribuzione M9 aperta.
- **Context:** v1 personale Windows 11 x64 senza vincolo di stack né necessità di servizio separato.
- **Decision:** PySide6 Qt Widgets e backend nello stesso processo, tramite contratti applicativi; un worker sync, query fuori dal thread UI. Una istanza sullo storage, chiusura attende job. ZIP standalone tramite pyside6-deploy, dipendenze incluse, nessun Python preinstallato.
- **Alternatives considered:** WPF/WinUI con backend separato, IPC/HTTP, installer per utente.
- **Consequences:** meno integrazione e un solo stack; nessun isolamento del backend dal processo UI. Domain/application non dipendono da Qt. Versioni e configurazione build fissate durante M9.
- **Pagination clarification (2026-11-06):** ogni ricerca usa lo snapshot attivo. Se una pagina successiva restituisce uno snapshot_id diverso da quello della lista visualizzata, la UI scarta la pagina e ripete la stessa query/campo con offset=0; ignora risposte superate da una nuova query o directory. Nessun parametro snapshot_id in SearchRequest; dettagli nei [Contratti](../INTERFACE_CONTRACTS.md).
- **Validation:** M7 runtime, M8 UX sotto carico, M9 avvio su Windows pulito.
- **Related:** [UX](../UX_WINDOWS.md), [Architettura](../ARCHITECTURE.md), [Roadmap](../ROADMAP.md).

- **M8 implementation clarification (2026-11-06, approvata):** pacchetto Python separato in `frontend/`,
  dipendente dal backend e da PySide6, launcher `local-document-search-desktop`. Qt resta escluso
  dall'installazione CLI. Un worker di coordinamento desktop esegue composizione e lifecycle;
  ricerca/dettagli usano le Future M7. Polling senza accumulo e aggiornamenti widget solo nel thread Qt.
  Informativa a ogni avvio prima di Continua, senza nuova preferenza persistente. Vincolo PySide6
  `>=6.8,<7`; versione verificata 6.12.0. Lock completo delle versioni per distribuzione in M9.
  [Evidenze M8](../M8_VERIFICATION.md).

- **M7 implementation clarification (2026-11-06, approvata):** lock OS per tutte le sessioni persistenti prima dell’apertura dei database; la CLI Homework volatile rimane invariata ed esente dal lock. Un worker sync e un worker letture, chiusura con attesa e rifiuto di nuove operazioni. Runtime verificato con thread/processi su Windows; ramo POSIX, UI e packaging restano da verificare nei rispettivi ambienti. [Evidenze M7](../M7_VERIFICATION.md).
