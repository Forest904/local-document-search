# V2-14 — accettazione del candidato 0.2.2

Questo registro distingue la release pubblicata 0.2.1 dal candidato locale 0.2.2. L'11 novembre 2026 l'utente ha confermato il funzionamento dell'installer 0.2.1 scaricato da GitHub su un PC di test. Non sono stati comunicati SHA-256 del file provato, misure né esiti per singolo scenario. Tale conferma non prova il nuovo installer.

| Requisito | Scenario | Esito 0.2.2 | Revisione / artefatto | Limite o azione aperta |
|---|---|---|---|---|
| V2-R01–R19, R20–R28 | T01–T32 applicabili | Backend 437 passed, 7 skipped; frontend/script 139 passed | Sorgente 0.2.2, revisione da fissare | Benchmark e collaudo del pacchetto distinti dalle evidenze storiche |
| V2-R29 | T33 | Cinque dimensioni QML PASS; audit nativo pendente | Sorgente 0.2.2, revisione da fissare | DPI, tastiera completa e Narrator nativi sul pacchetto |
| V2-R30 | T34 | Guida F1/Aiuto e onboarding QML PASS; frontend/script 139 passed | Sorgente 0.2.2, revisione da fissare | Collaudo sul pacchetto e F5 da attestare |
| V2-R18 | T18 | Runner Homework 3 PASS (10 query, 2 regressioni) | Sorgente 0.2.2, revisione da fissare | CLI indipendente dalla UI |
| V2-R08 | T08 | Da registrare | Installer 0.2.2 con SHA-256 | Benchmark compilato, tre cicli, tutti i budget |
| V2-R15–R17 | T15–T17, T19 | Da registrare | Installer 0.2.2 con SHA-256 | Build pulita, manifest, install/update/offline/uninstall su account standard isolato |

Un PASS automatico non sostituisce Narrator o collaudo del pacchetto. Un artefatto senza revisione e hash identificabili non chiude T08/T15–T19. Il corpus funzionale V2-01 e i benchmark V2-02 restano indipendenti.
