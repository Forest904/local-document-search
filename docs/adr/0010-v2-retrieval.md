# ADR 0010 — Ricerca v2 e vocabolario ordinato

- **Stato:** Accepted, 2026-11-07; retrieval V2-03 implementato nel backend.
- **Contesto:** v1 usa due dizionari di posting posizionali e lookup esatto. V2 richiede prefissi/suggerimenti e un target di 10.000 file/300 MB.
- **Decisione:** mantenere due indici invertiti posizionali proprietari, AND/frasi nello stesso campo, e aggiungere un indice secondario ordinato del vocabolario per campo e per snapshot. Query esatta non viene espansa implicitamente. Filtri e ranking agiscono sui match; rilevanza predefinita desktop, percorso alternativo; CLI invariata.
- **V2-D02:** tupla ordinata immutabile per campo, costruita dalle chiavi del dizionario al freeze e alla riapertura. Lookup esatto resta sul dizionario; prefissi via `bisect`. Nessuna nuova tabella o versione SQLite in V2-03. Il confronto riproducibile con scansione del dizionario e albero bilanciato è nella [relazione V2-03](../V2_03_RETRIEVAL.md).
- **V2-D03:** prefissi abilitati solo da `allow_prefixes=True`, con `termine*` fuori dalle frasi. Un solo token analyzer per campo, almeno due caratteri normalizzati; massimo 256 espansioni per prefisso/campo, oltre il limite `InvalidInput`. Suggerimenti separati: un token parziale, meno di due caratteri → vuoto, default 10/massimo 50, ordinamento lessicografico e deduplicazione in BOTH. Nessuna paginazione dei suggerimenti. CLI Homework invariata.
- **Scelte rinviate:** ranking [V2-D05](../OPEN_DECISIONS.md), snippet [V2-D06](../OPEN_DECISIONS.md).
- **Conseguenze:** più memoria/persistenza potenziale; ordine, vocabolario e posting devono restare coerenti. Un BST non è assunto più veloce di un dizionario per lookup esatto.
- **Relazione con v1:** estende [ADR 0003](0003-positional-index.md) e [0007](0007-analysis-and-readers.md), senza sostituire la semantica v1 delle query esatte o della CLI.
- **Verifica:** V2-03/V2-05, scenari T03–T08 e T18 nella [strategia](../TEST_STRATEGY.md).
