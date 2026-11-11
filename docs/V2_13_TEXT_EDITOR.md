# V2-13 — Editor TXT/MD e anteprima Markdown

## Comportamento nel sorgente locale

I risultati Markdown si aprono in anteprima formattata; TXT nel sorgente. La pagina consente modifica del sorgente, comandi Markdown essenziali, undo/redo Qt, ricerca manuale, copia della bozza e salvataggio esplicito. Un'uscita con bozza non salvata chiede Salva, Scarta o Annulla. Il rendering dell'anteprima è asincrono, usa `markdown-it-py` e un documento Qt separato; HTML incorporato e immagini non vengono caricati. I link copiano l'indirizzo negli appunti.

`SaveTextDocument` attende il job attivo, verifica directory e versione del sorgente e sostituisce atomicamente il file. Richiede poi un nuovo sync; il file può risultare salvato anche se l'avvio del sync fallisce. Il confronto usa identità, dimensione e `mtime_ns`; non rileva modifiche esterne che preservano questi dati. La ricerca continua a consultare lo snapshot attivo fino al commit del sync. Lo schema SQLite e la CLI non cambiano.

## Evidenze — 11 novembre 2026

- Backend completo: **437 passed, 7 skipped**. I test nuovi coprono BOM e newline misti, conflitto, limiti, sostituzione fallita senza alterare l'originale, attesa del job e richiesta del sync. Il test di symlink è saltato perché la sessione Windows non consente di crearlo.
- Frontend: **86 passed** con Qt offscreen. Coperti salto in anteprima, seconda occorrenza, link, tabelle, HTML e immagini, modifica, undo di un comando Markdown, anteprima della bozza e salvataggio.
- Runner Homework 3: **PASS** su otto TXT sintetici, dieci query e due regressioni.
- Probe Qt offscreen del solo rendering Markdown, su 100.000 righe sintetiche e 10.000.000 byte: **4,922 s** in un ciclo. Misura parsing e costruzione del documento rich text; non include apertura filesystem né popolamento QML e non è un benchmark V2-02.

Le suite sono test del sorgente. Restano distinti una misura end-to-end dell'apertura al limite del reader, la verifica visiva nativa Windows con DPI/Narrator e il collaudo dell'installer completo offline. Non costituiscono una nuova release.
