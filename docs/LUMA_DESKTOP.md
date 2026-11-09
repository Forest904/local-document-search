# Redesign Luma

Implementazione dell'8 novembre 2026, successiva alla verifica storica V2-06
e precedente a V2-08. Le prove del precedente installer non sono prove di questo
frontend. [Specifica UX](UX_WINDOWS.md).

## Modifiche

- Ingresso guidato con progresso reale, home di ricerca e risultati ad apertura
  diretta; nessuna sidebar o anteprima nel desktop.
- Impostazioni separate, filtri di sessione con riepilogo e reset, lingue e temi
  persistenti. Il backend dei dettagli resta disponibile per altri chiamanti.
- Componenti QML per pagine, marchio, ricerca, risultato, progresso, riepilogo,
  pulsanti e dialoghi; palette condivisa. Controller responsabile dei flussi.
- Asset originali vettoriali, PNG e ICO multirisoluzione; inventario delle
  risorse applicative e conservazione dei plugin SVG/ICO nel packaging.

## Polish successivo

L'icona desktop scelta dall'utente Ã¨ ora il simbolo nel marchio interno e la
sorgente dell'ICO. Suggerimenti, menu dei filtri e dialoghi hanno superfici e
testi esplicitamente coerenti con entrambi i temi. Le etichette delle
Impostazioni non dipendono piÃ¹ dal colore predefinito del controllo Qt; il
catalogo usa termini coerenti per la sincronizzazione anche negli errori.
I mockup con slogan incorporati rimangono riferimento visivo: il testo
traducibile Ã¨ reso dall'interfaccia.

La lista risultati usa righe piÃ¹ compatte: margini e distanze ridotti, titolo
da 18 px ed estratto limitato a due righe. La riga mantiene un'altezza minima
di 48 px per l'apertura con un clic e per il focus da tastiera.

## Ritocchi UI successivi

Sostituita la sorgente del marchio con il PNG trasparente fornito dall'utente,
rigenerando PNG nelle sette dimensioni e ICO. Impostazioni con etichette e
controlli affiancati; toggle a due segmenti per lingua, tema e ordinamento.
Le voci del menu campo hanno angoli arrotondati e rispettano il padding del popup.

Verifiche di questa modifica: suite frontend **40 passed**, inclusa regressione
su tastiera, selezione dei segmenti e reset. Catture native Windows a 900?640
pixel logici, IT/chiaro ed EN/scuro, controllate per layout, focus e logo;
PNG sorgente con canale alpha e angolo trasparente. Catture locali in
`build/ui-polish/`. Backend e installer non ricollaudati per questi ritocchi;
Narrator resta da verificare.

## Ritocchi UI successivi ? secondo intervento

Marchio statico con icona esistente e scritta grafica fornita dall'utente;
variante chiara per il tema scuro. Ricerca con lente nel campo su home e risultati;
selezionare un suggerimento completa la query e avvia ricerca e cambio pagina.
Impostazioni in due colonne dove utile: aspetto in cima con icone, campo e formati
affiancati, comandi dell'indice su una riga. Filtro sottocartella e recupero non
sono esposti, ma i contratti backend restano disponibili. Reset e pulizia sono
in fondo. Lo slogan della home ? rimosso.

Verifiche: test frontend e catture native Windows IT/chiaro ed EN/scuro a 900?640,
compresa la parte inferiore scorrevole delle Impostazioni, in `build/ui-polish-v2/`.
Narrator e pacchetto finale restano da verificare.

## Durata della ricerca

Il riepilogo dei risultati mostra il tempo trascorso dall'invio della ricerca
alla risposta pubblicata nella UI, inclusa l'attesa del worker. Il valore e
arrotondato a tre decimali, con virgola in italiano e punto in inglese.
Risposte obsolete non pubblicano tempi; una nuova query azzera la misura.

## Paginazione risultati

La ricerca desktop richiede 20 risultati per pagina. Le frecce, solo con piu
pagine, sono icone centrate ai lati del riepilogo localizzato della pagina e
dell'intervallo dei risultati. I testi visibili delle pagine QML usano il catalogo;
restano fissi solo il marchio e gli identificatori di formato TXT/MD/PDF.

