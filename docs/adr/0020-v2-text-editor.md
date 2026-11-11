# ADR 0020 — Editor TXT/MD e anteprima Markdown

- **Stato:** Accepted, 11 novembre 2026 (decisione approvata dall'utente nel piano V2-13).
- **Contesto:** il reader V2-12 mostra soltanto il sorgente; la modifica dei documenti originali era esclusa dal PRD.
- **Decisione:** il desktop apre MD in anteprima formattata e TXT nel reader; entrambi possono passare all'editor del sorgente. Il salvataggio è esplicito e riguarda soltanto TXT/MD aperti dai risultati. Il buffer sorgente resta autoritativo. L'anteprima usa `markdown-it-py` e il rich text Qt, senza WebEngine, rete, immagini o HTML eseguibile.
- **Navigazione:** si proietta l'intervallo sorgente V2-12 nell'anteprima tramite marcatori inseriti agli offset di provenienza prima del parsing; se i marcatori non sopravvivono al rendering, il salto formattato non viene mostrato come esatto. La ricerca manuale è distinta dall'indice.
- **Scrittura:** la porta applicativa salva un temporaneo nello stesso contenitore e lo sostituisce atomicamente solo se identità, size e `mtime_ns` corrispondono all'apertura. BOM e terminatori esistenti sono conservati; nuove righe usano il terminatore prevalente. La bozza resta disponibile dopo errori o conflitti.
- **Sync:** il salvataggio attende i job attivi; l'ammissione dei job è bloccata durante la scrittura. Subito dopo viene richiesto un nuovo sync. Il salvataggio non dipende dal suo esito, e la ricerca resta sul precedente snapshot fino al commit.
- **Limiti:** un controllo dei metadati non rileva modifiche esterne che preservano identità, size e timestamp; resta una finestra di gara fra verifica finale e `os.replace`. Rendering, salvataggio e collaudo dell'installer sono evidenze distinte.
- **Compatibilità:** schema SQLite, query e CLI Homework invariati. [Contratti](../INTERFACE_CONTRACTS.md), [UX](../UX_WINDOWS.md), [scenari](../TEST_STRATEGY.md).
