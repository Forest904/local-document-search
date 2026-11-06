# ADR 0003 — Due indici invertiti posizionali implementati internamente

- **Status:** Accepted (design); regole analyzer di dettaglio in proposta
- **Context:** l'Homework 3 richiede ricerca per nome e contenuto e phrase queries; un inverted index con soli docID non conserva l'adiacenza dei termini.
- **Decision:** `FilenameIndex` e `ContentIndex` separati; posting `term -> docID -> sorted positions`. Query non quotate con AND; frasi con sequenza posizionale; BOTH unisce risultati completi di ciascun campo.
- **Alternatives considered:** scansione completa dei file a ogni query, indici classici senza posizioni, biword index e motori IR preesistenti.
- **Consequences:** controllo algoritmico ed esplicitazione dei concetti del corso; più spazio e codice rispetto all'uso di libreria; attenzione a termini ripetuti e coerenza degli analyzer.
- **Open implementation details:** Unicode/case folding, CamelCase, suffix filename, stopword/stemming, grammatica esatta, ranking e layout fisico.
- **Related:** [Indexing & Analysis](../INDEXING_AND_ANALYSIS.md), [Homework alignment](../homework-3/ASSIGNMENT_ALIGNMENT.md).
