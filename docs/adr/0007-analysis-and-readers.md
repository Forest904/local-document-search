# ADR 0007 — Analyzer, clausole miste e reader v1

- **Status:** Accepted (design), 2026-11-06; analyzer e query verificati localmente in [M2](../M2_VERIFICATION.md); reader TXT verificato localmente in [M3](../M3_VERIFICATION.md); Markdown/PDF restano M4.
- **Context:** chiudere i dettagli degli ADR 0003/0005 per una CLI consegnabile e un corpus personale multiformato.
- **Decision:** indici in RAM; NFC+casefold, accenti, niente stemming/stop word; filename senza estensione con split CamelCase/cifre. Query di clausole termini/frasi AND soddisfatte in un singolo campo. UTF-8 strict con BOM; markdown-it-py e pypdf con policy in [Analisi](../INDEXING_AND_ANALYSIS.md).
- **Alternatives considered:** stemming per lingua, fallback charset, query solo interamente quotate, OCR e motori IR esterni.
- **Consequences:** determinismo e semplicità; nessuna segmentazione CJK, perdita di layout PDF e struttura Markdown. Estensione del modello da MatchMode unico a lista di clausole.
- **Validation:** M2 analyzer/query, M3 TXT, M4 reader; esempi in [Test](../TEST_STRATEGY.md).
- **Related:** [Contratti](../INTERFACE_CONTRACTS.md), [Decisioni](../OPEN_DECISIONS.md).
