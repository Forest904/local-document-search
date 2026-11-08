# Roadmap v2 — Dallo stato attuale al prodotto Windows

**Stato all'8 novembre 2026:** V2-01…V2-05 sono completate e verificate localmente; V2-06…V2-08 sono progettate. Il backend, la CLI e il desktop Qt Widgets v1 esistono; lo ZIP M9 è stato costruito e collaudato localmente, ma M9 è [parzialmente accettata](BASELINE.md#lacune-da-trasferire-non-prove-superate). Questa roadmap parte dal codice e dalle evidenze attuali, non richiede di ricominciare da zero né considera chiusa M9.

## Come usare questa roadmap

1. Aprire la milestone successiva e verificare nel codice l'**ingresso** indicato; un ADR approvato non prova che una funzione esista.
2. Chiudere le decisioni elencate nel [registro](OPEN_DECISIONS.md) **prima** di implementare la parte che dipende da esse. Le scelte interne ordinarie seguono le convenzioni esistenti.
3. Svolgere le attività nell'ordine logico, aggiornando [PRD](PRD.md), [contratti](INTERFACE_CONTRACTS.md), ADR e scenari se il comportamento approvato cambia. CLI Homework e backend desktop restano condivisi.
4. Chiudere la milestone solo dopo le verifiche di uscita, registrando revisione, comandi, ambiente, risultati e limiti. Test sul sorgente, prova visiva e collaudo del pacchetto sono evidenze differenti.

Il [PRD](PRD.md) assegna gli ID V2-R01…V2-R19; la [strategia di test](TEST_STRATEGY.md) definisce T01…T21. Le specifiche collegate contengono le regole normative senza duplicarle qui. L'archivio [v1](archive/v1/README.md) conserva le motivazioni e le prove M0–M9.

## Sequenza e dipendenze

| Milestone | Ingresso principale | Uscita |
|---|---|---|
| V2-01 — Corpus funzionale | Codice, generatori e test v1 | Corpus ibrido riproducibile e validazione funzionale |
| V2-02 — Baseline prestazionale | V2-01 | Metodo, misure e budget approvati sul target 10.000/300 MB |
| V2-03 — Retrieval | V2-02 | Vocabolario ordinato, prefissi e suggerimenti verificati |
| V2-04 — Storage e lifecycle | V2-02 e interfaccia indice V2-03 | Persistenza, riapertura, sync, cancel e isolamento v1/v2 |
| V2-05 — Ricerca applicativa | V2-03 e V2-04 | Ranking, filtri, snippet e highlighting nei contratti backend |
| V2-06 — Desktop Qt Quick | V2-05 per l'integrazione | Nuova UI, lingue, temi e accessibilità verificati |
| V2-07 — Installer offline | V2-06 per il pacchetto finale | Wizard, dipendenze, aggiornamento, disinstallazione e diritti verificati |
| V2-08 — Accettazione pubblica | V2-01…V2-07 | Pacchetto finale provato su Windows pulito e lacune M9 chiuse |

La progettazione visiva può iniziare dopo V2-02; l'integrazione desktop usa i contratti V2-05. Un prototipo di packaging Qt Quick può iniziare dopo V2-02; V2-07 non attende la fine della UI per scoprire incompatibilità. Il corpus funzionale V2-01 e quello prestazionale V2-02 hanno scopi e criteri distinti.

## V2-01 — Corpus ibrido e validazione funzionale

**Completamento al 7 novembre 2026, revisione di partenza `c1c04abe177847322b36bde7841d549581ff927d` (working tree modificato, non ancora consolidato in un commit):** generatore e query sintetiche, manifest reale con 12 fonti, download/cache con SHA-256, esportazione testo, controlli strutturali e suite opt-in implementati. La [ground truth reale](../experiments/v2_corpus/real_queries.json) contiene 36 query curate sui tre campi, con casi positivi, negativi, AND e frasi. Gli attesi sono stati preparati dai testi esportati e ricontrollati sui 12 documenti mediante scansioni indipendenti dal motore, prima del confronto applicativo. **T20, T21 e V2-01 chiusi localmente**; V2-01 non produce una baseline prestazionale, che è registrata separatamente in V2-02.

