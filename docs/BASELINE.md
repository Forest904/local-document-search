# Baseline implementata e debito M9

Rilevazione documentale e ispezione del codice v1: **7 novembre 2026**. Nessuna suite o misura fu rieseguita durante la riscrittura. V1 corrisponde ai pacchetti `0.1.0`; gli aggiornamenti V2-02 e V2-03 in fondo registrano il progresso successivo, senza cambiare la fotografia storica.

## Continuità da M0–M9 a v2

La v2 prosegue **nello stesso repository e sugli stessi package backend/frontend**: non è un nuovo progetto né un motore riscritto da zero. I contratti v1 implementati sono la baseline di regressione; ogni sostituzione è limitata alla parte dichiarata negli [ADR v2](adr/README.md). L'archivio conserva motivazioni, specifiche e prove originali.

| Tratto v1 | Base da riutilizzare | Evoluzione v2 |
|---|---|---|
| M0–M2: modello, analyzer, due indici posizionali | Identità, testo canonico, AND/frasi e corrispondenza per campo | Vocabolario ordinato, prefissi e ranking; verificare equivalenza delle query esatte |
| M3–M4: CLI Homework e reader | CLI TXT/MD/PDF, policy di errori/esclusioni e fixture | CLI invariata; prove reader completate sul pacchetto finale |
| M5–M7: SQLite, sync e job | Snapshot atomici, single-writer, diff e ricerca concorrente | Migliorare storage, tempi e memoria; aggiungere cancel e controllo metadati in ingestione |
| M8: desktop Qt Widgets | Casi d'uso applicativi e flussi di ricerca/anteprima | Sostituire la sola presentazione con Qt Quick, lingue, temi e accessibilità |
| M9: ZIP e collaudo locale | Procedure di build, corpus sintetico, fault test e misure storiche | Installer offline pubblico; prove mancanti trasferite in V2-08 |

Lo **storage v2 separato** è una scelta di compatibilità dei dati, non una separazione del prodotto o del codice: v1 continua a funzionare sui propri indici mentre v2 costruisce i suoi. Non importare dati v1 automaticamente e non considerare gli indici v1 un prerequisito per l'installazione v2. La CLI Homework continua a usare il backend condiviso con il proprio comportamento v1.

## Materiale di test esistente da cui parte V2-01

[`experiments/run_homework3.py`](../experiments/run_homework3.py) genera otto TXT sintetici in una directory temporanea e contiene dieci query più regressioni con liste attese scritte per il corpus. [`experiments/m9_corpus.py`](../experiments/m9_corpus.py) genera deterministicamente TXT/Markdown/PDF, un manifest con hash dei file e sette query attese; [`experiments/run_m9.py`](../experiments/run_m9.py) ne controlla i risultati ma misura anche build, sync e query. Le [fixture reader](../backend/tests/fixtures/README.md) e i test relativi coprono formati ed esiti mirati.

Sono basi concrete da riusare o integrare in [V2-01](TEST_DATASETS.md), non un corpus ibrido già pronto: manca una raccolta Internet con provenienza/licenza verificata e manca la relativa ground truth. Le misure M9 restano evidenze storiche; V2-01 costruisce validazione funzionale, mentre V2-02 definisce benchmark e budget. Nessun download o corpus reale è stato eseguito in questa revisione documentale.

## Stato verificato nel codice

| Area | Implementazione corrente | Evidenza da consultare |
|---|---|---|
| Ricerca | Due indici posizionali; dizionari Python congelati, lookup esatto con `terms.get`, AND/frasi e ordinamento per percorso | [Indice](../backend/src/local_document_search/domain/index.py), [query](../backend/src/local_document_search/domain/queries.py) |
| Contratti | Ricerca per campo/pagina, dettagli per snapshot, job e report di sessione; nessun cancel, ranking o suggerimento | [DTO](../backend/src/local_document_search/application/contracts.py), [job](../backend/src/local_document_search/application/jobs.py) |
| Persistenza | SQLite, indici/draft in RAM, snapshot completi, sync e lock di sessione | [Specifica v1](archive/v1/SNAPSHOTS_AND_SYNC.md), [repository](../backend/src/local_document_search/infrastructure/sqlite_snapshot_storage.py) |
| Desktop | PySide6 Qt Widgets italiano, testo completo, nessuna nuova UI QML | [Entrypoint](../frontend/src/local_document_search_desktop/main.py) |
| Distribuzione | ZIP standalone personale, non installer pubblico | [Packaging attuale](../scripts/package/README.md) |

