# ADR 0014 — Metodo e budget prestazionali v2

- **Stato:** Accepted, 2026-11-07; budget V2-D01 approvati dall'utente dopo tre cicli target `PASS`.
- **Contesto:** il target V2-R08 è 10.000 file e 300 MB di testo estratto. Le misure M9 hanno scala e metodo diversi. V2-01 valida la correttezza, non le prestazioni.
- **Decisione:** usare il corpus sintetico V2-02 TXT/MD/PDF e il PC Ryzen AI 7 350 / 32 GB / SSD come riferimento. Tre cicli con storage separato e processi nuovi; cache OS non svuotata; query con cinque warm-up, cento campioni e p95 nearest-rank. Accettare solo report `PASS` con volume estratto entro ±1%.
- **Budget approvati:** massimo query p95 ≤100 ms; avvio fino alla ricerca ≤15 s; build ≤300 s; sync incrementale 100/100/100 ≤60 s; no-change ≤1 s; picco working set ≤2560 MiB. Usare il massimo dei tre cicli e, per le query, il massimo dei p95 di tutti i casi.
- **Conseguenze:** V2-03 e V2-04 misurano gli interventi rispetto alla [baseline](../V2_02_BENCHMARK.md); V2-08 ripete la verifica sul pacchetto. Un risultato fuori budget richiede correzione o decisione esplicita, non viene convertito in PASS. I valori non sono limiti automatici dell'applicazione e non promettono cache fredda, PDF arbitrari o assenza di OOM.
- **Verifica:** [relazione V2-02](../V2_02_BENCHMARK.md) e T08. Il backend v1 misurato supera vari budget; sono criteri per le milestone successive, non esiti di accettazione già ottenuti.