**Verifiche locali (Windows, Python 3.12.2, pytest 8.3.5):** `python -m pytest` da `backend/`: 322 passed, 6 skipped; con `LDS_V2_REAL_CORPUS` impostato al percorso assoluto del corpus: 323 passed, 5 skipped. `python experiments/run_homework3.py`: PASS. `python experiments/v2_corpus.py validate-real experiments/results/v2-real`: corpus completo, 12 hash corretti, tutti i documenti indicizzati, 36/36 query PASS. Suite T20/T21 mirata: 6 passed, inclusi riproducibilità dei 13 sintetici e undici query. Report locale: `experiments/results/v2-real-validation.json`; corpus ID `d35d4e54e00102c67a8e3196c4ed8274eb78cfb5bd6f1343aaf7f3bd6d1a82b9`, hash canonico query `0efc95a09628faacd729d0c986120a5786540fde103ce33fa33abb4307f47164`. Corpus, testi e report restano fuori Git. Le note nelle query documentano ordine del testo PDF, accenti e vincoli BOTH; i test strutturali e il confronto col motore non costituiscono da soli una prova semantica indipendente. Resta da registrare la revisione finale dopo il commit.

**Ingresso storico:** `experiments/run_homework3.py` generava otto TXT con query attese; `experiments/m9_corpus.py` generava TXT/MD/PDF e manifest con query; `experiments/run_m9.py` confrontava risultati e misurava prestazioni; esistevano fixture reader. All'avvio di V2-01 non era stato acquisito un corpus Internet. [Stato iniziale](BASELINE.md#materiale-di-test-esistente-da-cui-parte-v2-01).

**Decisioni prima del codice:** V2-D10…V2-D13: fonti e permessi, struttura/versione del manifest, acquisizione e cache, composizione dei sintetici e preparazione della ground truth. Non scegliere URL o schemi definitivi per supposizione; [criteri approvati](TEST_DATASETS.md).

**Attività ordinate**

1. Separare gli scenari funzionali dai tempi del runner M9 e riusare, dove utile, generatori e fixture esistenti. Preparare sintetici deterministici TXT/MD/PDF per analyzer, campi, AND, frasi, Unicode, casi vuoti e negativi controllati; tenere errori/esclusioni reader in fixture distinte dal corpus ricercabile.
2. Selezionare circa 12–30 documenti autentici indicizzabili, con italiano e inglese e almeno un TXT, un MD e un PDF. Verificare per ciascuno fonte e permesso esplicito di riuso; versionare URL, licenza, lingua, formato e hash nel manifest, non i file scaricati.
3. Implementare acquisizione verificabile: URL o hash cambiati non modificano silenziosamente il corpus approvato. Un file può essere saltato con diagnostica, ma la suite reale non può passare finché il manifest non è completo.
4. Sul corpus acquisito preparare query e liste complete dei percorsi attesi, usando ChatGPT Astra come supporto e il testo estratto come evidenza; mai derivare la ground truth dall'output del motore. Verificare automaticamente schema, riferimenti, completezza strutturale e versione del corpus. Registrare le ambiguità che i controlli non risolvono.
5. Integrare sintetici nella suite ordinaria offline e reali in suite opt-in separata, predisposta per CI dedicata. Confrontare insiemi completi, non solo conteggi; conservare revisione di manifest, query e codice nell'esito.

**Verifica e uscita:** T20 e T21 passano con corpus completo; ripetendo la generazione si ottengono gli stessi file/hash; assenza o hash errato di un reale dà esito incompleto/non valido, mai PASS. La CLI Homework e i reader esistenti continuano a passare. Nessuna soglia prestazionale viene dichiarata da questi test.

**Riferimenti:** [Corpus](TEST_DATASETS.md), [test](TEST_STRATEGY.md), [layout](REPOSITORY_LAYOUT.md), [esperimenti attuali](../experiments/README.md).

## V2-02 — Baseline e budget prestazionali

