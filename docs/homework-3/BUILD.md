# Generazione della relazione

Il testo sorgente è [REPORT.md](REPORT.md). Modificarlo e lanciare in VS Code il task **Homework 3: genera PDF**. Il task produce `output/pdf/homework-3-report.pdf` e conserva LaTeX e log in `build/homework-3/`; gli artefatti generati sono ignorati da Git.

Servono Pandoc e MiKTeX con XeLaTeX disponibili nel `PATH`. Da PowerShell il comando equivalente è:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/docs/build-report.ps1
```

Il task compila solo la relazione e copia le figure nella directory di lavoro. La versione del 12 novembre 2026 contiene dieci pagine, con interruzioni esplicite nel Markdown. Per aggiornare le misure Homework, eseguire separatamente `backend/.venv/Scripts/python.exe experiments/run_homework3.py` dalla radice, verificare il JSON e aggiornare data, revisione, ambiente e risultati. Le misure del candidato 0.2.2 provengono dal [registro prestazionale](../PERFORMANCE.md); stato e limiti dal [registro V2-14](../V2_14_ACCEPTANCE.md). Non attribuire automaticamente queste evidenze a revisioni successive.

## Figure e controllo visivo

Le immagini in `figures/` sono versionate. Per rigenerarle con il backend e il frontend installati nell'ambiente di sviluppo:

```powershell
backend/.venv/Scripts/python.exe scripts/docs/create-report-figures.py
```

Il generatore usa PySide6 e i font Windows Segoe UI/Consolas: crea due schemi e cattura due schermate del QML effettivo con tre documenti sintetici. Corpus e storage sono temporanei e separati dalla sessione personale. `interfaccia.png` riunisce le due catture senza alterarne il contenuto. Il rendering offscreen non attesta accessibilità nativa o funzionamento dell'installer. Aggiornare la revisione dichiarata nel report se si rigenerano le schermate con altro codice.

Dopo la compilazione, renderizzare e ispezionare tutte le pagine:

```powershell
pdftoppm -scale-to 1300 -png output/pdf/homework-3-report.pdf build/homework-3/check
```

Verificare 8–10 pagine, tabelle e didascalie integre, figure leggibili, collegamenti e numerazione. Controllare nel log XeLaTeX l'assenza di `Overfull` e `Missing character`. PDF, PNG di verifica e log generati restano fuori Git; `REPORT.md` resta l'unica fonte del testo.
