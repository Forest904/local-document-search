# Linee guida per gli agenti

## Metodo e scope
- Comunica in italiano, con risposte concise e motivazioni delle scelte non ovvie.
- Implementa solo quanto richiesto: niente refactoring estranei, framework preventivi o funzionalità future anticipate.
- Salvo diversa richiesta, privilegia la CLI TXT e i requisiti Homework 3 (`docs/homework-3/ASSIGNMENT_ALIGNMENT.md`); le estensioni e la UI Windows non devono bloccarli.
- Verifica lo stato nel codice: specifiche e ADR accettati non dimostrano che una funzionalità sia implementata.
- Leggi solo la documentazione pertinente: `docs/PRD.md` e `docs/ROADMAP.md` per scope/priorità; `docs/REPOSITORY_LAYOUT.md` per ownership; `docs/INTERFACE_CONTRACTS.md` per casi d'uso e porte. Approfondisci le specifiche di ricerca o sync quando coinvolte.
- Consulta `docs/OPEN_DECISIONS.md` e gli ADR pertinenti prima di colmare un dettaglio non definito. Non riaprire implicitamente decisioni approvate; segnala contraddizioni tra richiesta, codice e specifiche.
- Se manca una scelta che cambia requisiti, comportamento pubblico, contratti o dipendenze, proponi un'opzione motivata e chiedi all'utente; prosegui sulle parti indipendenti. Decidi autonomamente i dettagli interni coerenti con le specifiche.

## Architettura
- Python >=3.12; rispetta `.editorconfig` e le convenzioni esistenti.
- `domain`: logica pura, senza I/O; dipendenze solo da standard library e dominio.
- `application`: casi d'uso, DTO e porte; nessun import di adapter concreti o GUI.
- `infrastructure`: filesystem, reader e persistenza tramite le porte; `interfaces`: CLI e composizione. La futura UI usa i contratti applicativi.
- Mantieni CLI e UI sullo stesso backend. Introduci astrazioni solo per confini reali, senza un generico `shared/` o porte per ogni classe.

## Invarianti da preservare
- Elaborazione locale; una directory ricorsiva attiva, un file = un documento; niente symlink/junction, OCR o watcher continuo.
- Due indici invertiti posizionali interni (`filename`, `content`), senza motori IR esterni. Query e indicizzazione usano analyzer coerenti; AND e frasi devono essere soddisfatti interamente nello stesso campo anche in modalità BOTH.
- Snapshot immutabili, attivazione atomica e single-writer. Durante sync si cerca sul precedente snapshot della stessa directory; un errore non pubblica risultati parziali.
- Diff incrementale solo con path, size e `mtime_ns`: non aggiungere hash o controlli sui sorgenti durante la ricerca per correggere limiti accettati.
- Mantieni distinti esclusioni ed errori dei reader secondo i contratti. Corpus personali, snapshot e testo estratto restano fuori da Git; usa fixture sintetiche.

## Verifica e documentazione
- Per logica nuova o corretta, aggiungi test pertinenti a comportamento, invarianti e regressioni secondo `docs/TEST_STRATEGY.md`; evita test che replicano l'implementazione.
- Da `backend/`: installazione sviluppo `python -m pip install -e ".[dev]"`; test `python -m pytest`. Esegui i test pertinenti e riporta esito e limiti; nessun test raccolto non equivale a suite verde.
- Quando risolvi una decisione di progetto, aggiorna ADR, `docs/OPEN_DECISIONS.md`, specifiche coinvolte e test corrispondenti. Non creare ADR per dettagli interni ordinari.
- Aggiorna la documentazione quando cambia il comportamento; non inventare benchmark o funzionalità completate. Nel riepilogo indica cosa cambia, verifiche eseguite ed eventuali punti aperti.
