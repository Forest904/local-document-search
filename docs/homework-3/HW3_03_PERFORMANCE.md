# HW3-03 — Pilot prestazionale ridotto

## Perimetro e metodo

Solo `synthetic-small-003`, 100 TXT, e le 30 query con attesi congelati in
`hw3-02-002/small-frozen.json`. Nessuna nuova prova reale, media o grande,
ottimizzazione del prodotto o modifica di API/CLI. Le evidenze sono distinte
da HW3-02, V2-01 e V2-02; la campagna estesa resta rinviata.

`experiments/homework3_performance.py` usa un processo e una build volatile
tramite `compose_cli`. `perf_counter` misura separatamente `build.execute`
e il recupero completo per query. Composizione, verifica degli hash,
registrazione dei risultati e confronti con gli attesi sono fuori dai tratti
cronometrati. La preparazione/conversione è esclusa.

Un passaggio di warm-up (passaggio 0) precede tre passaggi misurati. Ogni
passaggio segue l'ordine congelato delle query: indice poi scansione nei
passaggi 0 e 2, scansione poi indice nei passaggi 1 e 3. Ogni risultato,
compresi i warm-up, è confrontato con l'insieme completo atteso.

Il backend recupera pagine da 50 in ordine PATH, con wildcard disabilitate,
snippet e controlli di paginazione. La baseline chiama l'oracolo indipendente
con una query alla volta: enumera, apre e analizza ogni TXT a ogni invocazione,
senza indice o cache applicativa. Analizza entrambi i campi anche per query
su un solo campo. I due metodi svolgono quindi lavoro diverso; il rapporto
misura questi percorsi completi, non il solo lookup degli indici.

## Budget e artefatti

Budget di 600 secondi dall'avvio del runner, comprendente controlli preliminari,
metadati, build, warm-up e misure. Controllo cooperativo fra operazioni:
nessuna nuova operazione di benchmark inizia a budget esaurito; quella in corso
può sforare. Il controllo finale d'integrità e il salvataggio vengono comunque
eseguiti fuori dal budget e dai tempi di ricerca. Non è un timeout preemptive.

Ogni destinazione deve essere nuova. `setup.json` registra ordine e ambiente;
`build.json` registra la build; `samples.jsonl` viene aggiornato e scaricato su
file dopo ogni campione; `report.json` conserva esiti, differenze, errori e
casi mancanti; `summary.json` contiene gli aggregati esportabili e l'hash del
report. Errori interrompono il run senza rilanci; differenze negli insiemi
restano registrate e non selezionano i campioni da misurare.

Completezza, correttezza dei confronti eseguiti e timeout sono indipendenti:
correttezza vera su un run parziale non attesta i casi mancanti. Campioni
falliti non sono latenze valide; rimangono nel report con durata fino all'errore.

## Statistiche e limiti

Mediana e min–max dei tre campioni per query e metodo; per campo le stesse
statistiche sull'insieme dei campioni misurati, quindi una distribuzione di
query eterogenee. Rapporto per query = mediana scansione / mediana indice;
per campo si riassume la distribuzione di tali rapporti. Numerosità esplicite,
anche per risultati incompleti; nessuna soglia di accettazione prestazionale.

CPU, RAM installata (non picco RAM), OS, Python, revisione, working tree,
hash degli strumenti e del corpus e stato batteria osservabile accompagnano
il report. Alimentazione non rilevabile indicata esplicitamente. Cache OS non
svuotata: integrità, build e warm-up possono riscaldarla; nessuna misura è
dichiarata a cache fredda. Nessuna misura della residenza effettiva in cache.

Un corpus, un processo e tre campioni non dimostrano scalabilità, variabilità
fra processi o p95. Nessun picco RAM o grafico richiesto. Report e dati grezzi
restano locali; solo aggregati, ID e metadati non personali sono versionati.
Relazione e PDF sono oggetto di HW3-04.

## Evidenze

**Pilot concluso il 13 novembre 2026**, run locale
`experiments/results/homework3/hw3-03-001/`. Build: **1,910427 s**, 100/100 TXT,
zero esclusioni. Durata operativa **138,388906 s** su 600 disponibili;
nessun timeout, errore o caso mancante. Integrità verificata prima e dopo.
**240/240 confronti esatti**: 60 warm-up e 180 misurati (90 per metodo).

[Aggregati pubblici e identità](../../experiments/homework3_performance_results.json).
Tempi della tabella in millisecondi; rapporti adimensionali, mediana dei
rapporti per query (non rapporto fra le mediane aggregate di campo).

| Campo | Campioni per metodo | Indice mediana [min–max] | Scansione mediana [min–max] | Rapporto mediano [min–max] |
|---|---:|---:|---:|---:|
| Nome | 30 | 1,333 [0,146–3,145] | 420,542 [401,308–490,992] | 319,419 [220,576–2896,603] |
| Contenuto | 45 | 454,039 [0,136–5575,428] | 456,790 [429,950–577,041] | 1,185 [0,085–3322,625] |
| Entrambi | 15 | 389,425 [1,301–467,863] | 445,700 [432,113–549,218] | 1,228 [1,047–329,870] |

Rapporti sotto 1 indicano scansione più veloce: il risultato non dimostra
un vantaggio uniforme dell'indice. L'eterogeneità delle query e il lavoro
aggiuntivo del backend impediscono di attribuire questi tempi al solo lookup.
Nessuna causa specifica del rallentamento è stata accertata.

Ambiente: Windows 11, Python 3.12.2, AMD Ryzen AI 7 350, RAM fisica rilevata
33.598.853.120 byte; stato batteria CIM 1, carica 99% all'avvio. Revisione
`750a1f9ac013f51ae755a3453edca393b1916135`, working tree modificato;
hash degli strumenti registrati. Durante il run sono stati aggiornati soltanto
documenti; nessuna suite concorrente è stata avviata dall'agente. Carico esterno
non controllato. Queste evidenze non attestano un installer o una release.

Verifiche: **29 test mirati passati** (5 HW3-03 e 24 HW3-02), nessuno skip;
regressione CLI **10 query e 2 regressioni PASS**. Suite backend completa non
ripetuta per questa modifica esclusivamente sperimentale. Il pilot ridotto
è concluso; campagna estesa non eseguita. Alla chiusura del pilot HW3-04
restava da eseguire; la successiva [chiusura della relazione](HW3_04_REPORT.md)
documenta PDF e verifiche finali senza nuove misure prestazionali.
