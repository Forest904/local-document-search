# HW3-02 — Correttezza lessicale e rilevanza tematica

## Perimetro e stato

La valutazione usa i TXT di `real-002` (392 documenti) e dei sintetici originali
`small/medium/large-003` (100/1.000/10.000 documenti), identificati nel
[protocollo HW3-01](HW3_01_CORPUS.md). È distinta dalla regressione storica
su otto TXT, dal corpus funzionale V2-01 e dai benchmark V2-02/HW3-03.
Le API, la CLI e gli algoritmi del prodotto non sono modificati.

**Milestone conclusa il 13 novembre 2026:** 120 confronti lessicali esatti su
120, nessuna divergenza irrisolta. I 600 giudizi tematici sono stati approvati
dall'utente e congelati; la valutazione tematica è completa.
Gli [aggregati pubblici](../../experiments/homework3_results.json) conservano
metriche per query, corpus e campo, identità dei corpus e hash dei report.

| Corpus | Confronti esatti | TP | FP | FN | Casi macro validi P/R/F1 |
|---|---:|---:|---:|---:|---:|
| small-003 | 30/30 | 455 | 0 | 0 | 22/30 |
| medium-003 | 30/30 | 4.535 | 0 | 0 | 22/30 |
| large-003 | 30/30 | 45.335 | 0 | 0 | 22/30 |
| real-002 | 30/30 | 232 | 0 | 0 | 25/30 |

Precision, recall e F1 micro e macro sono 1 per ogni corpus; gli insiemi
esattamente corretti sono il 100%. Le query senza attesi hanno zero falsi
positivi e metriche N/A, escluse dalle macro-medie.

## Correttezza lessicale

`experiments/homework3_scan.py` è un verificatore a scansione che importa
soltanto standard library. Implementa dalle regole documentate NFC/casefold,
token Unicode, split del nome, clausole AND e frasi consecutive. Il suffisso
finale viene tolto dal nome del documento, non dalla query; le directory non
partecipano al campo nome. BOTH richiede l'intera query in uno dei due campi.
Le clausole sono validate anche se non esistono documenti o match.

La scansione legge ogni documento e mantiene temporaneamente i suoi token;
non costruisce un indice. Questo flusso batch di correttezza non è ancora la
baseline prestazionale di HW3-03, che dovrà rileggere i file per interrogazione.

Sono congelati due set: trenta query sintetiche comuni alle tre scale e trenta
query reali, ciascuno con 10 nome, 15 contenuto e 5 entrambi. Comprendono termini,
AND, frasi, assenze, Unicode, ripetizioni e negativi fra campi. Le query sono
state preparate leggendo i testi e i metadati; gli attesi completi sono stati
calcolati dall'oracolo, con esempi controllati manualmente, prima delle rispettive
esecuzioni. La selettività viene riportata per query attraverso TP/FP/FN.

`homework3_evaluate.py` usa `compose_cli`, build sincrono e repository volatile.
Richiede tutte le pagine da 50 risultati, ordine PATH e wildcard disabilitate;
controlla snapshot, totale, assenza di duplicati e ordinamento. Il confronto
riguarda insiemi completi, non soltanto la prima pagina o il numero di match.
I controlli SHA-256 prima/dopo l'esperimento appartengono al runner e non
introducono verifiche dei sorgenti nel percorso di ricerca del prodotto.

### Versioni locali

- `experiments/results/homework3/hw3-02-001/`: primo tentativo conservato.
  PowerShell aveva sostituito alcuni accenti nelle query con `?`. Piccolo e
  medio erano terminati; il grande è stato interrotto e il reale non raggiunto
  in quel processo. Questi risultati non sono evidenze finali.
- `hw3-02-002/`: query Unicode corrette secondo i testi originariamente previsti,
  nuovo controllo manuale del termine accentato sintetico, nuovi congelamenti
  e report. La correzione non deriva da una modifica della rilevanza dopo i risultati.
