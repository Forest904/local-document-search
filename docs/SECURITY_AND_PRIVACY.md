# Security & Privacy (baseline)

## 1. Natura dei dati

Il backend potrà processare documenti personali presenti in cartelle locali. **Il testo estratto viene persistito** nello snapshot: ciò può includere informazioni sensibili anche quando il file sorgente non è più accessibile. L'utente deve esserne informato nella futura UI.

## 2. Decisioni già definite

- Elaborazione locale; nessun requisito di upload cloud.
- Nessun OCR e nessun accesso al web per i reader.
- Non seguire symlink/junction o link simbolici a file: evitare scansioni esterne alla directory selezionata.
- Ricerca su snapshot eventualmente obsoleto tra due sincronizzazioni; la UI deve comunicarlo.
- Non effettuare commit di corpus utente, snapshot o testo estratto in Git.

## 3. Controlli ancora da progettare

- Percorso di salvataggio degli snapshot e permessi filesystem per utente Windows.
- Cifratura at-rest o uso delle protezioni standard dell'account: nessuna decisione presa.
- Comportamento di cancellazione sicura e retention degli snapshot vecchi.
- Politiche di logging: evitare testo estratto, query personali e percorsi assoluti nei log condivisibili.
- API locale/IPC: se esisterà un processo server, limitare accesso al dispositivo e non esporre automaticamente la porta alla rete.
- Validazione dei parser esterni per input non fidati e gestione robusta di PDF/Markdown corrotti.

## 4. Implicazione progettuale

Il salvataggio del testo estratto è una funzione confermata, ma rende prioritario definire storage per-utente, ciclo di vita e privacy notice prima del rilascio Windows.
