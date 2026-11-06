# ADR 0002 — Canonical Document Model testuale, un file per documento

- **Status:** Accepted (design)
- **Context:** TXT, Markdown e PDF richiedono reader specifici ma un solo motore IR.
- **Decision:** ogni file fisico diventa un `CanonicalDocument` con descriptor e **un unico `content: str`**, senza pagine/segmenti; un `IndexedDocument` conserva metadati e **testo estratto persistito**. La ricerca restituisce file e non pagine.
- **Alternatives considered:** CDM gerarchico con pagine/sezioni (maggiore complessità), corpus soltanto TXT (scope troppo ridotto per il prodotto).
- **Consequences:** analyzer indipendenti dal formato e snippet futuri; perdita delle pagine, maggior spazio disco, phrase queries che possono attraversare confini originari.
- **Open implementation details:** snippets, token offset, storage del testo, ordine logico del PDF.
- **Related:** [Domain Model](../DOMAIN_MODEL.md), [Privacy](../SECURITY_AND_PRIVACY.md).
