# Corpus di validazione funzionale v2

**Stato al 7 novembre 2026:** generatori, manifest, acquisizione, validatori e ground truth V2-01 implementati. T20 e T21 verificati localmente; [esiti e revisioni](ROADMAP.md#v2-01--corpus-ibrido-e-validazione-funzionale). Questa pagina non è un piano di benchmark.

## Scelte V2-01 implementate

`experiments/v2_corpus.py` riusa gli otto TXT Homework e `pdf_bytes` M9 e aggiunge MD/PDF per 13 documenti sintetici deterministici. Gli undici casi funzionali sono definiti dai testi del generatore, senza copiare l'output del motore. Errori ed esclusioni reader rimangono nelle fixture dedicate. Generazione e confronto avvengono nella suite ordinaria offline.

Il [manifest reale](../experiments/v2_corpus/real_manifest.json) fissa 12 documenti IT/EN: nove Markdown, un TXT e due PDF. Nove file provengono da GitHub Open Source Guides alla revisione Git indicata negli URL, con [licenza CC BY 4.0](https://github.com/github/opensource.guide/blob/e7ac98e94600c5eea834f9a026c000d26b28df24/LICENSE); un Markdown proviene da Italia Writing Toolkit con licenza CC BY 4.0. I PDF provengono da Wikimedia Commons e le rispettive pagine file attestano CC BY-SA 4.0. Il corpus locale è stato acquisito e tutti e 12 i documenti sono stati indicizzati; i file rimangono fuori da Git.

Lo schema JSON `1` usa `files` con `path`, `source`, `url`, `license`, `license_url`, `language`, `format` e `sha256`. `corpus_id` è SHA-256 del manifest JSON canonico (chiavi ordinate, UTF-8, senza spazi superflui). Il file query usa `schema`, `corpus_id` e `queries`, ciascuna con `query`, `field`, `expected` ordinato e `ambiguities`. Il validatore rifiuta versione errata, percorsi sconosciuti e duplicati; la completezza *semantica* delle liste richiede l'esame del testo estratto.

L'acquisitore riusa file in cache solo con hash corretto; un hash differente non viene sovrascritto. Scaricamenti falliti o hash diversi sono segnalati per file e non producono PASS. La suite reale è opt-in con `LDS_V2_REAL_CORPUS`; l'assenza della ground truth dà esito incompleto. La [ground truth reale](../experiments/v2_corpus/real_queries.json), preparata seguendo il [prompt](../experiments/v2_corpus/ASTRA_GROUND_TRUTH_PROMPT.md), contiene 36 query: 10 filename, 18 content e 8 both. Ogni lista è stata ricontrollata sui 12 testi esportati con scansioni sequenziali indipendenti, senza importare il motore o derivare gli attesi dai suoi risultati (432 coppie query/documento per passata). Le note esplicitano l'ordine di estrazione PDF, gli accenti preservati e il divieto di combinare campi in BOTH. Nessun caso selezionato resta indeterminabile rispetto ai testi esportati; non si certifica la fedeltà al layout PDF originale. [Comandi](../experiments/README.md).

## Scopo e componenti

Il corpus ibrido estende i test esistenti con due insiemi identificabili e riproducibili:

- **Sintetico:** file TXT, Markdown e PDF generati deterministicamente, con contenuti e percorsi controllati per analyzer, campo filename/content/BOTH, AND, frasi, Unicode, termini ripetuti, assenze e casi limite. Fixture che causano esclusione o errore reader restano separate dal nucleo ricercabile.
- **Reale:** circa 12–30 file autentici provenienti da Internet, indicizzabili dal reader v1, con italiano e inglese e almeno un TXT, un Markdown e un PDF. La selezione deve privilegiare varietà di struttura e testi autentici senza assumere che i reader conservino il layout originale.

`experiments/run_homework3.py` fornisce otto TXT e query con risultati attesi; `experiments/m9_corpus.py` fornisce il generatore PDF deterministico. V2-01 li riusa senza dipendere dal runner di benchmark M9. I test reader esistenti restano fixture piccole e mirate.

## Provenienza e riproducibilità

Per ogni documento reale, il manifest versionato registra fonte, URL di acquisizione, licenza o permesso di riuso esplicito, lingua, formato, percorso e hash del file acquisito. I file scaricati e gli output generati stanno fuori da Git. Le [scelte V2-01](OPEN_DECISIONS.md) sono documentate sopra.

L'acquisizione verifica hash e completezza e registra file saltati o non disponibili. Un URL cambiato o un hash discordante non aggiorna silenziosamente il manifest. È consentito saltare il file durante l'acquisizione con un esito esplicito; **la validazione reale non è riuscita finché tutti i file approvati non sono presenti e verificati**. Un sottoinsieme non produce un PASS del corpus completo. Nessuna rete è richiesta alla suite sintetica ordinaria o al prodotto.

## Query e ground truth

Ogni query curata dichiara campo e lista completa dei percorsi attesi per una versione precisa del corpus, includendo casi positivi, negativi, AND e frasi. I risultati attesi devono essere stabiliti dai documenti e dal testo estratto secondo i reader/analyzer approvati, mai copiando l'output del motore sotto test.

Dopo acquisizione completa, ChatGPT Astra è lo strumento previsto per preparare query e match. La bozza AI può essere accettata senza revisione umana dei singoli match, ma prima del versionamento controlli automatici devono verificare schema, riferimenti a file esistenti, liste complete rispetto al manifest e associazione esplicita alla versione del corpus. Questi controlli strutturali non dimostrano da soli la correttezza semantica: eventuali ambiguità di estrazione o query vanno esplicitate nei dati attesi e nei limiti della validazione. Un cambio di file, reader o analyzer richiede di riesaminare la ground truth interessata.

## Esecuzione

I sintetici entrano nella suite ordinaria offline. La suite reale è separata e opt-in, dopo download verificato; può essere eseguita in una CI dedicata. Se il corpus è incompleto, la suite reale segnala l'assenza e non passa. Confrontare insiemi completi di percorsi attesi, non soltanto conteggi o esempi positivi. Salvare esiti con revisione del manifest, dei risultati attesi e del codice.

Questo corpus serve a correttezza e integrazione. La [baseline prestazionale V2-02](ROADMAP.md) definirà corpus, hardware, metrica e budget propri: nessuna misura o soglia viene dedotta dai risultati funzionali. [Scenari T20–T21](TEST_STRATEGY.md), [requisito V2-R19](PRD.md).