Le misure backend più recenti riportate in [M9, aggiornamento del 7 novembre](archive/v1/M9_VERIFICATION.md) riguardano 3.000 documenti e 29.993.956 byte di testo: build 105,448 s, riapertura 20,781 s, sync incrementale 46,550 s, picco working set 944,9 MiB. Riapertura a cache calda; non sono soglie né risultati sul target v2. Il report conserva ambiente, metodo e limiti.

## Lacune da trasferire, non prove superate

**M9 resta parzialmente accettata.** Non è richiesto completare ora il collaudo dello ZIP v1. Le prove sotto devono essere effettuate sul pacchetto v2 finale; quelle sorgente non le sostituiscono.

| ID | Mancanza documentata sul pacchetto corrente | Destinazione v2 | Scenario |
|---|---|---|---|
| M9-G01 | Ciclo completo cambio directory e rebuild | V2-04, V2-08 | T09, T14 |
| M9-G02 | Pulizia rifiutata durante job | V2-04, V2-08 | T10, T16 |
| M9-G03 | PDF protetto/senza testo/misto e TXT/MD vuoti | V2-04, V2-08 | T02 |
| M9-G04 | Ricerca e anteprima sotto carico | V2-06, V2-08 | T07, T08, T12 |
| M9-G05 | Windows pulito senza Python/tool di sviluppo | V2-07, V2-08 | T01, T15 |
| M9-G06 | Account standard distinto | V2-07, V2-08 | T01, T16 |
| M9-G07 | CI della revisione finale e artefatto da revisione pulita | V2-08 | T19 |

[Txx: scenari di accettazione](TEST_STRATEGY.md). Ogni chiusura richiede revisione, artefatto, ambiente ed esito; il rinvio deciso per v1 non elimina il requisito v2.

## Lettura delle evidenze storiche

[Archivio v1](archive/v1/README.md) conserva specifiche e report M0–M9. Le sezioni iniziali dei report possono descrivere artefatti precedenti: per M9 prevale l'aggiornamento corrente datato, senza cancellare le prove storiche. Il manifest dell'ultimo ZIP registra una baseline Git con working tree modificato; non prova una build della revisione oggi in uso.

La CI citata nei report riguarda la baseline indicata, non la v2. Le simulazioni di fault non dimostrano resistenza a perdita fisica di alimentazione o OOM non intercettabile. Il materiale [Homework](homework-3/README.md) rimane separato e non prova l'invio amministrativo al docente.

## Aggiornamento V2-02

Il corpus e il runner prestazionali sintetici sono descritti nella
[relazione V2-02](V2_02_BENCHMARK.md). Misurano il backend da sorgente sugli
stessi casi d'uso v1, senza modificare il motore. I report small e adverse
hanno completato tre cicli; anche il target 10.000/300 MB ha tre cicli `PASS`
con 299.948.099 byte di testo estratto. Il build richiede 433,0–440,1 s,
la ricerca dopo riapertura 69,0–70,6 s e il sync incrementale 161,4–162,2 s,
con picco working set di 4125 MiB. I risultati e i budget approvati sono
distinti dalle prove storiche M9 e dalla validazione funzionale V2-01.
I budget V2-D01 sono approvati nell'[ADR 0014](adr/0014-v2-performance-budgets.md),
ma il backend v1 misurato ne supera diversi.

## Aggiornamento V2-03

Il backend include vocabolari ordinati per campo ricostruiti con gli snapshot, ricerca con prefissi espliciti e suggerimenti separati per versione. Il formato SQLite e la CLI Homework non sono cambiati. Le misure e lo stato del gate prestazionale sono nella [relazione V2-03](V2_03_RETRIEVAL.md); storage fisico e lifecycle restano V2-04. La tabella iniziale documenta la baseline v1 da cui parte la roadmap.

## Avanzamento V2-04

La composizione backend `compose_v2_application` usa uno storage SQLite separato, con versioni immutabili di documento e posting compressi. Sono implementati cancel cooperativo, verifica dei metadati in ingestione e recovery/rebuild espliciti. La composizione v1 e la CLI restano disponibili per regressione. Le [misure V2-04](V2_04_STORAGE.md) chiudono localmente il gate prestazionale target; la tabella iniziale resta la fotografia storica v1.

## Avanzamento V2-05

Il backend offre filtri per formato/cartella, ordinamento per rilevanza o percorso, snippet e intervalli di evidenziazione dalla versione acquisita. Ricerca e dettagli accettano uno `snapshot_id` esplicito; la CLI conserva i default v1. [Decisioni](adr/0010-v2-retrieval.md) e [contratti](INTERFACE_CONTRACTS.md). La tabella iniziale resta la fotografia storica v1; la prova della UI e del pacchetto appartiene a V2-06/V2-08.
