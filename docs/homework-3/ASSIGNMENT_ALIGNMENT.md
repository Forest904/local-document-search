# Homework 3 — Allineamento ai requisiti del corso

**Fonte:** presentazione allegata `id-homework-3.pptx`, slide 2 e 3 (corso Ingegneria dei Dati). È una sintesi dei requisiti, non una sostituzione del documento originale.

## Requisiti espliciti

1. Programma che indicizza i file `.txt` presenti in una directory del laptop.
2. Due campi, e quindi **due indici**: **nome** del file e **contenuto** del file; analyzer appropriato e motivato per ciascun campo.
3. Programma che legge query dalla console, interroga l'indice e stampa risultati. Sintassi semplice, ad esempio keyword `nome` o `contenuto`, seguita da termini; virgolette per phrase query.
4. Test del sistema con **circa dieci query differenti**.
5. Relazione con **URL del repository GitHub o analogo**, scelte degli analyzer e motivazioni, **numero di file indicizzati**, **tempi di indicizzazione**, query utilizzate.
6. Consegna della relazione indicata nelle slide: **13 novembre 2026 ore 18:00**, mediante modulo `https://forms.office.com/e/EbqbR7dvK4`.

## Cosa NON è richiesto, ma il prodotto aggiunge

- PDF digitali e Markdown.
- Snapshot persistenti, aggiornamenti incrementali, manifest, ricerca durante sync.
- UI Windows, background job e barra di progresso.
- Persistenza del testo estratto e futura generazione di snippet.

La CLI con TXT deve essere realizzabile e verificabile **indipendentemente** dalle estensioni.

## Collegamento al materiale didattico

Le slide `id-02-source-discovery-basics.pptx` presentano inverted index con dictionary + posting list (pagine 17–19), tokenization / normalization / stemming / stop words (pagina 20), phrase queries e positional indexes (pagine 64–70). La nostra scelta di mantenere le posizioni serve precisamente a eseguire le phrase queries senza affidarsi alla sola presenza dei termini.

## Stato della consegna

- Design documentato: sì.
- Codice di indexing/ricerca e CLI TXT: **implementati e verificati localmente in M3**.
- Misura del build iniziale su corpus sintetico: **8 file, 192 byte, 0,016752 s**; non è un benchmark di scala.
- Dieci query eseguite: **PASS**, oltre a due regressioni BOTH/clausole miste.
- Repository pubblico fornito dall'utente: https://github.com/Forest904/local-document-search. Nessun push o invio al docente eseguito.

Vedere [ROADMAP](../archive/v1/ROADMAP.md), [relazione compilata](REPORT.md) e [evidenze M3](../archive/v1/M3_VERIFICATION.md). Il [template](REPORT_TEMPLATE.md) resta riutilizzabile.
