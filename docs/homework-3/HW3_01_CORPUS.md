# HW3-01 — Protocollo e stato dei corpus

## Generatore corrente

`experiments/homework3_corpus.py` prepara corpus locali, separati dal corpus funzionale V2-01 e dai benchmark V2-02. Il generatore `hw3-original-2`, seed **20261113**, produce paragrafi originali parametrizzati in italiano e inglese per analisi, reti, basi di dati, fisica, storia e linguistica. Ogni materia compare in entrambe le lingue già nei primi 100 documenti. Appunti, schede di laboratorio, esercitazioni e riepiloghi variano intestazioni, ordine e numero delle sezioni, esempi numerici, elenchi e ripetizioni lessicali. I paragrafi vengono aggiunti progressivamente, senza riempimento tramite copia di un unico blocco.

Percorso e byte dipendono soltanto da versione, seed e ID; il profilo sceglie il numero di ID a partire da zero. Ogni blocco di dieci ID ha obiettivi di 6, 12, 18, 24, 30, 30, 36, 42, 48 e 54 kB decimali. La generazione termina su una frase completa dopo il raggiungimento dell'obiettivo; conta i byte UTF-8, non i caratteri. Il volume totale ammesso è ±5% di 3/30/300 MB. Percorsi con materia, lingua, struttura e ID includono spazi, trattini e Unicode compatibili con Windows; gli ID impediscono collisioni anche ignorando le maiuscole. Il nome completo non viene copiato nel contenuto.

Il lessico alterna termini comuni, disciplinari e rari, con ripetizioni controllate. **La distribuzione artificiale non rappresenta il linguaggio universitario reale.** I testi inglesi possono conservare etichette di materia italiane nei titoli e percorsi. Nessun testo è scaricato da Internet.

## Famiglie lessicali e manifest

Ogni blocco di dieci documenti contiene tutte le famiglie seguenti. I termini riservati sono distinti dal lessico dei paragrafi:

| Famiglia | Nome | Contenuto |
|---|---|---|
| Solo nome | `zefirnome` | assente |
| Solo contenuto | assente | `zefirtesto` |
| Coppia positiva nel nome | `velnaro tespilo` | assenti |
| Coppia positiva nel contenuto | assenti | `velnaro tespilo` |
| Campi separati, direzione 1 | `velnaro` | `tespilo` |
| Campi separati, direzione 2 | `tespilo` | `velnaro` |
| Frase consecutiva | assenti | `frandilo spolvero` |
| Frase interrotta | assenti | `frandilo passaggio spolvero` |
| Ordine invertito | assenti | `spolvero frandilo` |
| Sezioni distanti | assenti | `distalvo` all'inizio, `remotivo` nell'appendice |

`assentivo`, `introvello` e `vacanzuro` sono dichiarati assenti da tutti i nomi e contenuti. La parola effettiva `passaggio`, non la punteggiatura, interrompe la frase. Queste annotazioni descrivono la costruzione: **non sono query o attesi HW3-02**.

Il nuovo `manifest.json` (schema 2), esterno a `txt/`, registra versione, seed, profilo, conteggio atteso, tolleranza, byte effettivi, SHA-256, ID, lingua, materia, struttura, famiglia, sezioni e numero di paragrafi di ogni documento. Conserva descrizioni delle famiglie, termini assenti, distribuzioni e ambiente/revisione Git. L'identità è SHA-256 della serializzazione JSON compatta dell'elenco **ordinato per percorso** delle coppie percorso/hash: non dipende da metadati d'esecuzione o ordine delle righe. I manifest schema 1 restano leggibili e verificabili secondo la loro identità storica.

`verify` controlla file mancanti/aggiuntivi, dimensioni, hash, UTF-8 valido, conteggio previsto, volume e coerenza dei metadati. Per lo schema 2 rigenera anche ogni documento da seed e ID e confronta le caratteristiche: un manifest coerentemente riscritto con contenuti diversi non viene accettato. `verify-nested` verifica integralmente i tre profili e confronta percorsi/hash degli ID condivisi; richiede stesso seed e versione. Le destinazioni di generazione devono essere nuove.

## Risultati storici