**Completamento al 7 novembre 2026: misure eseguite e budget V2-D01 approvati.**
Il runner e i tre profili sono implementati. Su Windows 11 Home build 26200,
Python 3.12.2, Ryzen AI 7 350, 32 GB RAM e SSD WD SN5000S, il target
10.000 file/300 MB ha completato tre cicli `PASS` dal sorgente della revisione
`9766bb274dfcbd5e8bb0cd865b1fce5a40efe766` con working tree modificato.
Sono stati estratti 299.948.099 byte per ciclo. Build: 433,0–440,1 s;
avvio fino a ricerca: 69,0–70,6 s; sync no-change: 0,425–0,438 s;
sync incrementale 100/100/100: 161,4–162,2 s; peggior query p95:
247,4 ms; picco working set: 4125 MiB. Anche small e adverse hanno tre
cicli `PASS`. La cache OS non è stata svuotata; profilo energetico Balanced,
batteria in carica. Comandi, distribuzioni, spazio storage, profilazione e
limiti sono nella [relazione V2-02](V2_02_BENCHMARK.md); risultati grezzi in
`experiments/results/`, fuori Git. Verifiche: suite backend 327 passed,
6 skipped; Homework PASS; T08 mirata 5 passed. Metodo e budget approvati sono
nell'[ADR 0014](adr/0014-v2-performance-budgets.md), **Accepted**. **V2-02 è
chiusa localmente**; il backend v1 misurato supera vari budget, che restano
criteri di uscita per V2-03/V2-04/V2-08. La revisione finale del working tree
va registrata dopo il commit; nessuna prova sul pacchetto è attribuita a V2-02.

**Ingresso:** V2-01 chiusa; misure M9 disponibili solo come storia, con corpus ristretto e limiti documentati. Il target v2 è 10.000 file e 300 MB di testo estratto.

**Decisione prima delle ottimizzazioni:** V2-D01 approva corpus **prestazionale** separato, hardware, metodo, condizioni di cache e budget numerici per query p95, avvio, build iniziale, sync incrementale/no-change e picco RAM. Non usare la ground truth funzionale come benchmark implicito.

**Attività ordinate**

1. Preparare un carico riproducibile e un ambiente descritto con versioni, seed, formati, query, dimensioni e stato della cache.
2. Misurare lo stato attuale, distinguendo dove possibile lookup, intersezione, ordinamento, caricamento, estrazione, costruzione e serializzazione. Registrare distribuzioni, memoria e limiti del metodo, senza confronti impropri con M9.
3. Identificare i costi dominanti e approvare soglie da usare come criteri delle milestone V2-03/V2-04/V2-08. Documentare rischi e regressioni accettabili.

**Verifica e uscita:** runner ripetibile, risultati grezzi fuori Git, relazione con ambiente e budget approvati. V2-02 misura e decide: non dichiara raggiunti i budget dal codice v1.

**Riferimenti:** [PRD V2-R08](PRD.md), [test T08](TEST_STRATEGY.md), [misure storiche](archive/v1/M9_VERIFICATION.md).

## V2-03 — Retrieval e vocabolario ordinato

**Chiusura locale al 7 novembre 2026, revisione di partenza `fa9f73eb72f17509a6bbfa401f58abc0ac35895c` (working tree modificato):** vocabolari ordinati per campo e snapshot, prefissi espliciti e suggerimenti applicativi implementati. V2-D02 e V2-D03 sono risolte nell'[ADR 0010](adr/0010-v2-retrieval.md) dopo il [confronto misurato](V2_03_RETRIEVAL.md). CLI Homework invariata. Backend: 351 passed, 6 skipped; corpus reale opt-in mirato: 6 passed; Homework PASS. Il runner target 10.000 file/299.948.099 byte ha completato tre cicli `PASS`: massimo query p95 36,5 ms entro il budget 100 ms; no-change massimo 0,764 s entro 1 s. Build 729–742 s, avvio circa 110 s, sync incrementale 257–264 s e RAM 4127 MiB sono fuori budget e restano a V2-04/V2-08. Comandi, ambiente, risultati e limiti sono nella [relazione V2-03](V2_03_RETRIEVAL.md); grezzi fuori Git. **V2-03 chiusa localmente per il retrieval**, senza attribuire prove del pacchetto a questa milestone. La revisione finale va registrata dopo il commit.

**Ingresso storico:** budget V2-02; due indici posizionali e lookup esatto su dizionario implementati in v1. La struttura secondaria era obbligatoria, con rappresentazione allora aperta.

**Decisioni chiuse:** V2-D02 struttura, memoria, persistenza e coerenza per campo; V2-D03 sintassi/limiti dei prefissi e comportamento dei suggerimenti. Il confronto include albero bilanciato, scansione del dizionario e tupla ordinata: un BST non è assunto più rapido del dizionario per lookup esatto.