## Evidenze e limiti

Verifiche sul sorgente (Windows 11 build 26200, Python 3.12.2, Qt 6.12.0):

- `backend/.venv/Scripts/python.exe -m pytest frontend/tests -q`: **39 passed**.
  Include avvio dell'entrypoint reale in processo separato, navigazione, filtri
  e reset, apertura singola da clic/Invio senza dettagli, focus e scorrimento
  tastiera nelle Impostazioni, estratti sicuri, contrasto e cataloghi IT/EN.
- Da `backend/`, `.venv/Scripts/python.exe -m pytest`: **384 passed, 6 skipped**.
  Corpus reale opt-in e casi giÃ  esclusi dalla suite ordinaria non sono PASS.
- `backend/.venv/Scripts/python.exe experiments/run_homework3.py`: **PASS**,
  dieci query e due regressioni con attesi coincidenti.
- Probe `run_v2_desktop.py` sul corpus sintetico small: **PASS** a scala 1 e 2,
  100 risultati e rispettivamente 6/8 cicli ricerca/apertura durante rebuild.
  L'opener del probe Ã¨ uno stub: il risultato non prova l'applicazione esterna
  e non Ã¨ un benchmark T08. Report in `experiments/results/luma-native*`.
- Catture Windows native di ingresso, caricamento, home, risultati e Impostazioni,
  incluse dimensione minima 900Ã—640, IT/EN, chiaro/scuro e DPI differenti.
  I font non sono verificabili dalle catture offscreen di questo ambiente:
  la verifica visiva usa il plugin Windows.
- Prova interattiva dal sorgente su profilo isolato e documenti sintetici:
  recupero automatico della home, ricerca, apertura TXT con un clic in Blocco
  note, filtro MD disattivato, ritorno ai risultati con query e riepilogo
  preservati. L'utente ha fermato Computer Use con Esc: nessun ulteriore input UI.
- Build locale finale di ZIP e installer completata. Lo ZIP contiene 300 file,
  compresi componenti QML e asset Luma; manifest con revisione
  `e103de792dfb2e841255a238082f2a06b2c67620` e working tree modificato.
  Installer: SHA-256
  `e3dfc34af1ee276b2cad4eec53f8d0d51ec96cae68bb85ccccd0c8c05818cdcf`.
  L'eseguibile dello ZIP estratto fuori dal repository Ã¨ rimasto avviato sia al
  primo uso, senza creare dati prima dell'informativa, sia riaprendo un catalogo
  v2 sintetico isolato. Nessun errore runtime Ã¨ stato emesso in queste prove.

Un'esecuzione dei tre test QML con `QT_QPA_PLATFORM=windows` ha riportato
`3 passed` e un avviso COM `0x8001010d` dal runtime nativo. Non viene considerata
una prova pulita di accessibilitÃ . La suite offscreen e i probe nativi sono
separati; Narrator e tabulazione manuale completa restano da verificare.

Il primo smoke dello standalone ha rilevato un argomento errato al controller
nell'entrypoint. Corretto nel sorgente e coperto dal nuovo test di avvio.
Il collaudo interattivo del pacchetto finale, incluso Narrator, resta da
completare insieme all'installazione su Windows pulito con account standard
distinto. Il manifest dirty non identifica una revisione di release pulita.
Non sono state modificate installazione o directory personali dell'utente.

Catture e report locali in `experiments/results/` e `build/`, fuori Git.
Queste verifiche non chiudono V2-08 e non trasferiscono al nuovo installer
l'approvazione del payload storico V2-07.

## Verifica successiva del candidato pulito

Il collaudo del candidato `3b78203` sul PC Windows pulito, restituito il
9 novembre 2026, ha verificato la UI Luma nei flussi principali con tastiera
e Narrator, nelle due lingue e nei temi, con DPI diversi e ricerca/apertura
sotto carico. L'utente non ha segnalato anomalie. Questa prova riguarda
l'installer identificato nel [registro V2-08](V2_08_ACCEPTANCE.md), non il
payload con working tree modificato descritto sopra. V2-06 e V2-08 sono
chiuse sul candidato verificato; le osservazioni storiche sul prototipo
restano valide per quel solo artefatto.
