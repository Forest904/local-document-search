# ADR 0008 — SQLite, memoria e ciclo di vita degli snapshot

- **Status:** Accepted, 2026-11-06; persistenza/recovery/retention M5 implementate e verificate localmente ([evidenze](../M5_VERIFICATION.md)). Lifecycle/rebuild M6 implementati e verificati localmente ([evidenze](../M6_VERIFICATION.md)); concorrenza/lock M7 restano da implementare.
- **Context:** persistenza locale per alcune migliaia di documenti senza inventare un protocollo custom di file atomici.
- **Decision:** snapshot completi in SQLite; indici/draft in RAM, nessun full-text SQL o spill. Una transazione salva/valida candidato e attiva il riferimento; memoria aggiornata dopo commit. Attivo e precedente, letture già iniziate protette, nessuna cache di directory passate. Rebuild per incompatibilità, stato no-change separato. Storage per utente e pulizia esplicita.
- **Alternatives considered:** JSON con pointer swap, segmenti incrementali, streaming e migrazioni di indici.
- **Consequences:** maggiore spazio e picco RAM, ma protocollo semplice; ResourceFailure e crash testati. Riuso logico degli invariati, non condivisione fisica di segmenti.
- **Validation:** M5 transazioni/recovery, M6 lifecycle/rebuild, M7 letture concorrenti e lock, M9 misure.
- **Related:** dettaglio normativo in [Snapshot](../SNAPSHOTS_AND_SYNC.md), [Privacy](../SECURITY_AND_PRIVACY.md).

- **M6 clarification (2026-11-06):** catalogo di controllo SQLite v1 separato per settings, selezione e registro dei database posseduti. Rebuild fisico/logico su database candidato distinto; selezione transazionale dopo validazione/commit. Adozione dello storage M5 senza migrazione; schema incompatibile privo di settings richiede selezione della sorgente. ClearLocalData mantiene solo il contenitore di controllo vuoto riutilizzabile. [Dettagli](../SNAPSHOTS_AND_SYNC.md#8-realizzazione-m6).
