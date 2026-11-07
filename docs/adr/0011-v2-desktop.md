# ADR 0011 — Desktop v2 Qt Quick

- **Stato:** Accepted (direzione v2), 2026-11-07; non implementato.
- **Contesto:** il desktop v1 Qt Widgets è funzionale ma la v2 richiede un'esperienza visiva e accessibile da prodotto pubblico.
- **Decisione:** PySide6/Qt Quick con QML, stesso backend Python in-process e contratti applicativi. Sidebar essenziale, ricerca centrale, risultati e anteprima; temi chiaro/scuro e italiano/inglese. Ricerca con Invio, suggerimenti durante digitazione. Ispirazione dall'app desktop ChatGPT limitata al linguaggio visivo, senza chat o AI.
- **Conseguenze:** nuovo frontend e packaging QML, necessità di prova anticipata dell'installer e dei moduli Qt. Worker e gestione delle risposte obsolete proteggono la responsività.
- **Relazione con v1:** sostituisce per v2 la scelta **Qt Widgets** e la sola lingua italiana dell'[ADR 0009](0009-desktop-runtime.md); conserva backend in-process, CLI separata e niente servizio.
- **Verifica:** V2-06/V2-08, T12–T13 nella [strategia](../TEST_STRATEGY.md). [UX](../UX_WINDOWS.md).
