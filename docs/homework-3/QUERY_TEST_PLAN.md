# Piano di validazione — Circa 10 query

**Stato:** matrice eseguita sul corpus sintetico M3: dieci query PASS più due regressioni, con attesi espliciti definiti dai testi. Query e misure nella [relazione](REPORT.md); runner riproducibile in [experiments](../../experiments/run_homework3.py). La matrice resta utilizzabile per altri corpus.

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

## Estensione HW3-02

La matrice storica e le due regressioni restano invariate e indipendenti.
La nuova [valutazione HW3-02](HW3_02_EVALUATION.md) congela 30 query per ciascuno
dei quattro corpus: 10 nome, 15 contenuto, 5 entrambi. I tre sintetici annidati
condividono il testo delle query; gli attesi sono specifici per corpus. Il set
reale è distinto e rimane locale.

Gli attesi lessicali derivano dalla scansione indipendente e da controlli manuali
su esempi, prima della ricerca. Il confronto recupera tutte le pagine e conserva
insiemi, TP/FP/FN, metriche micro/macro, casi N/A e correttezza esatta. Esempi
sintetici: `velnaro tespilo` verifica il vincolo fra campi; `"frandilo spolvero"`
distingue adiacenza, interruzione e ordine invertito; `café` verifica gli accenti.

Dieci ulteriori query tematiche, approvate con i bisogni e poi mantenute fisse,
usano un indice dei soli 60 documenti selezionati. I 600 giudizi sono stati
revisionati e approvati prima di mostrarne i risultati; non derivano dalla
presenza lessicale dei termini. ID anonimi, metriche e limiti sono nel protocollo;
testi delle query reali, motivazioni e documenti dettagliati restano locali.
