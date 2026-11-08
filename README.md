# Local Document Search

Ricerca locale in file TXT, Markdown e PDF testuali, per nome e contenuto, con due indici invertiti posizionali proprietari.

**Disponibile oggi dal sorgente:** CLI Homework e backend condiviso, desktop Qt Quick v2 con ricerca, anteprima e preferenze IT/EN e chiaro/scuro. V2-01–V2-05 sono chiuse localmente; V2-06 è implementata e [resta aperta per la verifica manuale completa di accessibilità](docs/V2_06_DESKTOP.md). La distribuzione pubblica richiede V2-07/V2-08. M9 v1 è [parzialmente accettata](docs/BASELINE.md).

**Evoluzione organica:** v2 prosegue dal codice e dalle verifiche M0–M9 nello stesso repository; [mappa di continuità](docs/BASELINE.md#continuità-da-m0m9-a-v2).

**Corpus funzionale v2:** [sintetici riproducibili e documenti Internet verificati](docs/TEST_DATASETS.md), costruiti a partire dai generatori Homework/M9 esistenti.

**Direzione v2:** prodotto Windows 11 x64 offline, UI Qt Quick, ricerca con rilevanza e anteprime evidenziate, prestazioni misurate e installer completo. [Requisiti](docs/PRD.md) → [roadmap](docs/ROADMAP.md). Il percorso principale di lettura richiede indicativamente 15–20 minuti; i dettagli sono nell'[indice tecnico](docs/README.md).

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

Uso e test: [backend](backend/README.md), [desktop](frontend/README.md). Lo [script di packaging attuale](scripts/package/README.md) genera un prototipo ZIP Qt Quick; l'installer è V2-07.

## Progetto e dati

Backend e CLI sono in `backend/`, desktop in `frontend/`, automazione in `scripts/`, esperimenti sintetici in `experiments/`. [Ownership e confini](docs/REPOSITORY_LAYOUT.md).

Il desktop conserva testo estratto, indici e preferenze v2 in `%LOCALAPPDATA%/LocalDocumentSearchV2`, anche se un sorgente diventa assente. Nessun cloud; corpus personali, snapshot e testo estratto restano fuori da Git. [Privacy](docs/SECURITY_AND_PRIVACY.md).

La [consegna Homework 3](docs/homework-3/README.md) rimane una baseline di regressione. [Documentazione v1 archiviata](docs/archive/v1/README.md); [decisioni architetturali](docs/adr/README.md).

## Distribuzione e diritti

La distribuzione pubblica v2 non è ancora disponibile. I [termini italiani](scripts/package/TERMS-IT.txt) consentono l'uso personale, di studio e interno gratuito, anche per imprese e professionisti. Vendita, integrazione in prodotti distribuiti e offerta delle funzioni come servizio a terzi richiedono autorizzazione scritta. La verifica degli obblighi delle dipendenze sul payload finale resta un gate di rilascio. [Politica e gate](docs/SECURITY_AND_PRIVACY.md#distribuzione-e-diritti).
