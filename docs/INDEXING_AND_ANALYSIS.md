# Analisi, indici e ricerca

[Regole v1 complete e fixture](archive/v1/INDEXING_AND_ANALYSIS.md). V2 conserva discovery senza symlink/junction, TXT/MD UTF-8 rigoroso, PDF testuali senza OCR, un testo canonico per file, analyzer distinti e due indici invertiti posizionali proprietari. Il codice usa oggi dizionari Python e `terms.get` per i termini esatti: un albero non offre automaticamente lookup migliore. [Baseline](BASELINE.md).

## Vocabolario ordinato v2

Ogni snapshot comprende una tupla ordinata immutabile delle chiavi di ciascun indice, ricostruita alla riapertura senza cambiare lo schema SQLite. Il dizionario resta per i termini esatti. La scelta V2-D02 confronta albero bilanciato, scansione del dizionario e tupla ordinata su lookup, intervalli, build, RAM e ricostruzione; [misure](V2_03_RETRIEVAL.md). Le posting posizionali restano la fonte dei match.

V2-D03 abilita `termine*` solo con opzione esplicita, fuori dalle frasi. Prefisso iniziale/interno/ripetuto, token multipli nel campo, lunghezza normalizzata inferiore a due o oltre 256 espansioni per campo sono input invalidi. Il limite si verifica anche quando un'altra clausola non trova match. AND e BOTH continuano a essere risolti interamente per campo. La CLI Homework resta invariata. [Decisione](adr/0010-v2-retrieval.md).

Lo snapshot conserva l'ordine per percorso dei documenti. La ricerca applicativa calcola il totale su tutti i match e costruisce i risultati della sola pagina richiesta, evitando di ordinare e materializzare tutti i match nelle query ampie. L'API di dominio che restituisce tutti i match mantiene lo stesso ordinamento.

## Risultati v2

La ricerca determina prima quali documenti corrispondono, valutando ogni campo autonomamente. I filtri formato/cartella riducono i candidati secondo il [contratto](INTERFACE_CONTRACTS.md); rilevanza ordina solo i match rimasti. La formula è [V2-D05](OPEN_DECISIONS.md); ordine deterministico e spareggio stabile sono invarianti già approvati. L'alternativa per percorso preserva l'ordine lessicografico v1 nella UI v2.

Snippet ed evidenziazioni derivano da testo estratto persistito e versione acquisita, non dal file sorgente. Offset e selezione delle finestre devono rispettare Unicode e [V2-D06](OPEN_DECISIONS.md). Non promettere coordinate di pagina o fedeltà al layout PDF.

## Ingestione di sorgenti variabili

V2 controlla metadati prima e dopo la lettura/elaborazione per scoprire modifiche osservabili; se cambiano, il job fallisce con retry esplicito e conserva il vecchio snapshot. Il diff rimane path + size + `mtime_ns`, senza hash dei file. Un cambiamento che preserva size e mtime può sfuggire; nessun controllo del filesystem viene introdotto nelle query. [Lifecycle](SNAPSHOTS_AND_SYNC.md).
