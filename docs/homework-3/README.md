# Homework 3 — Materiale di consegna

1. [ASSIGNMENT_ALIGNMENT.md](ASSIGNMENT_ALIGNMENT.md): requisiti derivati dalle slide del compito, perimetro minimo vs estensioni.
2. [QUERY_TEST_PLAN.md](QUERY_TEST_PLAN.md): matrice di ~10 prove, da adattare al corpus reale.
3. [REPORT.md](REPORT.md): relazione riscritta il 12 novembre 2026, dieci pagine illustrate; requisiti Homework, motore, query eseguite ed evoluzione fino al candidato Luma 0.2.2, con evidenze e limiti separati.
4. [BUILD.md](BUILD.md): generazione del PDF e delle figure, controllo visivo e aggiornamento delle misure.
5. [ROADMAP.md](ROADMAP.md): HW3-01 e HW3-02 concluse; confronto indice-scansione e revisione della relazione restano attività HW3-03–04.
6. [HW3_02_EVALUATION.md](HW3_02_EVALUATION.md): strumenti, corpus/query congelati, campione, giudizi approvati, metriche e limiti.

La CLI TXT, il doppio indice e la valutazione con dieci query sono documentati nella [relazione compilata](REPORT.md). Questo non dimostra l'invio amministrativo al docente.

## HW3-01

**Milestone conclusa.** Il [protocollo corpus](HW3_01_CORPUS.md) registra `real-002` verificato e accettato, sintetici originali `-003` verificati e annidati, 25 test mirati passati, backend 464 passati/7 skip e CLI con dieci query e due regressioni superate. La revisione rappresentativa dell’agente su 376 PDF e 1.105 pagine resta distinta dall’accettazione dell’utente. Nessuna metrica HW3-02/03 anticipata. I dati personali e i manifest rimangono locali in `experiments/results/homework3/`.

## HW3-02

**Milestone conclusa.** Correttezza lessicale verificata sui quattro corpus:
120/120 confronti esatti, nessuna divergenza irrisolta. I 600 giudizi sui 60 documenti sono stati
approvati dall'utente prima delle ricerche. Rilevanza micro: precision 0,5769,
recall 0,4918, F1 0,5310; recall limitata al campione e revisione visuale PDF
rappresentativa. Test mirati 24 passati, backend 488 passati/7 skip, CLI 10+2 PASS.
Il [protocollo](HW3_02_EVALUATION.md) distingue risultati, approvazioni e limiti.
