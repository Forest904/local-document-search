# ADR 0014 — Metodo e budget prestazionali v2

- **Stato:** Accepted, 2026-11-07; budget V2-D01 approvati dall'utente dopo tre cicli target `PASS`.
- **Contesto:** il target V2-R08 è 10.000 file e 300 MB di testo estratto. Le misure M9 hanno scala e metodo diversi. V2-01 valida la correttezza, non le prestazioni.
- **Decisione:** usare il corpus sintetico V2-02 TXT/MD/PDF e il PC Ryzen AI 7 350 / 32 GB / SSD come riferimento. Tre cicli con storage separato e processi nuovi; cache OS non svuotata; query con cinque warm-up, cento campioni e p95 nearest-rank. Accettare solo report `PASS` con volume estratto entro ±1%.
- **Budget approvati originari (storici):** massimo query p95 ≤100 ms; avvio fino alla ricerca ≤15 s; build ≤300 s; sync incrementale 100/100/100 ≤60 s; no-change ≤1 s; picco working set ≤2560 MiB. Usare il massimo dei tre cicli e, per le query, il massimo dei p95 di tutti i casi. La revisione vigente è sotto.
- **Conseguenze:** V2-03 e V2-04 misurano gli interventi rispetto alla [baseline](../PERFORMANCE.md#v2-02); V2-08 ripete la verifica sul pacchetto. Un risultato fuori budget richiede correzione o decisione esplicita, non viene convertito in PASS. I valori non sono limiti automatici dell'applicazione e non promettono cache fredda, PDF arbitrari o assenza di OOM.
- **Verifica:** [relazione V2-02](../PERFORMANCE.md#v2-02) e T08. Il backend v1 misurato supera vari budget; sono criteri per le milestone successive, non esiti di accettazione già ottenuti.

## Revisione approvata il 12 novembre 2026

Prima delle nuove prove comparative 0.2.1/0.2.2, sono approvati p95 ≤100 ms per query esatte, wildcard ordinarie e suggerimenti; p95 ≤200 ms per il solo caso `frasecom*` nel contenuto; no-change ≤2 s. Restano invariati build ≤300 s, riapertura ≤15 s, sync incrementale ≤60 s e working set ≤2560 MiB. Il gate usa il massimo di tre cicli e il massimo dei p95 per gruppo. I limiti precedenti, 100 ms per tutte le query e 1 s per no-change, e i rispettivi risultati rimangono evidenza storica.

L'accettazione prestazionale può chiudersi con un rallentamento rispetto alla 0.2.1 ancora senza causa accertata, se il confronto è completo e documentato, il candidato finale è identificato e tutti i nuovi budget sono rispettati. Questa è accettazione esplicita del rallentamento entro le soglie, con indagine futura non bloccante.
