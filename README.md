# Local Document Search

> **Stato: architecture-first scaffold (v0.1.0).** Questa repository contiene la struttura del futuro backend, i contratti architetturali e la documentazione. **L'indicizzazione, la ricerca, la sincronizzazione e la UI non sono ancora implementate.** Non è un'applicazione funzionante.

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
├── backend/              # Package Python, contratti e punti d'estensione (scaffold)
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

Il package Python contiene moduli con **sole docstring descrittive**; non esistono ancora CLI o API eseguibili. L'elenco preciso dei file si trova in [docs/REPOSITORY_LAYOUT.md](docs/REPOSITORY_LAYOUT.md).

## Da dove partire

1. Leggere [docs/PRD.md](docs/PRD.md) e [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
2. Esaminare [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md), [docs/INTERFACE_CONTRACTS.md](docs/INTERFACE_CONTRACTS.md) e [docs/INDEXING_AND_ANALYSIS.md](docs/INDEXING_AND_ANALYSIS.md).
3. Prima di implementare, risolvere le questioni prioritarie indicate in [docs/OPEN_DECISIONS.md](docs/OPEN_DECISIONS.md).
4. Seguire [docs/ROADMAP.md](docs/ROADMAP.md) e il [piano di verifica](docs/TEST_STRATEGY.md).
5. Per il perimetro minimo del corso, vedere [docs/homework-3/ASSIGNMENT_ALIGNMENT.md](docs/homework-3/ASSIGNMENT_ALIGNMENT.md).

## Portare questa bozza su GitHub

Estrarre lo ZIP, aprire un terminale nella cartella `local-document-search/`, quindi:

```bash
git init
git add .
git commit -m "docs: scaffold architecture and contracts"
git branch -M main
# Creare un repository vuoto su GitHub dal sito, poi sostituire `USERNAME` nell’URL di esempio.
git remote add origin https://github.com/USERNAME/local-document-search.git
git push -u origin main
```

Non committare raccolte di documenti personali, snapshot operativi o testi estratti dagli utenti. Il file `.gitignore` ignora le directory di runtime convenzionali, ma non può proteggere directory arbitrarie aggiunte manualmente.

## Conformità all'Homework 3

L'esercizio richiede indicizzazione **TXT**, due campi (`nome`, `contenuto`), query da console con supporto alle frasi, circa dieci query di prova e relazione con URL del repository, scelte sugli analyzer, numero di file e tempi. PDF, Markdown, snapshot e UI sono estensioni di progetto. Nessun risultato sperimentale è ancora disponibile.

## Stato delle decisioni

Gli ADR in [docs/adr](docs/adr/) distinguono le decisioni accettate dai dettagli implementativi **non ancora stabiliti**. Non confondere la progettazione approvata con una tecnologia già selezionata (es. formato dello storage, libreria di estrazione PDF o framework Windows).