I profili senza suffisso erano basati su cinque parole ripetute: 100/1.000/10.000 TXT, 2.998.000/30.003.500/300.047.000 byte. Restano locali e non rappresentano i sintetici correnti. I profili `-002` sono un passaggio intermedio di questa revisione, conservato dopo la correzione di un carattere degradato in una frase; quelli finali usano il successivo suffisso comune libero `-003`. Nessun corpus precedente è stato sovrascritto.

La preparazione storica `real-001` conteneva 427 candidati, 397 TXT e 30 esclusioni senza testo, con 19 gruppi di duplicati. I controlli preliminari (20 campioni, 81 sospetti, stato `checked_with_limits`) e le suite da 441/449 test sono evidenze storiche, superate per lo stato corrente dalla selezione e accettazione di `real-002` e dalle verifiche riportate sotto.

## Criteri congelati di inclusione e valutazione

Il sistema ricerca lessicalmente nel nome del file e nel testo estraibile dai reader adottati. Ogni PDF con testo non-whitespace viene incluso, senza soglia minima: poche parole o un titolo testuale sono sufficienti, anche con molte immagini. Il campo filename usa il nome base e content comprende gli eventuali titoli estratti. Non si inferiscono titoli dalle immagini. I duplicati restano documenti distinti.

L’assenza di OCR è un confine del progetto. Un PDF escluso è descritto come «nessun testo estratto con questo reader e questa versione», non come documento vuoto o sicuramente scansionato. PDF protetti, corrotti e illeggibili restano errori distinti. Il rapporto fra dimensione del TXT e del PDF serve soltanto a selezionare casi per la revisione: immagini, font e compressione impediscono di usarlo come misura di fedeltà dell’estrazione.

Il flusso documentato distingue inventario e selezione didattica, candidati, inclusi, esclusi per motivo ed errori. L’inventario registra le directory escluse senza enumerarne il contenuto: non fornisce un conteggio completo di tutti i file di Uni. Nella preparazione storica real-001, per i 427 candidati selezionati: 397 inclusi, 30 esclusi senza testo estraibile, zero errori di conversione. Il 93,0% è il tasso di ammissione alla conversione, non recall né percentuale di informazione visibile ricercabile.

In HW3-02, correttezza lessicale sul TXT, rilevanza tematica giudicata sugli originali e copertura dell’ingestione restano separate. I documenti rilevanti soprattutto per immagini possono risultare mancati: conservare questi risultati e discuterli come limite della rappresentazione testuale. Non estendere la recall del sottoinsieme all’intera Uni e non escludere documenti con poco testo dopo aver osservato metriche sfavorevoli.

`complete` descrive solo l’esito della preparazione: ogni candidato deve avere un risultato ammesso e non devono esserci errori d’inventario. `verify` controlla originali inclusi ed esclusi, TXT dei soli inclusi, copertura dell’inventario, dimensioni, hash, duplicati e identità. Il report locale `metadata/integrity_verification.json` registra il controllo; `manual_review.json` conserva separatamente autori, metodi e limiti delle revisioni. Il manifest precedente è conservato localmente.

## Revisione didattica real-002

Una nuova versione locale deriva dalle copie verificate di real-001. Cinque documenti operativi o di dipendenze sono esclusi dal TXT valutato; tre README con spiegazioni didattiche sono mantenuti con motivazione registrata. La versione contiene 392 TXT, cinque esclusioni didattiche e 30 PDF senza testo estraibile. Il runner verifica provenienza, copie, estratti e identità della nuova versione; real-001 resta intatta.

La revisione visuale rappresentativa dei PDF di real-002 copre **tutti i 376 PDF**: **1.105 pagine effettivamente osservate** su 14.141 (tutte le pagine per PDF fino a tre pagine; prima, centrale e ultima per gli altri). Le pagine sono state renderizzate in tavole a risoluzione ridotta e ispezionate dall'agente. Nove PDF hanno richiesto una copia temporanea con percorso breve, verificata mediante SHA-256, per superare errori del renderer legati ai percorsi; anche le loro 27 pagine campionate sono state osservate. Per i 346 PDF inclusi il testo restituito dal reader sulle pagine campionate compare nel TXT conservato; per i 30 esclusi non è atteso un TXT. Questo controllo di presenza usa lo stesso reader e non prova la fedeltà parola per parola rispetto all'immagine. Il registro locale `metadata/pdf_visual_review.json` distingue pagine osservate, etichetta visuale, esito testuale e limiti.

