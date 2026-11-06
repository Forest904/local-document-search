# Windows frontend — futuro

Non esiste ancora un progetto UI. Il frontend Windows consumerà i contratti applicativi del backend (direttamente tramite adapter oppure tramite un canale locale da scegliere). Non può importare le strutture interne del positional index.

Esperienza prevista: selezione cartella, scansione e indicizzazione in background, progress bar, ricerca stile Google, pulsante Sync con spinner/check temporaneo, visualizzazione dei file e degli eventuali risultati obsoleti mentre un aggiornamento procede.

**Aperto:** WPF vs WinUI 3 o altro framework; trasporto API locale/IPC; distribuzione e avvio del backend; policy di gestione dei processi. Vedi [UX_WINDOWS.md](../docs/UX_WINDOWS.md) e [OPEN_DECISIONS.md](../docs/OPEN_DECISIONS.md).
