# Corpus di validazione funzionale v2

V2-01 verifica la correttezza, separatamente dal [benchmark prestazionale](PERFORMANCE.md). [Comandi di acquisizione e test](../experiments/README.md#v2-01-corpus-funzionale).

## Sintetici e reali

`experiments/v2_corpus.py` riusa gli otto TXT Homework e `pdf_bytes` M9, aggiungendo MD/PDF: **13 sintetici deterministici e 11 query**, definiti dai testi del generatore senza copiare risultati del motore. Coprono analyzer, filename/content/BOTH, AND, frasi, Unicode, ripetizioni, assenze e casi limite; errori/esclusioni reader restano nelle fixture separate. La generazione ripetuta deve produrre gli stessi hash.

Il [manifest reale](../experiments/v2_corpus/real_manifest.json) fissa **12 documenti IT/EN: nove Markdown, un TXT e due PDF**. Nove file provengono da GitHub Open Source Guides a revisione fissata, un Markdown da Italia Writing Toolkit (entrambi CC BY 4.0); le pagine Wikimedia dei PDF attestano CC BY-SA 4.0. URL, licenze e hash puntuali sono nel manifest. Il criterio di selezione è circa 12–30 testi autentici autorizzati, almeno un file per formato, con strutture diverse e indicizzabili dai reader.

Lo schema JSON `1` registra `files` con `path`, `source`, `url`, `license`, `license_url`, `language`, `format`, `sha256`. `corpus_id` è SHA-256 del manifest JSON canonico (chiavi ordinate, UTF-8, senza spazi superflui). Manifest e query sono versionati; download, testo estratto e report restano fuori Git.

## Acquisizione e ground truth

L’acquisitore riusa la cache solo con hash corretto e non sovrascrive hash discordanti. File saltati, download falliti o fonti cambiate sono segnalati; non aggiornano silenziosamente il manifest. La validazione reale non può dare PASS finché il corpus approvato non è completo. La suite ordinaria e il prodotto non richiedono rete.

Il file query contiene `schema`, `corpus_id`, `queries`, ciascuna con `query`, `field`, lista completa `expected` ordinata e `ambiguities`. Il validatore rifiuta versioni errate, riferimenti sconosciuti e duplicati. Gli attesi si ricavano da documenti e testo canonico, mai dall’output del motore.

ChatGPT Astra è previsto come supporto dopo l’acquisizione. La bozza può essere accettata senza revisione umana di ogni match, ma richiede controlli automatici di schema, riferimenti, completezza strutturale e versione. Questi non provano la correttezza semantica: esplicitare ambiguità; riesaminare gli attesi se cambiano file, reader o analyzer.

La [ground truth reale](../experiments/v2_corpus/real_queries.json) contiene **36 query**: 10 filename, 18 content, 8 both, con positivi, negativi, AND e frasi. È stata ricontrollata sui 12 testi con scansioni indipendenti dal motore (432 coppie per passata). Note su ordine PDF, accenti e vincoli BOTH; nessun caso selezionato indeterminabile rispetto al testo estratto, senza certificare fedeltà al layout originale.

T20 entra nella suite offline; T21 è opt-in tramite `LDS_V2_REAL_CORPUS` assoluto, predisponibile in CI dedicata. Confrontare insiemi completi, non conteggi. Corpus o ground truth mancanti non sono PASS. Registrare revisione manifest/query/codice e stato del working tree.

## Verifica V2-01

7 novembre 2026, base `c1c04abe177847322b36bde7841d549581ff927d` con working tree modificato; Windows, Python 3.12.2, pytest 8.3.5. Backend ordinario: **322 passed, 6 skipped**; con corpus completo: **323 passed, 5 skipped**; T20/T21 mirati: **6 passed**; Homework **PASS**.

`python experiments/v2_corpus.py validate-real experiments/results/v2-real`: 12 hash corretti, tutti i documenti indicizzati, **36/36 query PASS**. Report locale `experiments/results/v2-real-validation.json`; corpus ID `d35d4e54e00102c67a8e3196c4ed8274eb78cfb5bd6f1343aaf7f3bd6d1a82b9`, hash canonico query `0efc95a09628faacd729d0c986120a5786540fde103ce33fa33abb4307f47164`. T20/T21 chiusi localmente; il record identifica la base con modifiche, non una revisione finale consolidata. Nessuna misura prestazionale deriva da questa verifica.
