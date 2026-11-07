# Corpus di validazione funzionale v2

**Stato:** requisito approvato per V2-01, sistema non implementato e fonti Internet non ancora selezionate. Questa pagina definisce la base di test; non è un piano di benchmark. Il punto di partenza concreto è nella [baseline](BASELINE.md).

## Scopo e componenti

Il corpus ibrido estende i test esistenti con due insiemi identificabili e riproducibili:

- **Sintetico:** file TXT, Markdown e PDF generati deterministicamente, con contenuti e percorsi controllati per analyzer, campo filename/content/BOTH, AND, frasi, Unicode, termini ripetuti, assenze e casi limite. Fixture che causano esclusione o errore reader restano separate dal nucleo ricercabile.
- **Reale:** circa 12–30 file autentici provenienti da Internet, indicizzabili dal reader v1, con italiano e inglese e almeno un TXT, un Markdown e un PDF. La selezione deve privilegiare varietà di struttura e testi autentici senza assumere che i reader conservino il layout originale.

`experiments/run_homework3.py` fornisce otto TXT e query con risultati attesi; `experiments/m9_corpus.py` genera TXT/MD/PDF deterministici con manifest e query, ma nasce anche per misure. In V2-01 si decide come riusarli o integrarli senza fare dipendere la validazione dal runner di benchmark M9. I test reader esistenti restano fixture piccole e mirate.

## Provenienza e riproducibilità

Per ogni documento reale, un manifest versionato deve registrare fonte, URL di acquisizione, licenza o permesso di riuso esplicito, lingua, formato, identificatore/percorso e hash del file acquisito. I file scaricati e gli output generati stanno fuori da Git. Fonti, URL, licenze, schema concreto e procedura di acquisizione sono [decisioni V2-01](OPEN_DECISIONS.md), da approvare prima di costruire il corpus; nessuna fonte è già stata scelta.

L'acquisizione verifica hash e completezza e registra file saltati o non disponibili. Un URL cambiato o un hash discordante non aggiorna silenziosamente il manifest. È consentito saltare il file durante l'acquisizione con un esito esplicito; **la validazione reale non è riuscita finché tutti i file approvati non sono presenti e verificati**. Un sottoinsieme non produce un PASS del corpus completo. Nessuna rete è richiesta alla suite sintetica ordinaria o al prodotto.

## Query e ground truth

Ogni query curata dichiara campo e lista completa dei percorsi attesi per una versione precisa del corpus, includendo casi positivi, negativi, AND e frasi. I risultati attesi devono essere stabiliti dai documenti e dal testo estratto secondo i reader/analyzer approvati, mai copiando l'output del motore sotto test.

Dopo acquisizione completa, ChatGPT Astra è lo strumento previsto per preparare query e match. La bozza AI può essere accettata senza revisione umana dei singoli match, ma prima del versionamento controlli automatici devono verificare schema, riferimenti a file esistenti, liste complete rispetto al manifest e associazione esplicita alla versione del corpus. Questi controlli strutturali non dimostrano da soli la correttezza semantica: eventuali ambiguità di estrazione o query vanno esplicitate nei dati attesi e nei limiti della validazione. Un cambio di file, reader o analyzer richiede di riesaminare la ground truth interessata.

## Esecuzione

I sintetici entrano nella suite ordinaria offline. La suite reale è separata e opt-in, dopo download verificato; può essere eseguita in una CI dedicata. Se il corpus è incompleto, la suite reale segnala l'assenza e non passa. Confrontare insiemi completi di percorsi attesi, non soltanto conteggi o esempi positivi. Salvare esiti con revisione del manifest, dei risultati attesi e del codice.

Questo corpus serve a correttezza e integrazione. La [baseline prestazionale V2-02](ROADMAP.md) definirà corpus, hardware, metrica e budget propri: nessuna misura o soglia viene dedotta dai risultati funzionali. [Scenari T20–T21](TEST_STRATEGY.md), [requisito V2-R19](PRD.md).
