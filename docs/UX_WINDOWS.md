# Esperienza desktop Luma — Windows 11

V2-11: selezionare un risultato PDF apre una pagina interna con il documento alla pagina del primo match, numero di pagina, zoom, adattamento alla larghezza, apertura nell'app predefinita e apertura della cartella originale. Controlli compatti a icona con tooltip e nome accessibile; pinch e trascinamento hanno escursione moderata. Ctrl+F apre «Trova nel PDF» con la query della risposta precompilata; Invio avvia la ricerca letterale nel PDF, Invio/Shift+Invio e le icone passano fra le occorrenze. Se il file non ha testo ricercabile, il comando è disabilitato. Escape chiude prima la ricerca, poi torna ai risultati. TXT e MD conservano l'apertura esterna. Il viewer non evidenzia automaticamente la parola della query Luma; [specifica](V2_11_PDF_PAGE_NAVIGATION.md).

**Local Document Search** è il nome dell’app; **Luma** quello del motore. Qt Quick/QML e backend in-process. La revisione approvata dell’8 novembre 2026 sostituisce sidebar e anteprima con apertura diretta: [ADR 0011](adr/0011-v2-desktop.md).

## Percorsi

1. **Primo avvio:** informativa e «Accetta e scegli una cartella». Il backend parte dopo l’accettazione, poi apre il selettore nativo; annullarlo lascia disponibile la scelta.
2. **Preparazione:** cartella, fase, conteggi e progresso reale sulla stessa pagina; fasi senza percentuale indeterminate, nessuna ETA inventata. Consigli IT/EN ogni otto secondi, senza prendere focus o annuncio continuo a Narrator.
3. **Completamento:** home solo con snapshot ricercabile. Errore/cancel senza snapshot lascia retry, scelta cartella, ricostruzione e diagnostiche; recupero del precedente disponibile nel backend.
4. **Riapertura:** catalogo v2 esistente → recupero automatico, home e sync in background. Se il sorgente manca, ricerca sullo snapshot con avviso di possibile obsolescenza.
5. **Home:** marchio statico senza slogan, barra con lente e Impostazioni. Invio/lente eseguono; digitare propone suggerimenti per prefisso o, dopo `*`, per suffisso. Selezionarne uno sostituisce l'intera clausola con il termine esatto e avvia la ricerca. Non si propongono completamenti dentro frasi o wildcard malformate.
6. **Risultati:** titolo, percorso, formato ed estratto evidenziato dallo snapshot. Clic/Invio sul risultato apre l’app Windows associata, senza richiedere dettagli o anteprima interna. Esc torna alla home; eseguire una barra vuota torna alla home senza cercare.
7. **Impostazioni:** aspetto/lingua, ricerca, cartella/indice; sync, rebuild e diagnostiche. Campo e formati affiancati; reset e pulizia confermata in fondo. Sottocartella e recupero non sono esposti. Indietro preserva schermata/query; il pulsante Impostazioni compare solo in home.

## Ricerca e stato

Risultati in pagine da **20**; frecce visibili solo con più pagine, centrate ai lati del riepilogo localizzato di pagina/intervallo. La durata misura invio→risposta pubblicata, attesa worker inclusa: tre decimali, virgola IT e punto EN. Nuova query azzera il tempo; risposte obsolete non lo pubblicano.

Campo, formati e ordine valgono per la sessione; reset al cambio cartella/riavvio a BOTH, TXT/MD/PDF e rilevanza. Almeno un formato selezionato. Home/risultati mostrano restrizioni e reset; cambiare opzioni aggiorna una ricerca eseguita dalla prima pagina. Nessuna sintassi `type:pdf`.

Lingua IT/EN e tema chiaro/scuro persistono nel catalogo, separati dagli snapshot; la pulizia li azzera. Comandi incompatibili con job/chiusura bloccati, lavoro nei worker e risposte obsolete ignorate.

Dopo ogni ricerca di parole esatte, il riquadro «Intendevi…?» mostra una query proposta quando esistono correzioni plausibili, anche con risultati. Elenca le sostituzioni; il pulsante «Cerca con le correzioni», raggiungibile da tastiera e nominato per Narrator, sostituisce la query e cerca dalla prima pagina. La proposta sparisce se cambiano query, filtri, directory o snapshot. La digitazione continua a mostrare i suggerimenti di completamento separati.

## Sistema visivo e accessibilità

Segoe UI, spazio libero, bordi sottili e angoli morbidi. Palette chiara: avorio `#FAF9F6`, bianco, grafite `#252826`, verde `#315D50`, salvia `#DFEAE2`, lavanda `#E9E5F3`. Scura: `#191D1B`, superfici `#242A26`, testo `#EDF1ED`, accento `#ACD5BC`. Pastelli sulle superfici e match in grassetto, senza marcatori gialli pesanti.

Toggle a due segmenti per lingua, tema e ordine; icone per lingua/tema, menu campo arrotondato e formati multiselezione. Tab muove il focus, Spazio alterna, frecce scelgono il segmento. **Ctrl+L** ricerca, **Ctrl+O** cartella, **F5** sync.

Minimo **900×640 pixel logici**, focus visibile ed etichette accessibili. Verificare contrasto, DPI, scrolling e Narrator: test automatici/offscreen non sostituiscono Windows nativo o collaudo del pacchetto. Testi QML nel catalogo, eccetto marchio e TXT/MD/PDF; niente slogan negli asset traducibili.

[Asset locali e provenienza](../frontend/src/local_document_search_desktop/assets/README.md), rigenerabili con `scripts/dev/generate_luma_assets.py`. Il naming non implica verifica di disponibilità commerciale. [Evidenze desktop](V2_08_ACCEPTANCE.md#evidenze-desktop-precedenti-al-candidato).