**Attività ordinate**

1. Profilare e confrontare le strutture sul carico V2-02: lookup esatto, intervalli per prefisso, build, RAM e riapertura. Fissare una scelta motivata.
2. Costruire il vocabolario ordinato per filename e content nello stesso ciclo dello snapshot e validarne la coerenza con i due indici primari; preservare snapshot immutabili e single-writer.
3. Implementare prefissi solo espliciti e suggerimenti come operazione distinta dalla query; mantenere analyzer coerenti, AND/frasi nello stesso campo e nessuna espansione implicita della ricerca esatta.
4. Verificare aggiornamento, restart, recovery e regressioni della CLI Homework senza Qt o cambi di ordinamento.

**Verifica e uscita:** T03–T05 e T18; risultati delle query v1 invariati, vocabolario coerente in ogni snapshot e costi confrontati con i budget pertinenti. Nessun motore IR esterno.

**Riferimenti:** [analisi](INDEXING_AND_ANALYSIS.md), [dominio](DOMAIN_MODEL.md), [ADR 0010](adr/0010-v2-retrieval.md), [contratti](INTERFACE_CONTRACTS.md).

## V2-04 — Storage e lifecycle

**Chiusura locale all'8 novembre 2026, revisione di partenza `7047752ee70e90dbbe4af3db82b180f5209e9e70` (working tree modificato):** storage SQLite v2 separato, versioni immutabili per documento, posting compressi e riuso degli invariati; cancel cooperativo, controllo metadati durante ingestione, rebuild e recovery espliciti. Backend: 370 passed, 6 skipped; corpus reale opt-in: 6 passed; Homework PASS. Small, adverse e target hanno tre cicli `PASS`. Sul target 10.000 file/299.948.099 byte, i massimi sono: build **143,8 s**, avvio fino alla ricerca **8,24 s**, sync incrementale **9,37 s**, no-change **0,472 s**, query p95 **22,6 ms**, RAM campionata sull'albero dei processi **1353 MiB**: tutti entro i budget V2-D01. [Metodo, prove e limiti](V2_04_STORAGE.md). **V2-04 e V2-D04 chiuse localmente**; la revisione finale va registrata dopo il commit. I test frontend non sono stati raccolti in questo ambiente privo di PySide6; il collaudo del pacchetto resta V2-08.

**Ingresso:** V2-02 e interfaccia dello snapshot/vocabolario V2-03; v1 possiede persistenza SQLite, sync, lock e job concorrenti. M9 segnala costi di riapertura/sync e prove sul pacchetto ancora mancanti.

**Decisione prima della persistenza:** V2-D04 su layout fisico, versione, retention e recovery v2. Conservare gli invarianti; non importare automaticamente gli indici v1 né leggere/pulire il loro storage.

**Attività ordinate**

1. Implementare storage v2 separato per account e la strategia fisica approvata, collegando il vocabolario agli stessi snapshot di manifest, catalogo e posting. Commit e attivazione restano atomici; versioni incompatibili non diventano ricercabili.
2. Ridurre costi di riapertura, RAM e sync rispetto alla baseline V2-02, verificando no-change, add/modify/remove, rebuild, retention e recovery. Una directory alla volta, diff path+size+mtime_ns.
3. Aggiungere annullamento cooperativo prima del commit: stato CANCELLED distinto da FAILED, candidato scartato e precedente ricercabile. Rifiutare cancel dopo l'inizio del commit non interrompibile.
4. Controllare i metadati durante ingestione; variazione osservata fallisce il candidato e consente retry. Non aggiungere hash dei sorgenti né controlli filesystem durante le query.
5. Coprire cambio directory, pulizia durante job e matrice reader che M9 non ha documentato sul pacchetto corrente; la conferma finale sul prodotto installato resta V2-08.

**Verifica e uscita:** T02, T04 e T08–T11/T14; fault injection e restart producono solo snapshot completi; dati v1 e sorgenti intatti; tempi/memoria nel budget approvato o scostamenti esplicitamente risolti. Le modifiche con size+mtime invariati restano un limite dichiarato.

**Riferimenti:** [snapshot](SNAPSHOTS_AND_SYNC.md), [contratti](INTERFACE_CONTRACTS.md), [ADR 0012](adr/0012-v2-lifecycle-storage.md), [debito M9](BASELINE.md).

