# Homework 3 — Materiale di consegna

1. [ASSIGNMENT_ALIGNMENT.md](ASSIGNMENT_ALIGNMENT.md): requisiti derivati dalle slide del compito, perimetro minimo vs estensioni.
2. [QUERY_TEST_PLAN.md](QUERY_TEST_PLAN.md): matrice storica di dieci prove e due regressioni, distinta dalle valutazioni ampliate.
3. [REPORT.md](REPORT.md): relazione del 13 novembre 2026, 15 pagine, sei tabelle e otto figure: dataset, ground truth, metriche e risultati, con tre pagine su Luma.
4. [BUILD.md](BUILD.md): generazione del PDF e delle figure, controllo visivo e aggiornamento delle misure.
5. [ROADMAP.md](ROADMAP.md): HW3-01, HW3-02 e pilot ridotto HW3-03 conclusi; HW3-04 conclusa, campagna estesa rinviata.
6. [HW3_02_EVALUATION.md](HW3_02_EVALUATION.md): strumenti, corpus/query congelati, campione, giudizi approvati, metriche e limiti.
7. [HW3_03_PERFORMANCE.md](HW3_03_PERFORMANCE.md): pilot su 100 TXT, misure separate, confronto indice/scansione e limiti.

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

## HW3-03

**Pilot ridotto concluso:** 100 TXT, build 1,910427 s, run 138,388906 s,
240/240 confronti esatti, nessun timeout. Test mirati 29 passati, CLI 10+2 PASS.
[Misure e limiti](HW3_03_PERFORMANCE.md): un corpus e un processo non attestano
scalabilità; campagna estesa rinviata. La successiva HW3-04 è conclusa.

## HW3-04

**Conclusa:** sorgente e PDF di consegna verificati, contatto presente solo nella copia finale e nei metadati locali. Metriche e grafici riconciliati, tutte le 15 pagine ispezionate. Backend **493 passed, 7 skipped**, inclusi 54 test Homework senza skip; CLI **10+2 PASS**. [Registro di chiusura](HW3_04_REPORT.md). Nessun invio al docente attestato.
