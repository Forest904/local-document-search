# Layout e ownership

La struttura fisica esistente è la base. Questa pagina assegna responsabilità; non dichiara che i moduli v2 siano già presenti.

| Area | Responsabilità |
|---|---|
| `backend/src/local_document_search/domain/` | Documenti, analyzer, query, indici, snapshot e futura logica pura di ranking/vocabolario ordinato |
| `backend/src/local_document_search/application/` | Casi d'uso, DTO, porte, job, sync, futuri filtri/suggerimenti/cancel |
| `backend/src/local_document_search/infrastructure/` | Discovery, reader, SQLite e storage preferenze v2 mediante le porte |
| `backend/src/local_document_search/interfaces/` | CLI Homework e composizione backend |
| `frontend/src/local_document_search_desktop/` | Desktop attuale Qt Widgets; nuova presentazione Qt Quick, composizione desktop e risorse QML v2 |
| `scripts/dev/`, `scripts/package/` | Avvio sviluppo e ZIP v1; futuro installer v2 in automazione di packaging dedicata |
| `experiments/` | Generatori e runner esistenti; futura acquisizione e validazione del corpus ibrido secondo la [specifica](TEST_DATASETS.md) |
| `docs/`, `docs/archive/v1/` | Specifiche correnti e fotografia storica v1 |

Il dominio dipende solo da standard library e dominio. Application dipende da dominio e dalle proprie porte. Infrastructure implementa le porte; frontend importa API pubbliche application e PySide6, non strutture interne o filesystem di storage. Introduzioni di moduli e dipendenze seguono questi confini, senza `shared/` generico né porta per ogni classe. La CLI resta installabile senza Qt.

[Manifest e ground truth](TEST_DATASETS.md) saranno versionati; documenti Internet scaricati, output dei generatori, dati personali, snapshot, log runtime, build, dist e risultati dei benchmark restano fuori da Git. Su Windows v1 usa `%LOCALAPPDATA%/LocalDocumentSearch`; v2 avrà una radice separata approvata in [V2-D04](OPEN_DECISIONS.md). [Privacy](SECURITY_AND_PRIVACY.md).