## V2-05 — Ricerca applicativa e contratti

**Chiusura locale all'8 novembre 2026, revisione di partenza `b91e2a33ff2de8faf08f4dcadb7314f92576fb83` (working tree modificato):** filtri formato/cartella, ranking su posting, snippet e highlighting Unicode dal testo acquisito, ricerca e anteprima vincolate allo snapshot. V2-D05 e V2-D06 sono risolte nell'[ADR 0010](adr/0010-v2-retrieval.md). Suite backend: 380 passed, 6 skipped; corpus reale opt-in mirato: 6 passed; Homework PASS. Probe prestazionale small (100 file, 299.521 byte estratti, un ciclo, 10 campioni/query, 2 warm-up): `PASS`, peggior p95 query 18,7 ms. Comando: `python experiments/run_v2_benchmark.py run experiments/results/v2-small experiments/results/v2-05-small-probe-fast --cycles 1 --samples 10 --warmups 2`; report locale fuori Git. Il probe non dimostra il budget target 10.000/300 MB né il collaudo del pacchetto. **V2-05 chiusa localmente** per T05–T07/T18 backend; UI e pacchetto restano V2-06/V2-08. La revisione finale va registrata dopo il commit.

**Ingresso:** motore V2-03 e storage/lifecycle V2-04; `SearchDocuments`, `GetDocument` e DTO v1 sono la base, la CLI conserva i suoi default.

**Decisioni prima dell'API definitiva:** V2-D05 formula e spareggi della rilevanza; V2-D06 finestre snippet e corrispondenze nel testo Unicode. Fissare esempi attesi prima del codice.

**Attività ordinate**

1. Estendere i casi d'uso con filtri formato/cartella e scelta ordine: rilevanza predefinita desktop, percorso alternativo. Filtrare e ordinare i match senza allargare la semantica AND/frasi/BOTH; totale e pagine appartengono allo stesso snapshot.
2. Produrre snippet ed evidenziazione dal testo estratto persistito della versione acquisita; dettagli e anteprima mantengono lo `snapshot_id`. Nessuna rilettura dei sorgenti, coordinate PDF o promessa di layout originale.
3. Definire DTO/errori logici per suggerimenti, filtri, ordine e anteprima nei [contratti](INTERFACE_CONTRACTS.md), integrando lo stato e il cancel introdotti in V2-04; collegare il backend senza import di Qt nell'application.
4. Eseguire regressioni su query esatte, paginazione/versione e CLI Homework, preservando sintassi, ordine per percorso e codici esistenti.

**Verifica e uscita:** T05–T07 e T18; ranking deterministico sui soli match, liste attese e highlighting verificati con fixture sintetiche e corpus reale dove pertinente. Ogni cambio di versione o query non mescola risultati.

**Riferimenti:** [contratti](INTERFACE_CONTRACTS.md), [analisi](INDEXING_AND_ANALYSIS.md), [ADR 0010](adr/0010-v2-retrieval.md), [test](TEST_STRATEGY.md).

## V2-06 — Desktop Qt Quick

**Ingresso:** contratti backend V2-05; desktop v1 Qt Widgets esistente. Il design può essere esplorato dopo V2-02, ma non si dichiara integrato prima dei contratti.

**Attività ordinate**

1. Progettare e realizzare la presentazione PySide6/Qt Quick con QML nello stesso processo: sidebar essenziale, ricerca centrale, risultati con snippet, anteprima, stati vuoti ed errori. L'app ChatGPT è riferimento di qualità visiva, non un requisito di chat o AI.
2. Collegare ricerca con Invio, suggerimenti durante digitazione, campo, filtri, rilevanza/percorso, paginazione e apertura file ai casi d'uso; evitare lavoro pesante nel thread grafico e scartare risposte obsolete.
3. Collegare sync, progresso, diagnostiche, cancel e retry. La UI indica quando usa lo snapshot precedente e non mostra risultati della directory errata.
4. Completare italiano/inglese, temi chiaro/scuro e preferenze persistenti separate dagli indici. Verificare tastiera, focus, contrasto, DPI e Narrator sui flussi principali.
5. Provare anticipatamente il runtime QML nel packaging, senza confondere il prototipo con l'installer finale.

