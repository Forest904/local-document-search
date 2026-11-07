> Archivio v1 — fotografia documentale del 7 novembre 2026. Stati e risultati sono storici; non descrivono la v2. [Documentazione corrente](../../README.md).

# Verifica M2 — Motore di ricerca puro

**Data:** 6 novembre 2026. **Esito:** implementata e verificata localmente; CI remota da verificare.

## Ambiente e comandi

Windows, Python 3.12.2, ambiente virtuale esistente `backend/.venv`, pytest 8.3.5. Nessuna nuova dipendenza. Da `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

- Suite: **145 test superati**, inclusi 72 nuovi casi M2, nessuno saltato.
- `pip check`: `No broken requirements found.`
- Dalla radice, `git diff --check`: nessun errore.
- Il Python globale non aveva il package installato: il primo tentativo di raccolta nella pianificazione ha prodotto quattro errori di import. Le verifiche finali usano l'ambiente virtuale esistente; nessuna nuova installazione pulita dichiarata.

## Comportamenti verificati

- NFC/casefold/NFC, accenti preservati, apostrofi e punteggiatura separatori, segni combinanti associati, numeri Unicode, CamelCase/acronimi e split lettere/cifre nel filename.
- Suffisso finale supportato rimosso solo dal nome sorgente; query analizzate distintamente per campo, testo canonico preservato.
- Parser di termini/frasi AND; input vuoto, clausole senza token e virgolette sbilanciate rifiutati anche su snapshot vuoto.
- Frasi adiacenti e ordinate, termini ripetuti, clausole miste, BOTH senza distribuzione tra campi, deduplicazione e ordine per percorso preservato.
- Draft con add/replace/remove/exclude, ID forniti dal chiamante, pulizia posting, documenti vuoti e basename distinti per percorso.
- Freeze con validazione e copie indipendenti; modifiche successive al draft non alterano risultati e dati dello snapshot precedente.
- Pipeline integrata interamente in memoria e controlli architetturali degli import.

## Interfacce interne e limiti

`FilenameAnalyzer.analyze` e `ContentAnalyzer.analyze` restituiscono tuple di Token. `prepare_filename` si applica soltanto al nome sorgente. `QueryParser.parse(text, field=BOTH)` restituisce SearchQuery con clausole testuali; `QueryEvaluator.evaluate(query, snapshot)` restituisce tuple ordinate di SearchMatch con ID e campi concreti. Le query strutturate sono validate anche dall'evaluator. Virgolette adiacenti delimitano comunque clausole; nessun escape dedicato.

`IndexBuilder(draft)` vive in `domain/snapshots.py` accanto al draft per evitare cicli con i tipi di indice. Add rifiuta ID/percorso duplicati; replace richiede ID esistente e stesso percorso; remove assente è innocuo. Exclude sostituisce eventuali dati indicizzati. Per indicizzare un percorso escluso, rimuoverne prima la entry. `freeze` riceve dal chiamante ID snapshot, radice, data e versioni; non attiva o persiste lo snapshot.

Il dominio solleva ValueError; la traduzione in InvalidInput nel caso d'uso applicativo sarà collegata in M3. Allocazione degli ID, reader, CLI, paginazione, repository, sync e concorrenza non sono implementati. Nessun benchmark, corpus personale, esecuzione Linux o CI remota verificata. Nessun commit o push eseguito.
