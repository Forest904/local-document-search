# ADR 0007 — Analyzer, clausole miste e reader v1

- **Status:** Accepted (design), 2026-11-06; analyzer e query verificati localmente in [M2](../archive/v1/M2_VERIFICATION.md); reader TXT verificato localmente in [M3](../archive/v1/M3_VERIFICATION.md); Markdown/PDF verificati localmente in [M4](../archive/v1/M4_VERIFICATION.md).
- **Context:** chiudere i dettagli degli ADR 0003/0005 per una CLI consegnabile e un corpus personale multiformato.
- **Decision:** indici in RAM; NFC+casefold, accenti, niente stemming/stop word; filename senza estensione con split CamelCase/cifre. Query di clausole termini/frasi AND soddisfatte in un singolo campo. UTF-8 strict con BOM; markdown-it-py e pypdf con policy in [Analisi](../archive/v1/INDEXING_AND_ANALYSIS.md).
- **Alternatives considered:** stemming per lingua, fallback charset, query solo interamente quotate, OCR e motori IR esterni.
- **Consequences:** determinismo e semplicità; nessuna segmentazione CJK, perdita di layout PDF e struttura Markdown. Estensione del modello da MatchMode unico a lista di clausole.
- **Validation:** M2 analyzer/query, M3 TXT, M4 reader; esempi in [Test](../archive/v1/TEST_STRATEGY.md).
- **Related:** [Contratti](../archive/v1/INTERFACE_CONTRACTS.md), [Decisioni](../archive/v1/OPEN_DECISIONS.md).

> Per v2: [ADR 0010](0010-v2-retrieval.md) estende query e vocabolario; le query esatte v1 restano baseline.