**Verifica e uscita:** T05, T07, T10, T12–T13; test Qt e controllo visivo/accessibile su Windows, con ricerca e anteprima sotto carico. Registrare errori e limiti osservati; la prova sul pacchetto installato si ripete in V2-08.

**Riferimenti:** [UX](UX_WINDOWS.md), [contratti](INTERFACE_CONTRACTS.md), [ADR 0011](adr/0011-v2-desktop.md), [frontend attuale](../frontend/README.md).

## V2-07 — Installer offline e distribuzione

**Ingresso:** desktop V2-06 e prova preliminare del packaging QML; ZIP v1 disponibile solo come riferimento storico. La release pubblica richiede termini e diritti verificati.

**Decisioni prima della build finale:** V2-D07 strumento/formato, upgrade e wizard; V2-D08 termini d'uso; V2-D09 componenti Qt e obblighi LGPL del payload.

**Attività ordinate**

1. Preparare installer Windows 11 x64 per utente senza elevazione, con wizard e tutte le dipendenze software necessarie incluse: Python, Qt, plugin QML e runtime. Nessun servizio di download all'installazione o updater online.
2. Definire aggiornamento tramite installer completo e disinstallazione: preservare dati v2 per default, cancellarli solo su scelta esplicita; non toccare sorgenti o storage v1.
3. Inventariare i componenti effettivamente distribuiti e verificarne licenze, avvisi e sostituibilità delle librerie Qt secondo il percorso LGPL. Approvare i termini del progetto: diritti riservati, uso personale/studio gratuito, uso professionale soggetto ad autorizzazione.
4. Bloccare input e procedura di build, produrre manifest/hash e verificare installazione, update, uninstall e avvio offline su account standard di prova. Una prima release non firmata è ammessa; registrare gli avvisi Windows realmente osservati.

**Verifica e uscita:** T01, T14–T17; payload completo e tracciabile, nessuna elevazione/rete o Python preinstallato richiesti. Le prove su Windows pulito e il pacchetto finale identificato restano il gate V2-08.

**Riferimenti:** [privacy e diritti](SECURITY_AND_PRIVACY.md), [ADR 0013](adr/0013-v2-distribution.md), [packaging v1](../scripts/package/README.md), [test](TEST_STRATEGY.md).

## V2-08 — Accettazione della release pubblica

**Ingresso:** V2-01…V2-07 chiuse; installer finale da una revisione pulita, termini approvati e inventario dipendenze verificato. M9 v1 rimane storicamente parziale: questa milestone chiude sul prodotto v2 le [lacune trasferite](BASELINE.md#lacune-da-trasferire-non-prove-superate), non riscrive gli esiti v1.

**Attività ordinate**

1. Fissare revisione, toolchain e artefatto; verificare manifest, hash, licenze e CI della stessa revisione. Non usare un ZIP costruito da working tree modificato come prova della release.
2. Installare e usare offline su Windows 11 x64 pulito, senza Python/tool di sviluppo e con account standard distinto. Ripetere installazione, upgrade, avvio, disinstallazione e conservazione/cancellazione opzionale dei dati.
3. Sul pacchetto finale provare TXT/MD/PDF (anche protetto, senza testo e misto), TXT/MD vuoti, cambio directory/rebuild, pulizia rifiutata durante job, errori con snapshot precedente, doppia istanza e recovery.
4. Verificare ricerca, suggerimenti, filtri, ranking, snippet e anteprima durante carico; misurare rispetto ai budget V2-02 sul metodo approvato. Ripetere accessibilità, lingua, tema e regressioni CLI Homework.
5. Registrare esiti, ambiente, limiti, scostamenti e correzioni con collegamento alla revisione e all'installer effettivamente distribuito. Non segnare PASS per prove saltate o corpus reale incompleto.

**Verifica e uscita:** T01–T21 applicabili con evidenze, comprese M9-G01…G07; nessun candidato parziale; documenti personali e dati v1 intatti nelle prove sul pacchetto. La release è pronta solo quando i criteri pubblici e legali sono soddisfatti; nessuna data o soglia inventata.

**Riferimenti:** [baseline](BASELINE.md), [strategia di test](TEST_STRATEGY.md), [PRD](PRD.md), [privacy](SECURITY_AND_PRIVACY.md).
