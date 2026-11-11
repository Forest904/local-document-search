# ADR 0021 — Layout adattivi e guida desktop

- **Stato:** Accepted, 2026-11-11.
- **Contesto:** le nuove superfici reader/editor e i controlli a icona devono essere utilizzabili anche con finestre compatte e DPI elevato; alcune funzioni non ovvie richiedono una guida locale.
- **Decisione:** il desktop supporta da 480×360 pixel logici, riordina controlli e usa scorrimento senza ridurre testi o aree interattive. F1 e Aiuto aprono una guida IT/EN offline e modale da ogni schermata. F5 resta sincronizzazione. La guida non inizializza il backend, non modifica stato di ricerca o bozza e al termine ripristina il focus.
- **Alternative:** mantenere 900×640 e limitarsi a una guida esterna avrebbe lasciato difficoltà su display compatti e nella scoperta delle funzioni. Riassegnare F5 alla guida avrebbe rotto una scorciatoia documentata.
- **Conseguenze:** più stati di layout da verificare in QML, audit nativo DPI/Narrator e collaudo del nuovo installer separati da quelli della 0.2.1. Nessun cambiamento a backend, schema SQLite o CLI.
- **Riferimenti:** [PRD V2-R29/R30](../PRD.md), [UX](../UX_WINDOWS.md), [T33/T34](../TEST_STRATEGY.md).
