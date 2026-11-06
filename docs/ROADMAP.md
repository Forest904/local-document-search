# Roadmap — Dal progetto all'applicazione

**Stato attuale:** M0, scaffold e specifiche. Le milestone successive non sono state implementate.

| Milestone | Deliverable | Condizione d'uscita |
|---|---|---|
| **M0 — Architecture** | PRD, Domain, contratti, ADR, repository scaffold | Decisioni approvate documentate; aperte esplicitate |
| **M1 — Search Core** | Analyzer, IndexBuilder, QueryParser/Evaluator | Test unitari di AND/phrase e due indici verdi |
| **M2 — Readers** | TXT, Markdown, PDF testuali + CDM | Contract test, errori/exclusions, nessun OCR |
| **M3 — Storage & Sync** | Manifest, snapshot, persist/activate, incrementale | Restart, add/modify/remove, rollback e recovery testati |
| **M4 — CLI & Homework 3** | Comandi console, ~10 query, benchmark e relazione | Requisiti del corso soddisfatti con dati misurati |
| **M5 — Windows frontend** | Selettore directory, progress, Sync, search bar | UI responsiva, stesso backend, nessuna dipendenza del core da Windows |

### Sequenza operativa consigliata

Prima formalizzare OD-01/02, OD-05/06/07/08/09/10/12; poi test di dominio, implementazione e adapter. La milestone M4 per il corso va mantenuta **indipendente** dal completamento del frontend.

L'Homework 3 ha una scadenza indicata nel materiale del corso: **13 novembre 2026 alle 18:00**. Le estensioni del prodotto desktop non devono impedire la consegna del programma TXT e della relazione.

Nessun target prestazionale quantitativo o data di rilascio dell'app Windows è stato concordato.
