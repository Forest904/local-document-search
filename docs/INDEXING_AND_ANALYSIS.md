# Indexing Pipeline & Text Analysis v1

**Stato:** analyzer, parser e motore puro implementati e verificati localmente in [M2](M2_VERIFICATION.md); discovery TXT e reader UTF-8 implementati in [M3](M3_VERIFICATION.md); Markdown/PDF e discovery multiformato implementati e verificati localmente in [M4](M4_VERIFICATION.md). [ADR 0007](adr/0007-analysis-and-readers.md).

## 1. Pipeline e responsabilità

Discovery → reader → testo canonico → analyzer per campo → posting nel draft.
I reader non assegnano DocumentId né costruiscono posting. Application associa testo e descriptor.
Un documento contiene un solo content: str; nessun offset strutturale di pagina/sezione.
Nome e contenuto hanno analyzer distinti, indipendenti dal formato del reader.

## 2. Discovery e reader

Scansione ricorsiva ordinata per percorso relativo, suffissi .txt/.md/.pdf riconosciuti senza distinzione maiuscole.
Non seguire symlink, junction o altri reparse point di directory/file; una radice selezionata che sia un link è rifiutata.
M3 abilita solo TXT, M4 tutti i formati. Errori di scansione/lettura fanno fallire il job.
Nessuna lettura di URL, nessun OCR.

| Formato | Regole |
|---|---|
| TXT | UTF-8 strict, BOM iniziale ammesso e rimosso; nessun fallback o sostituzione di caratteri |
| Markdown | Stessa decodifica; markdown-it-py CommonMark con tabelle abilitate, estrazione dai token |
| PDF | pypdf, extract_text standard per pagina nell'ordine del documento, pagine separate da newline |

Markdown include titoli, paragrafi, liste, celle di tabelle, etichette link, alt immagini e codice inline.
Esclude blocchi di codice fenced/indentati, front matter iniziale delimitato da righe --- e token HTML grezzi.
Il front matter è rimosso solo se delimitato e chiuso; senza chiusura si tratta come Markdown normale.
HTML non viene eseguito/renderizzato: token raw HTML scartati, normali token testuali conservati.
Destinazioni dei link/immagini non aggiunte al testo; nessun accesso esterno.
Separare blocchi/celle e contenuti esclusi con whitespace, senza fondere parole adiacenti.
Testo estratto conservato prima della normalizzazione degli analyzer.

PDF misti: pagine immagine non contribuiscono; se il testo totale è vuoto o solo whitespace → Excluded.
PDF illeggibili/corrotti o che richiedono password → ExtractionFailed; nessun prompt password.
Un PDF con testo non-whitespace ma senza token ricercabili resta indicizzato per nome.
TXT/Markdown vuoti sono documenti validi con zero token contenuto.
Encoding invalido o errore reader → job FAILED e nessun commit.

## 3. Analyzer

1. Per il filename sorgente rimuovere solo il suffisso finale supportato; non applicarlo alla query.
2. Nel campo filename dividere confini minuscola→maiuscola, acronimo→parola e lettera↔cifra prima del casefold.
3. Applicare NFC, casefold e NFC al testo; mantenere gli accenti.
4. Tokenizzare sequenze Unicode di lettere/numeri e segni combinanti associati; segni isolati non sono token.
5. Punteggiatura, apostrofi, underscore, trattini, punti ed emoji separano; posizioni consecutive da zero.
6. Nessuno stemming o filtro stop word. Contenuto non suddiviso per CamelCase o lettera/cifra.

Esempi: l'acqua → l, acqua; Report2026Finale.txt → report, 2026, finale;
HTTPServer.md → http, server; caffè e caffe restano distinti.
La query Report2026Finale usa lo stesso split filename; la query txt non trova automaticamente tutti i TXT.
Focus italiano/lingue latine; nessuna segmentazione dedicata per lingue senza separatori.

## 4. Query e posting

Il parser produce clausole di termini o frasi, poi ogni campo applica il proprio analyzer.
Clausole non quotate: tutti i token richiesti in AND. Clausole quotate: adiacenza e ordine.
Tutte le clausole devono corrispondere in filename oppure tutte in content; BOTH unisce i documenti, senza duplicati.
Esempio: machine "deep learning" richiede machine e la frase deep learning nel medesimo campo.
Una frase t0…tk richiede posizioni p…p+k: termini ripetuti usano occorrenze distinte.
Posting: term → document_id → posizioni ordinate, strettamente crescenti e zero-based.
Non condividere contatori di posizione tra campi; interrogare solo snapshot immutabili.
Grammatica ed errori: [Contratti](INTERFACE_CONTRACTS.md).

## 5. Aggiornamenti

Nuovo: assegnare ID e aggiungere catalogo/posting; modificato: sostituire entrambi i campi preservando ID.
Rimosso: eliminare manifest, catalogo e posting; invariato: riutilizzare senza rileggere contenuto.
Escluso: solo manifest, nessun documento/posting. Modifiche solo sul draft.
Dettagli di persistenza in [Snapshot](SNAPSHOTS_AND_SYNC.md).

## 6. Limiti e verifica

Frasi possono attraversare pagine/paragrafi; ordine PDF non garantisce fedeltà al layout visivo.
Nessuna provenienza strutturale, snippet, highlighting o ranking nella v1.
Il testo completo è disponibile tramite GetDocument.
Test obbligatori e fixture: [Test Strategy](TEST_STRATEGY.md).

## Identità nelle esclusioni (2026-11-07)

INDEXED→EXCLUDED rimuove l'ID; EXCLUDED→INDEXED riceve un ID nuovo, mai uno già usato nella vita dell'indice persistente.