- `hw3-02-001/relevance/`: campione e giudizi tematici, indipendenti dalle query
  lessicali corrette. Le dieci query tematiche non hanno subito alterazioni Unicode.

Gli artefatti congelati includono hash del contenuto, identità del corpus,
manifest, revisione Git, working tree, ambiente e hash degli strumenti.
Le destinazioni devono essere nuove; ogni revisione conserva quella precedente.
Gli hash permettono controlli d'integrità locali, non costituiscono firme o
autenticazione dell'identità del revisore.

## Campione e giudizi

Il campione contiene **40 PDF, 10 TXT e 10 Markdown** come formato originale,
tutti già inclusi in HW3-01. Le quote privilegiano i formati minoritari:
il campione non è proporzionale alla composizione di tutto `real-002`.

La mappa locale delle materie usa la directory del corso e conserva un riscontro
testuale. Per formato, i documenti sono ordinati per byte del TXT e percorso e
divisi in terzili. Il campionamento distribuisce i posti ciclicamente fra gli
strati non vuoti materia/terzile, ordinati lessicograficamente; dentro ciascuno
ordina per SHA-256 di `20261113:percorso`, poi percorso. I duplicati restano
documenti distinti e il registro ne indica la molteplicità nel corpus.

I dieci bisogni, con criteri binari, esempi di inclusione/esclusione e query
iniziali, sono stati approvati dall'utente prima dei giudizi. Sono stati quindi
preparati dieci lotti da 60 coppie, senza mostrare risultati del motore. L'utente
ha approvato tutti i lotti e le 19 interpretazioni di confine, inclusa la lettura
ampia di alcuni criteri su modelli di computazione e ottimizzazione.

La revisione dell'agente comprende passaggi degli originali e **117 pagine
viste su 1.787 pagine dei 40 PDF**, attraverso otto tavole: prima pagina,
pagina pertinente e ultima, quando distinte. Non è una revisione visuale integrale:
i negativi possono risentire di contenuti non osservati. Le pagine estratte
automaticamente non sono conteggiate come pagine viste. I venti TXT/Markdown
sono stati consultati nel sorgente e nelle sezioni pertinenti. Un Markdown
contenente solo il riferimento a un'immagine non disponibile (`D003`) è stato
risolto dalla conferma esplicita dell'utente: schema generale non pertinente
ai dieci bisogni; l'immagine non è stata osservata dall'agente.

I limiti erano espliciti nella revisione finale e sono stati accettati dall'utente.
L'approvazione è distinta dall'attività dell'agente ed è registrata con evidenza,
data, autore e hash della versione. Nessuna approvazione è inferita dal silenzio.
`batches-001` conserva i moduli vuoti, `batches-002` le proposte e `batches-003`
i giudizi approvati; `judgments-frozen.json` precede la ricerca tematica.

## Metriche e risultati tematici

TP, FP e FN sono calcolati sugli insiemi. Precision = TP/(TP+FP),
recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN). Denominatore nullo significa
`N/A` (`null` in JSON), anche per due insiemi vuoti: in quel caso il confronto
esatto può comunque essere corretto. Le micro-metriche sommano i conteggi;
le macro-medie escludono i valori non definiti, dichiarandone il numero valido.
Per query senza attesi si conservano esplicitamente i falsi positivi.

L'indice tematico contiene esclusivamente i 60 TXT selezionati, con nomi,
percorsi relativi e hash conservati. Tutte le dieci query operano sul contenuto.
Non sono usate metriche di ranking né riscritte le query dopo la valutazione.

