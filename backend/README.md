# Backend (scaffold)

Questa directory contiene il futuro package Python, organizzato in quattro livelli: `domain`, `application`, `infrastructure`, `interfaces`. **Non contiene ancora logica di produzione.** Le dipendenze runtime per parser Markdown/PDF non sono state selezionate: per questo il `pyproject.toml` non le dichiara.

Struttura e regole d'import: [Repository Layout](../docs/REPOSITORY_LAYOUT.md). Contratti: [Interface Contracts](../docs/INTERFACE_CONTRACTS.md).

Il progetto sarà installabile come package Python, ma al momento non è configurato alcun comando CLI: non attribuire capacità operative a uno scaffold non implementato.