**Decisione di accettazione:** l'utente considera concluse le verifiche delle conversioni per tutti i 392 TXT del corpus e accetta come validati i 376 PDF visionati nel campionamento concordato. Il registro generale è `completed` come esito della decisione, attribuita all'utente; il controllo visuale delle pagine campionate resta attribuito all'agente. I 30 PDF senza testo estraibile conservano l'etichetta di esclusione. Le pagine non campionate, la fedeltà parola per parola di formule e tabelle e il contenuto delle immagini restano limiti metodologici dichiarati, senza casi pendenti nella decisione di accettazione.

## Chiusura verificata — 13 novembre 2026

**HW3-01 conclusa.** Corpus corrente: `real-002` accettato e tre sintetici `-003` verificati integralmente e annidati. Evidenze locali sotto `experiments/results/homework3/`: `hw3-01-verification-003.json`, manifest dei tre profili, registri di `real-002`, `hw3-01-targeted-tests.txt`, `hw3-01-backend-tests.txt` e `hw3-01-cli-002.json`. I report e i testi restano ignorati da Git.

| Profilo finale | TXT | Byte UTF-8 | Min / mediana / max byte | IT / EN |
|---|---:|---:|---|---|
| small-003 | 100 | 3,008,718 | 6034 / 30103 / 54215 | 52 / 48 |
| medium-003 | 1,000 | 30,082,141 | 6001 / 30080 / 54215 | 502 / 498 |
| large-003 | 10,000 | 300,840,184 | 6000 / 30083 / 54228 | 5002 / 4998 |

Tutti i volumi sono entro ±5%. Ogni struttura conta 25/250/2.500 documenti; ciascuna delle dieci famiglie conta 10/100/1.000 documenti. Analisi, reti, basi di dati e fisica contano ciascuna 17/167/1.667 documenti; storia e linguistica 16/166/1.666. Tutte le dodici combinazioni materia/lingua sono presenti in ogni profilo. Le nove classi dimensionali hanno ciascuna 10/100/1.000 documenti, salvo 30 kB che compare due volte per blocco e quindi ne ha 20/200/2.000. Il report locale conserva anche le distribuzioni incrociate.

Identità SHA-256 dei corpus finali:

- `small-003`: `b61a15c9a8a513b67e2ef221a70cbfde110179088953c0aa0db757be3dab9715`.
- `medium-003`: `b871bc7cfb89c6b223e0a3a81e114c5b29315990d59841ac973c60566392bff0`.
- `large-003`: `396a82555f2da6db726d16376a84ff40d633fd5fe092905a2d6ff35340019f11`.
- `real-002`: `310404c579e638a92f9d1cf6ed2c1bf608068befdf7b5f4503d18239079bfb03` (invariata).

Verifiche sul working tree modificato della revisione `a231873f79677f39236dd72ff98c84345e5db0e3`, Python 3.12.2, Windows 11 x64; il report registra ambiente completo e SHA-256 del runner per identificare anche il codice non ancora committato. La verifica reale ha riconciliato 427 candidati: 392 convertiti, 30 esclusi senza testo e 5 esclusioni didattiche; zero errori. L'accettazione delle conversioni rimane una decisione dell'utente, distinta dalla revisione rappresentativa dell'agente.

**Test mirati: 25 passed. Suite backend: 464 passed, 7 skipped. CLI: 10 query e 2 regressioni PASS**, controllando conteggi e singoli esiti del JSON. I sette skip sono cinque casi symlink non consentiti in questa sessione Windows, un caso di nomi distinti solo per maiuscole non supportato dal filesystem e il corpus reale V2 opt-in. Quest'ultimo è distinto da `real-002`, verificato esplicitamente qui. Nessuno skip nelle prove HW3-01 mirate.

Le verifiche HW3-01 coprono costruzione, integrità e regressioni; non misurano recall, rilevanza tematica o prestazioni dei nuovi corpus. Al momento di questa chiusura HW3-02 e successive restavano aperte; il successivo [protocollo HW3-02](HW3_02_EVALUATION.md) registra separatamente le valutazioni. La distribuzione sintetica artificiale, l'assenza di OCR e le pagine reali non campionate restano limiti dichiarati; non attestiamo una revisione integrale delle 14.141 pagine.
