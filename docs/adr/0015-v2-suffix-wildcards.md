# ADR 0015 — Ricerca per suffisso e wildcard esplicite

- **Stato:** Accepted, 2026-11-10; milestone V2-09.
- **Contesto:** V2-03 indicizza il vocabolario in ordine lessicografico e usa `bisect` per `termine*`. Serve anche `*termine` nella ricerca e nei suggerimenti dinamici.
- **Decisione:** ogni indice posizionale possiede un secondo vocabolario immutabile, ordinato per termine con caratteri invertiti e derivato dalle stesse chiavi. La ricerca per suffisso inverte il frammento, trova l'intervallo con `bisect` e consulta i posting originali. Nessun nuovo albero, schema SQLite o indice di posting.
- **Sintassi:** `allow_wildcards=True` abilita `termine*` e `*termine` fuori dalle frasi. Wildcard interne, doppie o su entrambi i lati sono invalide. Un token normalizzato per campo, almeno due caratteri e massimo 256 espansioni per clausola/campo; controllo prima dei match. Il default `False` preserva l'analisi storica della punteggiatura.
- **API:** `allow_prefixes` è rinominato `allow_wildcards` senza alias. `SuggestRequest.mode` usa `PREFIX` (default) o `SUFFIX`; il testo parziale non include `*`. I suggerimenti restano alfabetici nell'ordine originale, deduplicati in BOTH e limitati a 50; non applicano il limite delle 256 espansioni della ricerca.
- **Desktop:** digitare `*ing` richiede suggerimenti per suffisso senza cercare; scegliere un termine sostituisce l'intera clausola con il termine esatto e avvia la ricerca.
- **Alternative:** scansione del vocabolario normale troppo costosa per suffissi comuni; albero aggiuntivo non necessario per snapshot immutabili. La tupla rovesciata aumenta memoria e tempo di costruzione/riapertura; misurarli con V2-09.
- **Relazioni:** estende [ADR 0010](0010-v2-retrieval.md); preserva AND/frasi nello stesso campo, snapshot e CLI Homework. Verifica in T22/T23 e regressioni T03–T09, T12/T13 e T18.
