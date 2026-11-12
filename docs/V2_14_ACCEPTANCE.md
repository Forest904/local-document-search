# V2-14 — accettazione del candidato 0.2.2

Questo registro distingue la release pubblicata 0.2.1 dal candidato locale 0.2.2. L'11 novembre 2026 l'utente ha confermato il funzionamento dell'installer 0.2.1 scaricato da GitHub su un PC di test. Non sono stati comunicati SHA-256 del file provato, misure né esiti per singolo scenario. Tale conferma non prova il nuovo installer.

| Requisito | Scenario | Esito 0.2.2 | Revisione / artefatto | Limite o azione aperta |
|---|---|---|---|---|
| V2-R01–R19, R20–R28 | T01–T32 applicabili | Backend 439 passed, 7 skipped; frontend/script 138 passed, 1 deselected | Sorgente candidato `800ff756`, installer 0.2.2 | Sei skip Windows: symlink/nomi filesystem; uno skip corpus reale opt-in. Test installer silenzioso escluso perché l'app era aperta; collaudo del pacchetto distinto dal benchmark |
| V2-R29 | T33 | Cinque dimensioni QML PASS; audit nativo parziale; resize con bozza Markdown PASS sul sorgente | Sorgente `4263029`, installer 0.2.2; test bozza aggiunto dopo la build | DPI 100–200%, tastiera completa e Narrator sul pacchetto pendenti |
| V2-R30 | T34 | Guida F1/Aiuto e onboarding QML PASS; ispezione nativa IT della guida PASS | Sorgente `4263029`, installer 0.2.2 | Collaudo sul pacchetto e F5 da attestare |
| V2-R18 | T18 | Runner Homework 3 PASS (10 query, 2 regressioni) | Sorgente `4263029` | CLI indipendente dalla UI |
| V2-R08 | T08 storico | **FAIL dei vecchi budget:** no-change 1,520 s > 1 s; query p95 172,797 ms > 100 ms | Compilato locale della revisione `4263029`; installer SHA-256 `70b8d0f7a983f4f7dbfad0122f1129d9ad2af1c49b84d3e36b1606867808c4b6` | Runner completo `PASS`, tre cicli, 100 campioni e 5 warmup; report locale `experiments/results/v2-022-compiled/report.json` |
| V2-R08 | T08 finale | **PASS** dei budget rivisti, tre cicli target e correttezza inclusa `frasecom*` | Compilato pulito `800ff756`; installer SHA-256 `be9ce4c280d73e7e108c6e41a6e658fa396dc53199a3c9810dcaf29f82fd38ab` | Confronto compilato completo con 0.2.1 e report finale `experiments/results/v2-022-final-800ff75/report.json`; rallentamento storico non spiegato, accettato entro soglia |
| V2-R15–R17 | T15–T17, T19 | Nuova build pulita e verifica manifest/checksum PASS | Installer `800ff756`, SHA-256 `be9ce4c280d73e7e108c6e41a6e658fa396dc53199a3c9810dcaf29f82fd38ab` | Install/update/offline/uninstall su account standard isolato pendenti |

Un PASS automatico non sostituisce Narrator o collaudo del pacchetto. Un artefatto senza revisione e hash identificabili non chiude T08/T15–T19. Il corpus funzionale V2-01 e i benchmark V2-02 restano indipendenti.

Verifiche della revisione locale `800ff756`: backend **439 passed, 7 skipped**; frontend/script **138 passed, 1 deselected** per installer silenzioso rifiutato mentre l'app era aperta; runner Homework 3 **PASS**. La suite frontend/script senza esclusione aveva **138 passed, 1 failed** esclusivamente per lo stesso blocco dell'installer. Il commit di build è in un worktree locale separato; le modifiche corrispondenti restano nel working tree principale per la revisione. Gli artefatti finali sono conservati localmente in `dist/candidates/800ff756/`.

Massimi degli altri budget T08: build 254,258 s ≤ 300 s; riapertura 12,471 s ≤ 15 s; sync incrementale 5,198 s ≤ 60 s; working set 1.433.071.616 byte ≤ 2.560 MiB. No-change dei cicli 2/3: 0,920/0,959 s; p95 query dei cicli 1/2/3: 122,857/172,797/82,286 ms. Il criterio usa il massimo dei tre cicli, quindi T08 resta aperto. Il report è locale e ignorato da Git; non è una prova sull'installer installato.

### Revisione dei budget del 12 novembre 2026

Le righe storiche conservano l'esito con 100 ms per ogni query e 1 s per no-change. La rivalutazione separata `experiments/results/v2-022-reassessed.json` (report originale invariato) dà PASS sui nuovi budget: p95 massimo esatte 86,732 ms, wildcard ordinarie 46,544 ms, `frasecom*` nel contenuto 172,797 ms, suggerimenti 0,374 ms; no-change 1,520 s. Il [confronto alternato e il candidato finale](PERFORMANCE.md#confronto-compilato-021--022-del-12-novembre-2026) completano T08. Il rallentamento non spiegato è accettato entro le soglie; Narrator/DPI e installer su account isolato restano gate separati.
