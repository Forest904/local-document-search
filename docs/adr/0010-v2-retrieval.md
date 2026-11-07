# ADR 0010 — Ricerca v2 e vocabolario ordinato

- **Stato:** Accepted (direzione v2), 2026-11-07; non implementato.
- **Contesto:** v1 usa due dizionari di posting posizionali e lookup esatto. V2 richiede prefissi/suggerimenti e un target di 10.000 file/300 MB.
- **Decisione:** mantenere due indici invertiti posizionali proprietari, AND/frasi nello stesso campo, e aggiungere un indice secondario ordinato del vocabolario per campo e per snapshot. Query esatta non viene espansa implicitamente. Filtri e ranking agiscono sui match; rilevanza predefinita desktop, percorso alternativo; CLI invariata.
- **Scelte rinviate:** rappresentazione e serializzazione [V2-D02](../OPEN_DECISIONS.md), prefissi [V2-D03](../OPEN_DECISIONS.md), ranking [V2-D05](../OPEN_DECISIONS.md), snippet [V2-D06](../OPEN_DECISIONS.md). Confronto misurato obbligatorio prima del codice pertinente.
- **Conseguenze:** più memoria/persistenza potenziale; ordine, vocabolario e posting devono restare coerenti. Un BST non è assunto più veloce di un dizionario per lookup esatto.
- **Relazione con v1:** estende [ADR 0003](0003-positional-index.md) e [0007](0007-analysis-and-readers.md), senza sostituire la semantica v1 delle query esatte o della CLI.
- **Verifica:** V2-03/V2-05, scenari T03–T08 e T18 nella [strategia](../TEST_STRATEGY.md).
