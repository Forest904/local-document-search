# V2-14 — accettazione del candidato 0.2.2

Questo registro distingue la release pubblicata 0.2.1 dal candidato locale 0.2.2. L'11 novembre 2026 l'utente ha confermato il funzionamento dell'installer 0.2.1 scaricato da GitHub su un PC di test. Non sono stati comunicati SHA-256 del file provato, misure né esiti per singolo scenario. Tale conferma non prova il nuovo installer.

| Requisito | Scenario | Esito 0.2.2 | Revisione / artefatto | Limite o azione aperta |
|---|---|---|---|---|
| V2-R01–R19, R20–R28 | T01–T32 applicabili | Backend 437 passed, 7 skipped; frontend/script 139 passed | Sorgente `4263029`, installer 0.2.2 | Sei skip Windows: symlink/nomi filesystem; uno skip corpus reale opt-in. Benchmark e collaudo del pacchetto distinti dalle evidenze storiche |
| V2-R29 | T33 | Cinque dimensioni QML PASS; audit nativo parziale; resize con bozza Markdown PASS sul sorgente | Sorgente `4263029`, installer 0.2.2; test bozza aggiunto dopo la build | DPI 100–200%, tastiera completa e Narrator sul pacchetto pendenti |
| V2-R30 | T34 | Guida F1/Aiuto e onboarding QML PASS; ispezione nativa IT della guida PASS | Sorgente `4263029`, installer 0.2.2 | Collaudo sul pacchetto e F5 da attestare |
| V2-R18 | T18 | Runner Homework 3 PASS (10 query, 2 regressioni) | Sorgente `4263029` | CLI indipendente dalla UI |
| V2-R08 | T08 | **FAIL dei budget:** no-change 1,520 s > 1 s; query p95 172,797 ms > 100 ms | Compilato locale della revisione `4263029`; installer SHA-256 `70b8d0f7a983f4f7dbfad0122f1129d9ad2af1c49b84d3e36b1606867808c4b6` | Runner completo `PASS`, tre cicli, 100 campioni e 5 warmup; report locale `experiments/results/v2-022-compiled/report.json` |
| V2-R15–R17 | T15–T17, T19 | Build pulita e verifica manifest/checksum PASS | Installer `4263029`, SHA-256 come sopra | Install/update/offline/uninstall su account standard isolato pendenti |

Un PASS automatico non sostituisce Narrator o collaudo del pacchetto. Un artefatto senza revisione e hash identificabili non chiude T08/T15–T19. Il corpus funzionale V2-01 e i benchmark V2-02 restano indipendenti.

Massimi degli altri budget T08: build 254,258 s ≤ 300 s; riapertura 12,471 s ≤ 15 s; sync incrementale 5,198 s ≤ 60 s; working set 1.433.071.616 byte ≤ 2.560 MiB. No-change dei cicli 2/3: 0,920/0,959 s; p95 query dei cicli 1/2/3: 122,857/172,797/82,286 ms. Il criterio usa il massimo dei tre cicli, quindi T08 resta aperto. Il report è locale e ignorato da Git; non è una prova sull'installer installato.
