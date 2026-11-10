# Generazione della relazione

Il testo sorgente è [REPORT.md](REPORT.md). Modificarlo e lanciare in VS Code il task **Homework 3: genera PDF**. Il task produce `output/pdf/homework-3-report.pdf` e conserva LaTeX e log in `build/homework-3/`; gli artefatti generati sono ignorati da Git.

Servono Pandoc e MiKTeX con XeLaTeX disponibili nel `PATH`. Da PowerShell il comando equivalente è:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/docs/build-report.ps1
```

Il task compila solo la relazione. Per aggiornare le misure Homework, eseguire separatamente `backend/.venv/Scripts/python.exe experiments/run_homework3.py` dalla radice del repository, verificare il JSON e modificare nel Markdown data, revisione, ambiente e risultati. Le misure v2 provengono dal [registro V2-08](../V2_08_ACCEPTANCE.md).
