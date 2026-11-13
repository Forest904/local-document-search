# Homework 3 — Roadmap di valutazione e relazione

**Stato: HW3-01 e HW3-02 concluse; pilot ridotto HW3-03 concluso; campagna estesa rinviata; HW3-04 da eseguire.** La mail del docente richiede di esplicitare costruzione del dataset e metriche, raccomanda più documenti per valutare tempi e recall e chiede l'indirizzo email nella relazione. Le evidenze di HW3-01 e HW3-02 sono nei protocolli collegati; nessun invio del report è attestato.

Restano separate quattro evidenze: [regressione Homework](QUERY_TEST_PLAN.md) su otto TXT (dieci query e due regressioni), nuova valutazione Homework qui pianificata, [corpus funzionale V2-01](../TEST_DATASETS.md) e [benchmark desktop V2-02](../PERFORMANCE.md). Nessuna modifica prevista alle API pubbliche, alla semantica di ricerca o alla CLI; strumenti nuovi solo nell'area sperimentale. Le milestone si eseguono nell'ordine seguente.

## HW3-01 — Corpus tracciabili

Criteri approvati: includere ogni PDF con testo estraibile non vuoto, senza soglia minima; i PDF senza testo estratto dal reader sono esclusioni previste e non impediscono il completamento della preparazione. Errori, integrità e revisione visuale hanno stati separati. [Protocollo e copertura](HW3_01_CORPUS.md). Milestone conclusa il 13 novembre 2026, dopo verifica integrale dei corpus e regressioni.

- [x] Inventariare localmente la cartella universitaria `Uni` indicata dall'utente; selezionare TXT, Markdown e PDF testuali universitari, escludendo directory tecniche (`.git`, ambienti virtuali, dipendenze, build). Registrare criteri, conteggi, duplicati, esclusioni ed errori.
- [x] Preparare una copia ordinaria fuori da OneDrive in `experiments/results/homework3/`, ignorata da Git secondo la scelta dell'utente, senza modificare gli originali, seguire symlink/junction o cambiare le protezioni del backend sui reparse point.
- [x] Conservare i TXT validi e convertire MD/PDF in TXT UTF-8 tramite i reader esistenti: un sorgente = un TXT, senza suddivisione in pagine. Preservare nomi base e percorsi relativi sotto directory separate per formato, evitando collisioni.
- [x] Conservare un manifest locale con provenienza, hash, versioni degli estrattori, dimensioni e mappa sorgente/TXT. Distinguere PDF senza testo, protetti ed errori di lettura, senza OCR. Gli hash verificano il corpus sperimentale, non cambiano il diff del prodotto.
- [x] Revisione delle conversioni accettata dall’utente: registro `completed`; controlli preliminari sui 20 campioni e sospetti, poi revisione rappresentativa dell’agente su 376 PDF e 1.105 pagine. Non equivale a controllo integrale delle pagine; limiti registrati nel protocollo.
- [x] Generare sintetici originali IT/EN a temi con seed fissato: profili annidati da 100/1.000/10.000 TXT, circa 3/30/300 MB di testo. Variare lunghezze, frequenze, nomi, sezioni e ripetizioni; includere Unicode, negativi difficili AND/frasi e vincoli fra campi. Documentare i limiti del linguaggio generato.

**Completamento ed evidenze:** corpus identificati e verificabili, manifest e registro di preparazione completi, nessuna omissione silenziosa. Testi personali, copie, estratti e artefatti grezzi restano fuori Git. Conteggi e volumi finali derivano dalla preparazione, non dall'inventario preliminare.

Evidenze riconciliate: `real-002` verificato, 392 TXT e accettazione dell'utente; sintetici `-003` da 100/1.000/10.000 TXT verificati e annidati; 25 test mirati passati, backend 464 passati/7 skip, dieci query e due regressioni CLI superate. Protocollo, istruzioni, strategia e indici aggiornati. [Aggregati, identità e limiti](HW3_01_CORPUS.md#chiusura-verificata--13-novembre-2026).

