# Local Document Search

Local Document Search è un’app per Windows che trova documenti sul tuo computer cercando nel nome e nel contenuto di file TXT, Markdown e PDF testuali. Scegli una cartella, anche con sottocartelle, e cerca parole o frasi: i risultati mostrano un estratto evidenziato e si aprono nell’app associata al file.

Funziona localmente e offline, senza account né invio dei documenti a servizi esterni. L’interfaccia Luma è disponibile in italiano e inglese, con tema chiaro o scuro.

## Scarica e prova

Serve **Windows 11 x64**; non occorre installare Python.

1. Apri la [release 0.2.0](https://github.com/Forest904/local-document-search/releases/tag/v0.2.0) e scarica `LocalDocumentSearch-0.2.0-windows-x64-setup.exe` dalla sezione **Assets**.
2. Esegui l’installer e avvia **Local Document Search** dal menu Start.
3. Premi **Accetta e scegli una cartella**, seleziona i documenti e attendi la prima indicizzazione.
4. Scrivi una query e premi **Invio**. Per esempio: `bilancio`, `"relazione annuale"` oppure `progett*`. Clicca un risultato per aprire il file.

In **Impostazioni** puoi scegliere campo di ricerca, formati, ordinamento e cartella. Ai successivi avvii l’app recupera l’indice e sincronizza in background; **F5** aggiorna manualmente. Non c’è monitoraggio continuo delle modifiche. I PDF scansionati senza testo richiederebbero OCR, che non è supportato.

Il pacchetto non è firmato digitalmente; nella release trovi il checksum `.sha256`. Per aggiornare, chiudi l’app e avvia il nuovo installer. La disinstallazione conserva i dati salvo tua scelta esplicita.

Testo estratto, indici e preferenze sono salvati in `%LOCALAPPDATA%/LocalDocumentSearch/Data`, anche quando un originale non è più disponibile. Puoi eliminarli dalle Impostazioni senza cancellare i documenti. [Privacy e termini d’uso](docs/SECURITY_AND_PRIVACY.md).

## Avvio dal sorgente

Con Git e **Python 3.12 o successivo, x64**, da PowerShell:

```powershell
git clone https://github.com/Forest904/local-document-search.git
cd local-document-search
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -e ./backend -e ./frontend
backend/.venv/Scripts/local-document-search-desktop.exe
```

L’installazione delle dipendenze richiede rete o una cache pip completa. In VS Code puoi anche usare il task **Local Document Search: avvia / riavvia**, che prepara l’ambiente automaticamente: [guida allo sviluppo](scripts/dev/README.md).

Per la sola CLI, senza Qt, installa soltanto `./backend` e avvia `backend/.venv/Scripts/local-document-search.exe "C:/percorso/documenti"`. [Sintassi e test backend](backend/README.md) · [uso e test desktop](frontend/README.md).

## Per approfondire

[Documentazione del progetto](docs/README.md): requisiti, architettura, decisioni e verifiche. La [consegna Homework 3](docs/homework-3/README.md) resta una regressione indipendente del backend.

L’uso personale, di studio e interno è gratuito, anche professionale. Vendita, integrazione in prodotti distribuiti e offerta come servizio richiedono autorizzazione scritta: [termini italiani](scripts/package/TERMS-IT.txt).

Il nome pubblico resta **Local Document Search**, indipendentemente dalla generazione interna. Per passare dalla precedente installazione nella cartella `LocalDocumentSearchV2`, disinstallarla conservando i dati e installare il nuovo pacchetto. Al primo avvio scegliere nuovamente la cartella e indicizzarla: i dati precedenti restano conservati e non vengono importati.

Nel codice successivo alla release 0.2.0, il wizard permette di scegliere la cartella applicativa alla prima installazione, mostra un riepilogo, consente di riprovare dopo aver chiuso l'app e propone l'avvio finale. Un aggiornamento mantiene la cartella registrata; per cambiarla occorre disinstallare conservando i dati e reinstallare. Indici e preferenze restano nel percorso indicato sopra. Queste modifiche non sono ancora una nuova release pubblicata.