| Bisogno anonimo | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| N01 | 5 | 1 | 0 | 0,8333 | 1,0000 | 0,9091 |
| N02 | 3 | 1 | 8 | 0,7500 | 0,2727 | 0,4000 |
| N03 | 1 | 1 | 0 | 0,5000 | 1,0000 | 0,6667 |
| N04 | 2 | 0 | 6 | 1,0000 | 0,2500 | 0,4000 |
| N05 | 5 | 0 | 2 | 1,0000 | 0,7143 | 0,8333 |
| N06 | 3 | 1 | 0 | 0,7500 | 1,0000 | 0,8571 |
| N07 | 4 | 5 | 10 | 0,4444 | 0,2857 | 0,3478 |
| N08 | 5 | 13 | 4 | 0,2778 | 0,5556 | 0,3704 |
| N09 | 0 | 0 | 1 | N/A | 0,0000 | 0,0000 |
| N10 | 2 | 0 | 0 | 1,0000 | 1,0000 | 1,0000 |
| **Micro** | **30** | **22** | **31** | **0,5769** | **0,4918** | **0,5310** |
| **Macro** | — | — | — | **0,7284** | **0,6078** | **0,5784** |

Valori validi macro: precision **9/10**, recall **10/10**, F1 **10/10**.
Insiemi tematici esatti: **1/10 (10%)**. La recall riguarda solo questo campione
e questi bisogni; non stima la recall di tutta `Uni`.

Il registro locale contiene 53 diagnosi, una per FP/FN. I falsi positivi derivano
da elenchi di programmi, menzioni insufficienti e termini usati con altro
significato. I falsi negativi riguardano formulazioni più strette del bisogno,
singolare/plurale, sinonimi, abbreviazioni e italiano/inglese. L'assenza di
stemming, traduzione o espansione semantica è una scelta documentata dell'analyzer.
Il controllo indipendente delle dieci query tematiche sui TXT riproduce tutti
gli insiemi del backend; non sono emerse divergenze lessicali in questa prova.

Nessuno dei 53 casi dimostra da solo un difetto di estrazione: il confronto
testuale con gli originali estratti non cambia la presenza letterale della query.
Questo non prova fedeltà visuale: formule, diagrammi, allegati e pagine non viste
rimangono limiti della rappresentazione e della revisione. Non sono state
effettuate correzioni preventive del prodotto né aggiunte soglie di rilevanza.

## Ripetizione e verifiche

I [comandi sperimentali](../../experiments/README.md#homework-3--hw3-02)
coprono congelamento, valutazione, campione, bisogni, lotti e giudizi.
Il riepilogo esportabile contiene solo ID anonimi e metriche; query reali,
percorsi, testi, immagini, giudizi e approvazioni dettagliate restano ignorati da Git.
Il corpus personale non è riproducibile esternamente; le fixture sintetiche
verificano strumenti e invarianti nella suite ordinaria.

Test mirati finali: **24 passati**. Suite backend finale: **488 passati, 7 skip**;
regressione CLI: **10 query e 2 regressioni PASS**. I sette skip sono cinque
casi symlink non consentiti nella sessione Windows, un caso di nomi distinti
solo per maiuscole non supportato dal filesystem e il corpus reale V2 opt-in,
distinto dal corpus Homework verificato qui. Nessuno skip nei test HW3-02.
Il profilo grande è concluso e riconciliato. Le esecuzioni iniziali da 16/480
test sono conservate come passaggi precedenti, non sommate. La revisione Git
è `072a97c712a5df0bfbc36d438f7a718896c006bd`, con working tree modificato;
gli artefatti registrano lo stato e gli hash degli strumenti.

### Osservazione operativa, non benchmark controllato

La validazione finale grande ha occupato circa 33 minuti complessivi
(avvio osservato alle 17:05, conclusione rilevata entro le 17:38, ora italiana).
Include integrità, build, trenta query, tutte le pagine e costruzione degli
snippet. Non sono disponibili tempi separati, ripetizioni, p95, picco RAM
campionato o confronto cronometrato con la scansione. Il dato documenta il
costo della validazione; non permette di dedurre latenza interattiva,
accelerazione o scalabilità. La riduzione di HW3-03 per il tempo disponibile
è esplicitata nella roadmap e non modifica le evidenze di correttezza.
