# Frontend Windows — pianificato

PySide6 con Qt Widgets, Windows 11 x64; nessuna UI implementata.
Consuma i contratti applicativi del backend Python nello stesso processo; non accede direttamente agli indici o allo storage.
Sync e ricerche fuori dal thread UI; un'istanza sullo storage; chiusura attende il job.
Lista ordinata, testo completo, apertura file, Sync e pulizia dati secondo [UX](../docs/UX_WINDOWS.md).
Distribuzione ZIP standalone tramite pyside6-deploy, senza Python preinstallato.
Implementazione M8 e distribuzione M9: [Roadmap](../docs/ROADMAP.md), [ADR 0009](../docs/adr/0009-desktop-runtime.md).
