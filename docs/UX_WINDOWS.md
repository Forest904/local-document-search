# Esperienza desktop Luma â€” Windows 11

Direzione approvata l'8 novembre 2026: **Local Document Search** conserva il nome
applicazione; **Luma** identifica il motore. Qt Quick/QML e backend Python
in-process restano invariati. Sostituisce sidebar e anteprima dell'ADR 0011,
senza cambiare ricerca backend o CLI Homework.

## Percorsi

1. **Primo avvio:** informativa locale e Â«Accetta e scegli una cartellaÂ».
   Il backend si inizializza dopo l'accettazione; il selettore nativo si apre
   appena pronto. Annullarlo lascia disponibile la scelta cartella.
2. **Preparazione:** la stessa pagina mostra cartella, fase, conteggi e barra
   reale. Fasi senza percentuale indeterminate, nessuna ETA inventata.
   Consigli IT/EN ogni otto secondi spiegano prefissi, frasi, filtri e apertura;
   non prendono focus e non sono annunciati continuamente da Narrator.
3. **Completamento:** la home appare soltanto quando lo snapshot Ã¨ ricercabile.
   Fallimento e cancel senza snapshot lasciano retry, scelta cartella,
   ricostruzione e recupero. Errori e diagnostiche restano consultabili.
4. **Riapertura:** un catalogo v2 presente identifica una precedente
   inizializzazione; avviare automaticamente il recupero, poi aprire la home
   e sincronizzare in background. Sorgente assente: cercare sullo snapshot
   disponibile e spiegare che l'indice puÃ² essere obsoleto.
5. **Home:** marchio Luma, Â«Ritrova ciÃ² che cerchiÂ», barra, Cerca e Impostazioni.
   Invio esegue; digitare produce soltanto suggerimenti sullo snapshot corrente.
6. **Risultati:** barra in alto, conteggio, lista e pagine da 50. Percorso,
   formato, titolo ed estratto evidenziato provengono dallo snapshot. Clic o
   Invio sul risultato apre il file nell'app Windows associata. Nessuna anteprima
   interna nÃ© richiesta del testo completo per selezionare/aprire un risultato.
7. **Impostazioni:** Ricerca, Cartella e indice, Aspetto e lingua. Campo, formati,
   sottocartella e ordine sono qui; sync, rebuild, recupero, diagnostiche e
   pulizia mantengono i vincoli di lifecycle. Pulizia con conferma esplicita.
   Etichette e controlli sono affiancati in righe compatte. Lingua, tema e ordine
   usano toggle a due segmenti con alternative sempre visibili; campo usa un
   menu a voci arrotondate e formati mantiene la selezione multipla. Tab sposta
   il focus, Spazio alterna il toggle e le frecce sinistra/destra scelgono il segmento.

Filtri limitati alla sessione, azzerati al cambio directory/riavvio: entrambi i
campi, TXT/MD/PDF, nessuna sottocartella, rilevanza. Almeno un formato selezionato.
Home e risultati mostrano il riepilogo delle restrizioni e il reset. Cambiare
opzioni aggiorna una ricerca giÃ  eseguita dalla prima pagina. Nessuna sintassi
nuova come `type:pdf`. Il marchio torna alla home; Indietro dalle Impostazioni
recupera schermata e query. `Ctrl+L` focalizza la ricerca, `Ctrl+O` sceglie una
cartella, `F5` sincronizza. I comandi incompatibili con job/chiusura sono bloccati.
Risposte obsolete ignorate; operazioni pesanti nei worker.

## Sistema visivo e accessibilitÃ 

Segoe UI, spazio libero, componenti riusabili, bordi sottili e angoli morbidi.
Chiaro predefinito: avorio `#FAF9F6`, bianco, grafite `#252826`, verde
`#315D50`, salvia `#DFEAE2`, lavanda `#E9E5F3`. Scuro: fondo `#191D1B`,
superfici `#242A26`, testo `#EDF1ED`, accento `#ACD5BC`. Pastelli sulle
superfici e corrispondenze in grassetto, senza marcatori gialli pesanti.

IT/EN e tema persistono nel catalogo v2; la pulizia li azzera. Asset originali
SVG/PNG e ICO locali, rigenerabili con `scripts/dev/generate_luma_assets.py`.
Il naming non implica una verifica della disponibilitÃ  commerciale del marchio.

Tastiera, etichette accessibili, focus visibile e finestra minima 900Ã—640 pixel
logici sono obbligatori. Verificare contrasto, DPI, scorrimento e Narrator.
I test automatici non sostituiscono Narrator o il collaudo su Windows pulito.
[Verifiche Luma](LUMA_DESKTOP.md).
