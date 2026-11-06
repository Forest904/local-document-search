# Backend — fondazioni M1

Package Python >=3.12 con modelli immutabili, DTO di ricerca, porte e punto di composizione minimo. Nessuna dipendenza runtime esterna. Analyzer, parser, matching, reader, repository operativo, CLI e job restano nelle milestone successive.

## Installazione e verifica

Da `backend/`, su Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest
```

Su Linux attivare l'ambiente con `source .venv/bin/activate`; gli altri comandi restano uguali.
`requirements-dev.txt` fissa le dipendenze di sviluppo e transitive per Python 3.12 e include l'installazione editable con extra dev. Le dipendenze di build sono fissate anche nel `pyproject.toml`.
Il comando rapido `python -m pip install -e ".[dev]"` resta supportato, ma da solo non fissa tutte le dipendenze transitive: per riprodurre la verifica M1 usare il file requirements.

GitHub Actions configura gli stessi controlli su Windows e Linux, Python 3.12. La verifica locale non sostituisce l'esecuzione remota: [evidenze e limiti](../docs/M1_VERIFICATION.md).

## Confini implementati

- Domain: documenti, token, clausole, posting e snapshot immutabili; nessun I/O.
- Application: DTO e quattro `Protocol`; nessun adapter concreto.
- Interfaces: `compose_application` riceve dipendenze esplicite e restituisce un contenitore tipizzato. Il cablaggio operativo sarà introdotto in M3.
- Test: invarianti, coerenza, copie difensive, DTO, sostituti di test e controllo AST degli import.

Reader pypdf/markdown-it-py (M4), SQLite (M5) e PySide6 (M8) non vengono installati. Non è configurato un comando CLI.
Vedere [Layout](../docs/REPOSITORY_LAYOUT.md) e [Contratti](../docs/INTERFACE_CONTRACTS.md).