## HW3-02 — Correttezza e rilevanza

[Protocollo ed evidenze](HW3_02_EVALUATION.md): milestone conclusa il 13 novembre
2026, 120/120 confronti lessicali esatti, 600 giudizi approvati e report tematico
completo. Test mirati 24 passati, backend 488 passati/7 skip, CLI 10+2 PASS.

- [x] Preservare le dieci query storiche e le due regressioni. Preparare 30 query per ciascun nuovo corpus: 10 nome, 15 contenuto, 5 entrambi; termini, AND, frasi, assenze e selettività diverse. Fissare query e attesi prima di osservare i risultati del motore.
- [x] Implementare un verificatore a scansione indipendente, senza riusare analyzer, parser o evaluator del prodotto. Applicare le regole documentate e confrontare insiemi completi, non conteggi o prime pagine.
- [x] Riportare TP, FP, FN, precision, recall e F1 per query, aggregati micro/macro e percentuale di insiemi esattamente corretti. Denominatori nulli producono `N/A`, con numero di casi validi dichiarato; per query senza attesi controllare esplicitamente i falsi positivi.
- [x] Selezionare 60 documenti reali stratificati per materia, formato originale e lunghezza. Definire 10 bisogni informativi, ciascuno con criterio binario di rilevanza e query iniziale.
- [x] Preparare tutti i 600 giudizi documento-bisogno e sottoporli alla revisione finale dell'utente senza mostrare i risultati del motore. Risolvere gli ambigui prima di congelare i giudizi.
- [x] Valutare la rilevanza su un indice dei soli 60 documenti: la recall tematica si riferisce a questo sottoinsieme, non a tutta `Uni`. Non usare metriche di ranking per la CLI ordinata per percorso.

**Completamento ed evidenze:** query e giudizi versionati localmente con identità del corpus, confronti completi senza differenze lessicali inattese, tabelle metriche e diagnosi degli errori. La qualità tematica si riporta anche se imperfetta: distinguere limiti delle query, analyzer ed estrazione. Correttezza sul TXT convertito non dimostra fedeltà dell'estrazione al sorgente.

## HW3-03 — Prestazioni e scalabilità

**Scope ridotto concordato il 13 novembre 2026 per il tempo disponibile:**
eseguire soltanto un pilot su `small-003` (100 TXT), poi passare a HW3-04.
Non dichiarare completata la campagna estesa di scalabilità. Le verifiche
HW3-02 forniscono correttezza e un'osservazione del costo complessivo del run
grande (circa 33 minuti), non sostituiscono misure separate o ripetute.

### Pilot richiesto prima della relazione

- [x] Riutilizzare le 30 query e gli attesi congelati di `small-003`. Confrontare indice volatile e scansione indipendente sugli stessi TXT; la scansione apre e analizza i documenti a ogni query, senza cache applicativa.
- [x] Cronometrare separatamente build e ricerca con `perf_counter`; misurare il recupero completo su entrambi i metodi, senza stampa. Il backend include snippet e controlli di paginazione; dichiarare questa differenza di lavoro rispetto alla scansione. Verificare gli insiemi fuori dai tratti cronometrati.
- [x] Eseguire un processo, un passaggio di warm-up e tre ripetizioni per query, in ordine deterministico registrato. Riportare tempi grezzi, mediana e intervallo min–max per query/campo e rapporto scansione/indice; non stimare p95 da tre valori.
- [x] Registrare hardware, Python, revisione, working tree, hash degli strumenti e corpus, stato alimentazione e condizioni di cache osservabili. Cache OS non svuotata; nessuna dichiarazione di cache fredda. Preparazione/conversione escluse dai tempi.
- [x] Budget operativo: dieci minuti per il pilot, nessuna nuova prova grande. Se esaurito, conservare risultati e timeout, indicare i casi mancanti senza selezionare soltanto quelli favorevoli; passare comunque a HW3-04 con il limite esplicito.

