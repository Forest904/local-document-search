# ADR 0002 — Canonical Document Model testuale, un file per documento

- **Status:** Accepted (design)
- **Context:** TXT, Markdown e PDF richiedono reader specifici ma un solo motore IR.
- **Decision:** ogni file fisico diventa un `CanonicalDocument` con metadati sorgente e **un unico `content: str`**, senza pagine/segmenti; application associa l'ID, non il reader. Un `IndexedDocument` conserva descriptor e **testo estratto persistito**. La ricerca restituisce file e non pagine.
- **Alternatives considered:** CDM gerarchico con pagine/sezioni (maggiore complessità), corpus soltanto TXT (scope troppo ridotto per il prodotto).
- **Consequences:** analyzer indipendenti dal formato e snippet futuri; perdita delle pagine, maggior spazio disco, phrase queries che possono attraversare confini originari.
- **v1 clarification (2026-11-06):** testo in SQLite, PDF concatenato in ordine di pagina; snippet e offset per highlighting fuori v1. Vedi [ADR 0007](0007-analysis-and-readers.md) e [ADR 0008](0008-sqlite-snapshots.md).
- **Related:** [Domain Model](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/DOMAIN_MODEL.md), [Privacy](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/SECURITY_AND_PRIVACY.md).
