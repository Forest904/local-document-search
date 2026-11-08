"""Catalogo locale completo per i flussi desktop, senza servizi remoti."""
MESSAGES = {
    "app": ("Ricerca documenti", "Document search"),
    "tagline": ("I tuoi documenti, sul tuo dispositivo.", "Your documents, on your device."),
    "choose": ("Scegli cartella…", "Choose folder…"),
    "none": ("Nessuna cartella selezionata", "No folder selected"),
    "sync": ("Sincronizza", "Synchronize"),
    "retry": ("Riprova", "Retry"),
    "rebuild": ("Ricostruisci indice", "Rebuild index"),
    "recover": ("Recupera versione precedente", "Recover previous version"),
    "cancel": ("Annulla sincronizzazione", "Cancel synchronization"),
    "clear": ("Elimina dati locali…", "Delete local data…"),
    "clearTitle": ("Eliminare i dati locali?", "Delete local data?"),
    "clearBody": ("Verranno eliminati indice, cartella salvata, lingua e tema v2. I documenti originali e i dati v1 restano intatti.", "The v2 index, saved folder, language and theme will be deleted. Original documents and v1 data are preserved."),
    "delete": ("Elimina", "Delete"),
    "back": ("Indietro", "Back"),
    "continue": ("Continua", "Continue"),
    "privacyTitle": ("Solo sul tuo dispositivo", "Only on your device"),
    "privacy": ("L’elaborazione avviene sul dispositivo, senza cloud o telemetria. Il testo estratto viene salvato localmente e può restare disponibile anche quando il file sorgente è assente. Puoi eliminarlo con Elimina dati locali.", "Processing stays on your device, without cloud services or telemetry. Extracted text is stored locally and can remain available when the source file is missing. Use Delete local data to remove it."),
    "settings": ("Impostazioni", "Settings"),
    "language": ("Lingua", "Language"),
    "theme": ("Tema", "Theme"),
    "light": ("Chiaro", "Light"),
    "dark": ("Scuro", "Dark"),
    "filters": ("Filtri", "Filters"),
    "formats": ("Formati", "Formats"),
    "folder": ("Cartella relativa (es. lavoro)", "Relative folder (e.g. work)"),
    "field": ("Cerca in", "Search in"),
    "both": ("Nome e contenuto", "Name and content"),
    "filename": ("Nome", "Name"),
    "content": ("Contenuto", "Content"),
    "relevance": ("Rilevanza", "Relevance"),
    "path": ("Percorso", "Path"),
    "order": ("Ordina per", "Sort by"),
    "query": ("Cerca termini o \"frasi esatte\"…", "Search terms or \"exact phrases\"…"),
    "hint": ("Invio per cercare · prefissi espliciti: parola* · Ctrl+L per la ricerca", "Enter to search · explicit prefixes: word* · Ctrl+L to focus search"),
    "search": ("Cerca", "Search"),
    "suggestions": ("Suggerimenti", "Suggestions"),
    "results": ("Risultati", "Results"),
    "empty": ("Nessun risultato. Prova altri termini o filtri.", "No results. Try different terms or filters."),
    "enter": ("Premi Invio per cercare", "Press Enter to search"),
    "welcome": ("Scegli una cartella per iniziare", "Choose a folder to get started"),
    "building": ("La ricerca sarà disponibile dopo l’indicizzazione", "Search will be available after indexing"),
    "preview": ("Anteprima", "Preview"),
    "select": ("Seleziona un risultato per leggere il testo acquisito.", "Select a result to read the indexed text."),
    "open": ("Apri file", "Open file"),
    "previous": ("Precedente", "Previous"),
    "next": ("Successiva", "Next"),
    "ready": ("Indice disponibile", "Index available"),
    "old": ("Ricerca sulla versione precedente durante la sincronizzazione", "Searching the previous version while synchronizing"),
    "closing": ("Chiusura: attendo operazioni e letture in corso…", "Closing: waiting for operations and reads…"),
    "loading": ("Caricamento…", "Loading…"),
    "details": ("Diagnostiche", "Diagnostics"),
    "complete": ("Report completo", "Complete report"),
    "incomplete": ("Report incompleto", "Incomplete report"),
    "excluded": ("Esclusi", "Excluded"),
    "failure": ("Operazione non riuscita. Riprova.", "Operation failed. Try again."),
    "InvalidInput": ("Query o opzioni non valide. Controlla frasi, prefissi e filtri.", "Invalid query or options. Check phrases, prefixes and filters."),
    "SourceUnavailable": ("Cartella sorgente non disponibile. Verifica il percorso e riprova Sync; l’indice precedente resta consultabile.", "Source folder unavailable. Check the path and retry Sync; the previous index remains searchable."),
    "SnapshotUnavailable": ("Versione non disponibile. Ripeti la ricerca oppure usa ricostruzione o recupero.", "Version unavailable. Search again, rebuild or recover the index."),
    "StorageFailure": ("Impossibile accedere ai dati locali. Controlla spazio, permessi e altre istanze; riprova.", "Cannot access local data. Check space, permissions and other instances; retry."),
    "ResourceFailure": ("Risorse insufficienti. Libera memoria e riprova.", "Insufficient resources. Free memory and retry."),
    "ExtractionFailure": ("Acquisizione non riuscita o file modificato durante la lettura. Riprova Sync.", "Extraction failed or a file changed during reading. Retry Sync."),
    "FileNotFoundError": ("File non disponibile. Premi Sincronizza per aggiornare l’indice.", "File unavailable. Synchronize to update the index."),
    "OSError": ("Impossibile aprire il file con l’applicazione predefinita.", "Cannot open the file with the default application."),
    "ACCEPTED": ("Annullamento richiesto…", "Cancellation requested…"),
    "COMMIT_STARTED": ("Commit iniziato: annullamento non più possibile.", "Commit started: cancellation is no longer possible."),
    "FINISHED": ("Il job è già terminato.", "The job has already finished."),
    "PENDING": ("In attesa", "Pending"),
    "RUNNING": ("Sincronizzazione in corso", "Synchronizing"),
    "COMPLETED": ("Indice aggiornato", "Index up to date"),
    "FAILED": ("Sincronizzazione non riuscita. Riprova.", "Synchronization failed. Retry."),
    "CANCELLED": ("Sincronizzazione annullata", "Synchronization cancelled"),
    "SCANNING": ("Scansione", "Scanning"),
    "EXTRACTING": ("Acquisizione", "Extracting"),
    "ANALYZING": ("Analisi", "Analyzing"),
    "BUILDING": ("Costruzione indice", "Building index"),
    "COMMITTING": ("Salvataggio finale", "Committing"),
    "exclusion": ("Documento escluso", "Document excluded"),
    "error": ("Errore di acquisizione", "Extraction error"),
}


def translate(key, language):
    return MESSAGES.get(key, MESSAGES["failure"])[language == "en"]


def catalog(language):
    return {key: translate(key, language) for key in MESSAGES}


DIAGNOSTICS = {
    "PDF senza testo estraibile": "PDF has no extractable text",
    "Esclusione intenzionale": "Intentional exclusion",
    "File non decodificabile": "File cannot be decoded as UTF-8",
    "PDF protetto o illeggibile": "Protected or unreadable PDF",
    "Lettura o estrazione fallita": "Reading or extraction failed",
    "Pubblicazione dello snapshot fallita": "Snapshot publication failed",
    "Operazione fallita": "Operation failed",
}


def diagnostic_text(reason, category, language):
    if reason in DIAGNOSTICS:
        return reason if language == "it" else DIAGNOSTICS[reason]
    return translate("exclusion" if category == "excluded" else category if category in MESSAGES else "error", language)
