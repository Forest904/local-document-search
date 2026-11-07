# Local Document Search

Ricerca locale in file TXT, Markdown e PDF testuali, per nome e contenuto, con due indici invertiti posizionali proprietari.

**Disponibile oggi: v1 (pacchetti 0.1.0).** CLI Homework, backend persistente, desktop italiano Qt Widgets e ZIP standalone personale. M9 è parzialmente accettata: vedere [baseline e verifiche mancanti](docs/BASELINE.md). La v2 è progettata, non implementata.

**Evoluzione organica:** v2 prosegue dal codice e dalle verifiche M0–M9 nello stesso repository; [mappa di continuità](docs/BASELINE.md#continuità-da-m0m9-a-v2).

**Primo incremento v2:** [corpus ibrido per test funzionali](docs/TEST_DATASETS.md), costruito a partire dai generatori Homework/M9 esistenti. I documenti Internet non sono ancora acquisiti.

**Direzione v2:** prodotto Windows 11 x64 offline, nuova UI Qt Quick, ricerca con rilevanza e anteprime evidenziate, prestazioni misurate e installer completo. [Requisiti](docs/PRD.md) → [roadmap](docs/ROADMAP.md). Il percorso principale di lettura richiede indicativamente 15–20 minuti; i dettagli sono nell'[indice tecnico](docs/README.md).

## Avvio attuale

Da Windows/VS Code: **Terminal → Run Task → Local Document Search: avvia / riavvia**. Il task prepara l'ambiente Python e avvia il desktop attuale; [prerequisiti e comportamento](scripts/dev/README.md).

Oppure, dalla radice con Python >=3.12 e un ambiente virtuale attivo:

```powershell
python -m pip install -e "./backend[dev]" -e "./frontend[dev]"
local-document-search-desktop
```

Per la sola CLI, senza Qt:

```powershell
python -m pip install -e "./backend[dev]"
local-document-search "C:/percorso/documenti"
```

Esempi: `nome report`, `contenuto "roma tre"`, `entrambi machine "deep learning"`. AND e frasi devono corrispondere interamente nello stesso campo. La CLI ricostruisce l'indice in memoria a ogni sessione, stampa tutti i risultati per percorso ed esce con EOF o Ctrl+C.

Uso e test: [backend](backend/README.md), [desktop](frontend/README.md). Lo [script di packaging attuale](scripts/package/README.md) genera lo ZIP v1, non l'installer v2.

## Progetto e dati

Backend e CLI sono in `backend/`, desktop in `frontend/`, automazione in `scripts/`, esperimenti sintetici in `experiments/`. [Ownership e confini](docs/REPOSITORY_LAYOUT.md).

Il desktop attuale conserva testo estratto e indici in `%LOCALAPPDATA%/LocalDocumentSearch`, anche se un sorgente diventa assente. Nessun cloud; corpus personali, snapshot e testo estratto restano fuori da Git. [Privacy](docs/SECURITY_AND_PRIVACY.md).

La [consegna Homework 3](docs/homework-3/README.md) rimane una baseline di regressione. [Documentazione v1 archiviata](docs/archive/v1/README.md); [decisioni architetturali](docs/adr/README.md).

## Distribuzione e diritti

La distribuzione pubblica v2 non è ancora disponibile. La politica approvata prevede diritti riservati sul codice del progetto e uso gratuito personale e di studio; l'uso professionale richiede autorizzazione. I termini completi e gli obblighi delle dipendenze devono essere verificati prima del rilascio: questa descrizione non è un contratto di licenza completo. [Politica e gate di rilascio](docs/SECURITY_AND_PRIVACY.md#distribuzione-e-diritti).
