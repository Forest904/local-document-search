# Indice documentazione

**Stato corrente:** M1–M8 implementate; correzioni ID e FR-18 in verifica, M9 in accettazione locale. Le decisioni approvate non sostituiscono i test.

| Documento | Scopo |
|---|---|
| [PRD.md](PRD.md) | Product Requirements Document, MVP e requisiti accettabili |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architettura generale, dependency rule, runtime e snapshot |
| [DOMAIN_MODEL.md](DOMAIN_MODEL.md) | Entità, Value Object, invarianti e query |
| [INTERFACE_CONTRACTS.md](INTERFACE_CONTRACTS.md) | Porte, casi d'uso, DTO e politiche d'errore |
| [INDEXING_AND_ANALYSIS.md](INDEXING_AND_ANALYSIS.md) | Discovery, estrazione, analyzer, posting lists e phrase query |
| [SNAPSHOTS_AND_SYNC.md](SNAPSHOTS_AND_SYNC.md) | Diff incrementale, manifest, commit e ricerca su snapshot precedente |
| [UX_WINDOWS.md](UX_WINDOWS.md) | UX prevista, stati, progress e Sync |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | Verifiche, edge case, benchmark e accettazione |
| [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md) | Ownership e dipendenze tra cartelle |
| [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md) | Trattamento locale di documenti e testo persistito |
| [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | Registro OD-01…OD-23 risolte/escluse, limiti e rischi |
| [ROADMAP.md](ROADMAP.md) | Sequenza M0–M9 con prerequisiti, attività, test e criteri di uscita |
| [M0](M0_VERIFICATION.md) · [M1](M1_VERIFICATION.md) · [M2](M2_VERIFICATION.md) · [M3](M3_VERIFICATION.md) · [M4](M4_VERIFICATION.md) · [M5](M5_VERIFICATION.md) · [M6](M6_VERIFICATION.md) · [M7](M7_VERIFICATION.md) · [M8](M8_VERIFICATION.md) · [M9](M9_VERIFICATION.md) | Evidenze datate e limiti di ciascuna milestone |
| [adr/](adr/) | Architecture Decision Records approvati/proposti |
| [homework-3/](homework-3/) | Conformità consegna, test delle query, template relazione |

**Ordine consigliato:** PRD → Architecture → Domain Model → Interface Contracts → Snapshots & Sync → Open Decisions → Roadmap.
