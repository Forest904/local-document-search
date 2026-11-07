# Analisi, indici e ricerca

[Regole v1 complete e fixture](archive/v1/INDEXING_AND_ANALYSIS.md). V2 conserva discovery senza symlink/junction, TXT/MD UTF-8 rigoroso, PDF testuali senza OCR, un testo canonico per file, analyzer distinti e due indici invertiti posizionali proprietari. Il codice usa oggi dizionari Python e `terms.get` per i termini esatti: un albero non offre automaticamente lookup migliore. [Baseline](BASELINE.md).

## Vocabolario ordinato v2

Ogni snapshot v2 comprende una struttura secondaria ordinata del vocabolario per `filename` e `content`, coerente con il rispettivo indice primario. Serve a prefissi espliciti e suggerimenti. La scelta concreta ([V2-D02](OPEN_DECISIONS.md)) confronta albero bilanciato, array ordinato e altre rappresentazioni appropriate per lookup, intervalli, costo di build, RAM e persistenza. Una struttura sbilanciata non soddisfa il requisito solo perché è un BST. Le posting posizionali restano la fonte dei match.

La sintassi dei prefissi, limiti di espansione e suggerimenti saranno fissati in [V2-D03](OPEN_DECISIONS.md) prima del codice. Non introdurre completamento implicito in una query esatta e non cambiare l'input della CLI Homework. Analyzer di query e indicizzazione restano coerenti; una frase richiede posizioni consecutive in un singolo campo.

## Risultati v2

La ricerca determina prima quali documenti corrispondono, valutando ogni campo autonomamente. I filtri formato/cartella riducono i candidati secondo il [contratto](INTERFACE_CONTRACTS.md); rilevanza ordina solo i match rimasti. La formula è [V2-D05](OPEN_DECISIONS.md); ordine deterministico e spareggio stabile sono invarianti già approvati. L'alternativa per percorso preserva l'ordine lessicografico v1 nella UI v2.

Snippet ed evidenziazioni derivano da testo estratto persistito e versione acquisita, non dal file sorgente. Offset e selezione delle finestre devono rispettare Unicode e [V2-D06](OPEN_DECISIONS.md). Non promettere coordinate di pagina o fedeltà al layout PDF.

## Ingestione di sorgenti variabili

V2 controlla metadati prima e dopo la lettura/elaborazione per scoprire modifiche osservabili; se cambiano, il job fallisce con retry esplicito e conserva il vecchio snapshot. Il diff rimane path + size + `mtime_ns`, senza hash dei file. Un cambiamento che preserva size e mtime può sfuggire; nessun controllo del filesystem viene introdotto nelle query. [Lifecycle](SNAPSHOTS_AND_SYNC.md).
