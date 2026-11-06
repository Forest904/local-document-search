# Piano di validazione — Circa 10 query

**Stato:** matrice di test proposta. Le query concrete devono essere selezionate in base al corpus `.txt` effettivamente usato; non inventare corrispondenze attese.

| # | Scenario | Campo/modalità | Aspettativa da verificare |
|---|---|---|---|
| 1 | Un solo termine comune | nome | Documento col termine nel nome |
| 2 | Un termine assente | contenuto | Nessun risultato |
| 3 | Due termini in ordine normale | contenuto, AND | Entrambi presenti nello stesso documento |
| 4 | Due termini in ordine inverso | contenuto, AND | Stessi risultati della query #3 se stessi termini |
| 5 | Frase esatta di due termini | contenuto, phrase | Presenza consecutiva |
| 6 | Termini presenti ma non adiacenti | contenuto, phrase | Nessun falso positivo |
| 7 | Frase nel nome | nome, phrase | Nome con termini adiacenti |
| 8 | Maiuscole/minuscole | nome o contenuto | Coerenza con analyzer scelto |
| 9 | Termine ripetuto in frase | contenuto, phrase | Richiede due occorrenze consecutive |
| 10 | Test con più documenti possibili | contenuto, AND/phrase | Verificare insieme risultati corretti |

Per ogni query registrare:

- Testo preciso inserito in console.
- File attesi (ground truth verificata manualmente).
- File restituiti e numero di match.
- Esito PASS/FAIL, osservazioni sull'analyzer e sulle posizioni.

Estensioni facoltative: query multilingue, filename vs content, Markdown senza codice, PDF digitale. Le prove dell'homework devono comunque includere un corpus TXT verificato.
