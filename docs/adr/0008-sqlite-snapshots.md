# ADR 0008 — SQLite, memoria e ciclo di vita degli snapshot

- **Status:** Accepted, 2026-11-06; persistenza/recovery/retention M5, lifecycle/rebuild M6 e concorrenza/lock M7 implementati e verificati localmente.
- **Context:** persistenza locale per alcune migliaia di documenti senza inventare un protocollo custom di file atomici.
- **Decision:** snapshot completi in SQLite; indici/draft in RAM, nessun full-text SQL o spill. Una transazione salva/valida candidato e attiva il riferimento; memoria aggiornata dopo commit. Attivo e precedente, letture già iniziate protette, nessuna cache di directory passate. Rebuild per incompatibilità, stato no-change separato. Storage per utente e pulizia esplicita.
- **Alternatives considered:** JSON con pointer swap, segmenti incrementali, streaming e migrazioni di indici.
- **Consequences:** maggiore spazio e picco RAM, ma protocollo semplice; ResourceFailure e crash testati. Riuso logico degli invariati, non condivisione fisica di segmenti.
- **Validation:** M5 transazioni/recovery, M6 lifecycle/rebuild, M7 letture concorrenti e lock, M9 misure.
- **Related:** dettaglio normativo in [Snapshot](../archive/v1/SNAPSHOTS_AND_SYNC.md), [Privacy](../archive/v1/SECURITY_AND_PRIVACY.md).

- **M6 clarification (2026-11-06):** catalogo di controllo SQLite v1 separato per settings, selezione e registro dei database posseduti. Rebuild fisico/logico su database candidato distinto; selezione transazionale dopo validazione/commit. Adozione dello storage M5 senza migrazione; schema incompatibile privo di settings richiede selezione della sorgente. ClearLocalData mantiene solo il contenitore di controllo vuoto riutilizzabile. [Dettagli](../archive/v1/SNAPSHOTS_AND_SYNC.md#8-realizzazione-m6).

- **ID (2026-11-07, approvato):** l'allocatore SQLite separato conserva il progressivo
  oltre snapshot, retention, rebuild, cambio directory e riavvio. Le prenotazioni sono durevoli
  prima della costruzione del candidato e possono lasciare buchi. Storage precedente senza
  allocatore richiede ClearLocalData esplicita; nessuna migrazione automatica.

> Per v2: [ADR 0012](0012-v2-lifecycle-storage.md) conserva gli invarianti, mentre il layout fisico richiede V2-D04.
