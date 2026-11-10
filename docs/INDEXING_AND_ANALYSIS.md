# Reader, analyzer e ricerca

Discovery → reader → testo canonico → analyzer per campo → posting nel draft. I reader non assegnano ID né costruiscono indici: l’application associa il testo al documento. Nome e contenuto hanno analyzer distinti e indipendenti dal formato.

## Discovery e reader

Scansione ricorsiva ordinata per percorso relativo, suffissi `.txt`, `.md`, `.pdf` case-insensitive. Symlink, junction e altri reparse point non vengono attraversati/indicizzati; radice link o con componenti link rifiutata. Errori di scansione/lettura fanno fallire il job. Nessun OCR, rendering HTML o accesso agli URL dei documenti.

| Formato | Estrazione e casi limite |
|---|---|
| TXT | UTF-8 strict, BOM iniziale ammesso/rimosso; nessun fallback o sostituzione dei caratteri. Vuoto valido, ricercabile per nome. |
| Markdown | Stessa decodifica; token CommonMark con tabelle (`markdown-it-py`). Include titoli, paragrafi, liste, celle, etichette link, alt immagini e codice inline; esclude blocchi fenced/indentati, token HTML raw e front matter iniziale tra righe `---` solo se chiuso. Senza chiusura tratta il testo come Markdown. Non include destinazioni URL. Separa blocchi/celle/esclusioni con whitespace; vuoto valido. |
| PDF | `pypdf.extract_text()` per pagina, nell’ordine del documento, unite da newline. Pagine immagine non contribuiscono; testo complessivo vuoto/whitespace → Excluded. Corrotto/illeggibile o password necessaria → ExtractionFailed, senza prompt; prova la password vuota se cifrato. Testo non-whitespace senza token resta indicizzato per nome. |

Encoding invalido o errore reader fallisce il candidato, mai commit parziale. Il testo viene conservato prima della normalizzazione; frasi possono attraversare pagine/paragrafi. PDF multicolonna/tabelle possono estrarre un ordine diverso da quello visivo: nessuna provenienza strutturale o garanzia di layout.

## Analyzer e query esatte

1. Dal solo nome sorgente rimuovere il suffisso finale supportato, mai dalla query o dalle directory del percorso.
2. Per filename applicare NFC e dividere minuscola→maiuscola, acronimo→parola e lettera↔cifra prima del casefold. Il contenuto non usa questi split.
3. Normalizzare NFC → casefold → NFC, conservando gli accenti. Token: sequenze Unicode di lettere/numeri e segni combinanti associati; segni isolati non sono token.
4. Punteggiatura, apostrofi, underscore, trattini, punti ed emoji separano. Posizioni consecutive da zero per campo; niente stemming o stop word, né segmentazione dedicata a lingue senza separatori.

Esempi: `l’acqua` → `l`, `acqua`; `Report2026Finale.txt` → `report`, `2026`, `finale`; `HTTPServer.md` → `http`, `server`; `caffè` e `caffe` restano distinti. La query filename `Report2026Finale` usa lo stesso split; `txt` non trova automaticamente tutti i TXT.

Il parser conserva il testo delle clausole, poi ogni campo applica il proprio analyzer. Termini non quotati in AND; virgolette doppie delimitano frasi con ordine/adiacenza. Una frase `t0…tk` richiede posizioni `p…p+k`, anche per termini ripetuti. L’intera query deve corrispondere nel nome oppure interamente nel contenuto; BOTH unisce senza duplicati, mai combinando clausole tra campi. `machine "deep learning"` richiede termine e frase nello stesso campo.

Query vuote, virgolette sbilanciate e clausole senza token (anche frasi vuote) danno `InvalidInput`, non sono ignorate. Nessun escape dedicato, OR/NOT o fuzzy; OR/NOT scritti dall’utente sono termini normali. La CLI rimuove l’eventuale selettore iniziale `nome`/`contenuto`/`entrambi`; l’API riceve il campo separatamente. [Uso CLI](../backend/README.md#sessione-console).

## Vocabolario ordinato v2

Ogni snapshot comprende una tupla ordinata immutabile delle chiavi di ciascun indice, ricostruita alla riapertura dalle chiavi dell’indice. Il dizionario resta per i termini esatti. La scelta V2-D02 confronta albero bilanciato, scansione del dizionario e tupla ordinata su lookup, intervalli, build, RAM e ricostruzione; [misure](PERFORMANCE.md#v2-03). Le posting posizionali restano la fonte dei match.

V2-D03 abilita `termine*` solo con opzione esplicita, fuori dalle frasi. Prefisso iniziale/interno/ripetuto, token multipli nel campo, lunghezza normalizzata inferiore a due o oltre 256 espansioni per campo sono input invalidi. Il limite si verifica anche quando un'altra clausola non trova match. AND e BOTH continuano a essere risolti interamente per campo. La CLI Homework resta invariata. [Decisione](adr/0010-v2-retrieval.md).

Lo snapshot conserva l'ordine per percorso dei documenti. La ricerca applicativa calcola il totale su tutti i match e costruisce i risultati della sola pagina richiesta, evitando di ordinare e materializzare tutti i match nelle query ampie. L'API di dominio che restituisce tutti i match mantiene lo stesso ordinamento.

## Risultati v2

La ricerca determina prima quali documenti corrispondono, valutando ogni campo autonomamente. I filtri formato/cartella riducono i candidati secondo il [contratto](INTERFACE_CONTRACTS.md); rilevanza ordina solo i match rimasti. La formula [V2-D05](adr/0010-v2-retrieval.md) dà priorità al nome, poi alla frequenza di posizioni distinte nei soli campi che soddisfano tutta la query, quindi al percorso. L'alternativa per percorso preserva l'ordine lessicografico v1 nella UI v2.

Snippet ed evidenziazioni derivano da testo estratto persistito e versione acquisita, non dal file sorgente. La mappatura dei token restituisce intervalli Unicode `[start, end)` sul testo originale; i prefissi evidenziano il token completo e le frasi l'intervallo dei token consecutivi. [V2-D06](adr/0010-v2-retrieval.md) fissa una finestra massima di 240 caratteri. Non promettere coordinate di pagina o fedeltà al layout PDF.

Diff, metadati in ingestione e pubblicazione sono definiti in [architettura](ARCHITECTURE.md#snapshot-e-sincronizzazione).