**Completamento del pilot:** report locale e aggregati pubblici, confronto di
correttezza, misure separate e limiti. Un solo corpus e un solo processo non
dimostrano scalabilità o variabilità fra processi. Il picco RAM non è requisito
del pilot. Nessuna ottimizzazione del prodotto rientra in questa riduzione.

**Evidenze del 13 novembre 2026:** pilot concluso su 100 TXT, build 1,910427 s,
run 138,388906 s, 240/240 confronti esatti, nessun timeout o caso mancante.
Test mirati 29 passati, CLI 10+2 PASS. [Protocollo e misure](HW3_03_PERFORMANCE.md).
Campagna estesa non eseguita; nessuna conclusione di scalabilità.

### Campagna estesa rinviata, non vincolante per HW3-04

Il protocollo originario resta sotto come lavoro non eseguito; i suoi requisiti
di ripetizione, p95, RAM e scalabilità non sono attribuiti al pilot.

- [ ] Confrontare indice Homework in memoria e scansione sequenziale sugli stessi TXT, campi e query. La baseline apre e analizza i documenti a ogni interrogazione, senza indice o cache applicativa.
- [ ] Separare preparazione/conversione, avvio del processo, build e ricerca. Misurare prima pagina di 50 risultati con totale e recupero completo, senza stampa a console.
- [ ] Eseguire tre cicli in processi nuovi, cinque warm-up e cento campioni per query, con ordine deterministico mescolato. Verificare la correttezza fuori dalle sezioni cronometrate.
- [ ] Registrare durata build, file/s e MB/s, latenza mediana/p95, picco RAM e accelerazione rispetto alla scansione. Mostrare variabilità per ciclo, campo e selettività, non solo un aggregato.
- [ ] Registrare hardware, ambiente, revisione, stato Git, alimentazione e cache. Non svuotare la cache OS e non dichiarare misure a cache fredda.
- [ ] Eseguire prima il pilot da 100 documenti. Timeout: 30 minuti per build e 60 secondi per singola query; superamenti rendono la misura incompleta, senza scartare campioni né dichiarare PASS.
- [ ] Mantenere i budget desktop separati dalle misure Homework. Riportare V2-02 solo in appendice con revisione e artefatto identificati.

**Completamento ed evidenze:** campioni grezzi locali, riepiloghi riproducibili e grafici di scalabilità; limiti, timeout e prove incomplete espliciti. Nessuna ottimizzazione preventiva o nuova soglia di accettazione prestazionale implicita.

## HW3-04 — Correzioni, relazione e consegna

- [ ] Correggere difetti di correttezza con regressioni e ripetere le valutazioni interessate, conservando gli esiti precedenti. Pianificare separatamente eventuali ottimizzazioni.
- [ ] Testare generatore, manifest, conversioni, verificatore indipendente e metriche con piccoli esempi calcolati manualmente. Benchmark grandi opt-in, fuori dalla suite ordinaria; preservare la regressione CLI Homework.
- [ ] Aggiornare protocollo dataset e [piano query](QUERY_TEST_PLAN.md); riscrivere la [relazione](REPORT.md) attorno a costruzione del corpus, metriche, risultati, grafici e limiti. Aggiornare lo stato negli indici solo sulla base delle evidenze ottenute.
- [ ] Pubblicare solo aggregati, ID anonimi ed esempi sintetici. Testi, percorsi personali, query reali e giudizi dettagliati restano locali; dichiarare il limite alla riproducibilità esterna del corpus personale.
- [ ] Inserire l'email solo nel PDF di consegna tramite configurazione locale non versionata; chiedere l'indirizzo prima della compilazione finale. Aggiornare le [istruzioni di build](BUILD.md), renderizzare e verificare PDF e dati riportati.

**Completamento ed evidenze:** test pertinenti con esiti e skip dichiarati, relazione coerente con i report, PDF controllato e contatto presente solo nella copia di consegna. I giudizi dell'utente sono approvati in HW3-02; resta necessario il suo indirizzo email per la consegna. Nessuna pubblicazione dei documenti universitari o invio automatico al docente.
