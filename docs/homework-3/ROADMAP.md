# Homework 3 — Roadmap di valutazione e relazione

**Stato: HW3-01 conclusa; HW3-02–04 approvate e da eseguire.** La mail del docente richiede di esplicitare costruzione del dataset e metriche, raccomanda più documenti per valutare tempi e recall e chiede l'indirizzo email nella relazione. Le evidenze di HW3-01 sono nel protocollo collegato; nessun invio del report è attestato.

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

- [ ] Preservare le dieci query storiche e le due regressioni. Preparare 30 query per ciascun nuovo corpus: 10 nome, 15 contenuto, 5 entrambi; termini, AND, frasi, assenze e selettività diverse. Fissare query e attesi prima di osservare i risultati del motore.
- [ ] Implementare un verificatore a scansione indipendente, senza riusare analyzer, parser o evaluator del prodotto. Applicare le regole documentate e confrontare insiemi completi, non conteggi o prime pagine.
- [ ] Riportare TP, FP, FN, precision, recall e F1 per query, aggregati micro/macro e percentuale di insiemi esattamente corretti. Denominatori nulli producono `N/A`, con numero di casi validi dichiarato; per query senza attesi controllare esplicitamente i falsi positivi.
- [ ] Selezionare 60 documenti reali stratificati per materia, formato originale e lunghezza. Definire 10 bisogni informativi, ciascuno con criterio binario di rilevanza e query iniziale.
- [ ] Preparare tutti i 600 giudizi documento-bisogno e sottoporli alla revisione finale dell'utente senza mostrare i risultati del motore. Risolvere gli ambigui prima di congelare i giudizi.
- [ ] Valutare la rilevanza su un indice dei soli 60 documenti: la recall tematica si riferisce a questo sottoinsieme, non a tutta `Uni`. Non usare metriche di ranking per la CLI ordinata per percorso.

**Completamento ed evidenze:** query e giudizi versionati localmente con identità del corpus, confronti completi senza differenze lessicali inattese, tabelle metriche e diagnosi degli errori. La qualità tematica si riporta anche se imperfetta: distinguere limiti delle query, analyzer ed estrazione. Correttezza sul TXT convertito non dimostra fedeltà dell'estrazione al sorgente.

## HW3-03 — Prestazioni e scalabilità

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

**Completamento ed evidenze:** test pertinenti con esiti e skip dichiarati, relazione coerente con i report, PDF controllato e contatto presente solo nella copia di consegna. Restano necessari i giudizi dell'utente e il suo indirizzo email. Nessuna pubblicazione dei documenti universitari o invio automatico al docente.
