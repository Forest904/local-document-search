# Homework 3 — Relazione (TEMPLATE NON COMPILATO)

> Sostituire ogni campo `[DA COMPILARE]` con un risultato realmente ottenuto. Questo file resta un template; per i risultati M3 effettivamente misurati vedere [REPORT.md](REPORT.md).

## 1. Informazioni generali

- **Progetto:** Local Document Search
- **Repository GitHub:** `[DA COMPILARE: URL del repository pubblico/privato appropriato]`
- **Ambiente di prova:** `[DA COMPILARE: sistema operativo, versione Python, CPU/RAM se pertinenti]`
- **Data del test:** `[DA COMPILARE]`

## 2. Obiettivo

Realizzazione di un sistema di indicizzazione dei file `.txt` in una directory, con due indici distinti (nome file e contenuto), ricerca da console e supporto alle phrase queries.

## 3. Scelte architetturali e analyzer

### Nome del file

- Regole di tokenizzazione: `[DA COMPILARE CON COMPORTAMENTO IMPLEMENTATO]`
- Regole di normalizzazione: `[DA COMPILARE]`
- Motivazione: `[SPIEGARE LA DIFFERENZA RISPETTO AL CONTENUTO]`

### Contenuto

- Regole di tokenizzazione: `[DA COMPILARE]`
- Regole di normalizzazione: `[DA COMPILARE]`
- Stop words / stemming e loro motivazione: `[DA COMPILARE]`

### Indice e phrase query

Descrivere `term -> docID -> positions` e come vengono verificate le posizioni consecutive. Indicare eventualmente le estensioni Markdown/PDF **se effettivamente implementate**, separandole dai requisiti minimi.

## 4. Corpus e indicizzazione

| Voce | Misura |
|---|---|
| Directory/corpus di test | `[DA COMPILARE]` |
| File `.txt` scoperti | `[DA COMPILARE]` |
| File `.txt` indicizzati | `[DA COMPILARE]` |
| File esclusi / errori | `[DA COMPILARE]` |
| Durata totale indicizzazione | `[DA COMPILARE]` |
| Eventuali tempi separati per nome/contenuto | `[DA COMPILARE, SE MISURATI]` |
| Numero di termini distinti (opzionale) | `[DA COMPILARE]` |

Chiarire se il tempo si riferisce al primo build completo o a un aggiornamento incrementale. Per il confronto didattico, riportare sempre il tempo del build iniziale.

## 5. Query di prova

Consultare [QUERY_TEST_PLAN.md](QUERY_TEST_PLAN.md) e sostituire gli scenari con **query reali**, documenti attesi ed esiti.

| # | Query eseguita | Risultati attesi | Risultati ottenuti | Esito |
|---|---|---|---|---|
| 1 | `[DA COMPILARE]` | | | |
| 2 | `[DA COMPILARE]` | | | |
| 3 | `[DA COMPILARE]` | | | |
| 4 | `[DA COMPILARE]` | | | |
| 5 | `[DA COMPILARE]` | | | |
| 6 | `[DA COMPILARE]` | | | |
| 7 | `[DA COMPILARE]` | | | |
| 8 | `[DA COMPILARE]` | | | |
| 9 | `[DA COMPILARE]` | | | |
| 10 | `[DA COMPILARE]` | | | |

## 6. Osservazioni e limiti

Discutere eventuali errori o limiti di normalizzazione, phrase queries e dataset. Non dichiarare supporto a funzionalità non ancora implementate.

## 7. Conclusioni

Sintetizzare i risultati verificati, il supporto ai requisiti e possibili estensioni dell'applicazione Windows.
