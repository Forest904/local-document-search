# Local Document Search

> **Stato: M1–M5 implementate e verificate localmente (v0.1.0).** CLI TXT/Markdown/PDF operativa, discovery ricorsiva, reader UTF-8 rigorosi per TXT/Markdown, build completo e ricerca su snapshot in memoria. Persistenza SQLite e recupero testo per versione disponibili nel backend; sync e UI restano nelle milestone successive. [Evidenze M5](docs/M5_VERIFICATION.md).

Motore di ricerca documentale **locale** per file `.txt`, `.md` e `.pdf` testuali, basato su **due indici invertiti posizionali implementati internamente** (nome e contenuto). Il backend è progettato per essere riutilizzato inizialmente da una CLI (Homework 3 di Ingegneria dei Dati) e successivamente da una UI desktop Windows.

## Ambito della prima versione

- Una directory attiva alla volta, esplorata ricorsivamente, senza seguire symlink o junction.
- Un file fisico = un documento. Conversione TXT/Markdown/PDF testuali in un CDM con contenuto testuale unico; nessun OCR.
- Analyzer distinti per `filename` e `content`, corpus potenzialmente multilingue, positional inverted index costruito senza un motore IR esterno.
- Snapshot dell'indice immutabili e persistenti, con attivazione atomica; testo estratto persistito per future anteprime/snippet.
- Sincronizzazione incrementale con confronto **solo** di percorso, dimensione e `mtime_ns`, all'avvio, dopo nuova selezione e su richiesta manuale.
- Indicizzazione asincrona, progresso misurabile per byte dei file completati, ricerca disponibile sullo snapshot precedente mentre la sincronizzazione è in corso.
- Ricerca su entrambi i campi: l'intera query deve soddisfare **almeno un singolo campo**; termini non quotati con semantica AND, query tra virgolette come frase.

Le caratteristiche elencate rappresentano **requisiti/decisioni**, non funzioni attualmente implementate.

## Repository

```text
local-document-search/
├── backend/              # Package Python, modelli, contratti e test M1
│   ├── pyproject.toml
│   ├── src/local_document_search/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   └── tests/
├── frontend/             # Segnaposto per la futura applicazione Windows
├── experiments/          # Piano delle query e misure dell'homework
├── docs/                 # PRD, architettura, dominio, contratti, ADR e limiti
├── .gitignore
└── README.md
```

Installazione e test sono descritti in [backend/README.md](backend/README.md). Con ambiente virtuale attivo:

```powershell
local-document-search "C:\percorso\documenti"
```

Esempi di query: `nome report`, `contenuto "roma tre"`, `entrambi machine "deep learning"`. Senza prefisso si cerca in entrambi i campi; l'intera query deve essere soddisfatta da un singolo campo. EOF o Ctrl+C chiudono la sessione. Tutti i risultati vengono stampati, ordinati per percorso. L'indice è ricostruito in RAM a ogni avvio.

Suite locale: 268 test superati, 5 skip; [limiti della verifica](docs/M5_VERIFICATION.md). La CI Windows/Linux è configurata, ma non ancora verificata su GitHub.

## Da dove partire

1. Leggere [docs/PRD.md](docs/PRD.md) e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
2. Esaminare [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md), [docs/INTERFACE_CONTRACTS.md](docs/INTERFACE_CONTRACTS.md) e [docs/INDEXING_AND_ANALYSIS.md](docs/INDEXING_AND_ANALYSIS.md).
3. Consultare le decisioni v1 e le milestone di verifica in [docs/OPEN_DECISIONS.md](docs/OPEN_DECISIONS.md).
4. Seguire [docs/ROADMAP.md](docs/ROADMAP.md) e il [piano di verifica](docs/TEST_STRATEGY.md).
5. Per il perimetro minimo del corso, vedere [docs/homework-3/ASSIGNMENT_ALIGNMENT.md](docs/homework-3/ASSIGNMENT_ALIGNMENT.md).

## Repository pubblico e dati locali

Repository: https://github.com/Forest904/local-document-search. Le modifiche M5 sono locali finché non vengono committate e pubblicate. Non committare raccolte personali, snapshot o testi estratti dagli utenti. La `.gitignore` copre directory runtime convenzionali; le fixture e il corpus Homework sono sintetici.

## Conformità all'Homework 3

L'esercizio richiede indicizzazione **TXT**, due campi (`nome`, `contenuto`), query da console con supporto alle frasi, circa dieci query di prova e relazione con URL del repository, scelte sugli analyzer, numero di file e tempi. PDF, Markdown, snapshot e UI sono estensioni di progetto. Dieci query e due regressioni sono state eseguite con successo su otto TXT sintetici: [relazione compilata](docs/homework-3/REPORT.md) e [runner riproducibile](experiments/run_homework3.py).

## Stato delle decisioni

Gli ADR in [docs/adr](docs/adr/) registrano le decisioni v1: SQLite, pypdf, markdown-it-py e PySide6 Qt Widgets, con ZIP Windows 11 x64. pypdf e markdown-it-py sono operativi in M4; SQLite è operativo nel backend M5 tramite standard library; PySide6 resta da implementare. La [roadmap](docs/ROADMAP.md) anticipa la CLI TXT per il corso e conduce al desktop distribuibile.
