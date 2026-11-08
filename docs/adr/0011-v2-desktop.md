# ADR 0011 — Desktop v2 Qt Quick

- **Stato:** Accepted (direzione v2), 2026-11-07; implementazione V2-06 e limiti verificati nel [rapporto](../V2_06_DESKTOP.md).
- **Contesto:** il desktop v1 Qt Widgets è funzionale ma la v2 richiede un'esperienza visiva e accessibile da prodotto pubblico.
- **Decisione:** PySide6/Qt Quick con QML, stesso backend Python in-process e contratti applicativi. Sidebar essenziale, ricerca centrale, risultati e anteprima; temi chiaro/scuro e italiano/inglese. Ricerca con Invio, suggerimenti durante digitazione. Ispirazione dall'app desktop ChatGPT limitata al linguaggio visivo, senza chat o AI.
- **Conseguenze:** nuovo frontend e packaging QML, necessità di prova anticipata dell'installer e dei moduli Qt. Worker e gestione delle risposte obsolete proteggono la responsività.
- **Relazione con v1:** sostituisce per v2 la scelta **Qt Widgets** e la sola lingua italiana dell'[ADR 0009](0009-desktop-runtime.md); conserva backend in-process, CLI separata e niente servizio.
- **Verifica:** V2-06/V2-08, T12–T13 nella [strategia](../TEST_STRATEGY.md). [UX](../UX_WINDOWS.md).

## Revisione approvata — Luma, 2026-11-08

La richiesta del titolare sostituisce sidebar e anteprima con ingresso guidato,
home minimale, lista con snippet e apertura diretta dei file. Filtri e gestione
indice sono nella pagina Impostazioni; filtri solo di sessione, reset al cambio
cartella/riavvio e riepilogo visibile. Italiano/inglese e chiaro/scuro persistenti
sono confermati. Luma è il nome del motore; Local Document Search resta il nome
applicazione. Il catalogo v2 esistente permette il recupero automatico agli avvii
successivi; la prima inizializzazione segue l'informativa accettata.

QML suddiviso per pagine e componenti, asset originali SVG/PNG/ICO locali.
Nessun cambiamento a backend dei dettagli, grammatica query o CLI. Le prove
storiche V2-06/V2-07 non si trasferiscono al nuovo frontend: vedere
[UX](../UX_WINDOWS.md) e [verifiche Luma](../LUMA_DESKTOP.md).
