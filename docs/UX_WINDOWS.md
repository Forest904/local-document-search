# Esperienza desktop v2 — Windows 11

**Direzione approvata, non implementata.** Il desktop attuale usa Qt Widgets; [UX v1](archive/v1/UX_WINDOWS.md). La v2 usa PySide6/Qt Quick e QML, con ispirazione dall'app desktop ChatGPT per chiarezza, spaziatura e qualità visiva. La funzione centrale rimane la ricerca documentale.

## Flussi

1. **Installazione e primo avvio.** Wizard offline per utente, informativa sui dati locali, scelta cartella e indicizzazione. Mostrare fase, conteggi e progresso senza presentare i byte come ETA.
2. **Apertura successiva.** Recuperare lo snapshot v2, cercare mentre il sync automatico verifica la cartella; indicare quando i risultati possono essere obsoleti. Sorgente assente: preservare ricerca sullo snapshot compatibile e spiegare il limite.
3. **Ricerca.** Campo centrale con ricerca su Invio; suggerimenti durante digitazione distinti dai risultati. Campo nome/contenuto/entrambi, filtri formato/cartella e ordinamento per rilevanza predefinito, con alternativa per percorso.
4. **Risultati e lettura.** Sidebar essenziale per cartella, stato, filtri e impostazioni; lista con snippet/evidenziazione; pannello di anteprima del testo persistito e comando Apri file. Se il file non esiste, proporre Sync. Nessun rendering PDF promesso.
5. **Sync e recupero.** Stato del job, diagnostiche sicure, annullamento fino al commit, retry dopo errore. Un job annullato lascia il precedente snapshot. Pulizia confermata e indisponibile durante job incompatibile.

Le risposte superate da nuova query, campo, filtro, ordinamento, selezione o directory sono ignorate. Se una pagina proviene da nuovo snapshot, tornare alla prima con il contesto corrente. La UI non esegue letture o query pesanti nel thread grafico. Chiusura e cancel seguono il [lifecycle](SNAPSHOTS_AND_SYNC.md).

## Sistema visivo e accessibilità

Due temi, chiaro e scuro, con tipografia leggibile, spaziatura coerente, stati vuoti ed errori visibili. Italiano e inglese sono completi nei flussi e nelle diagnostiche; lingua e tema persistono nello storage v2. La somiglianza visiva non comporta chat, AI o account.

Tutti i comandi principali devono essere raggiungibili da tastiera, con ordine di tabulazione prevedibile, focus visibile, etichette accessibili e scorciatoie documentate. Verificare contrasto, zoom/DPI e dimensioni finestra supportate; provare con Narrator selezione cartella, ricerca, risultati, anteprima, job, errore e impostazioni. Gli esiti effettivi appartengono ai report V2-06/V2-08, non a questa specifica.
