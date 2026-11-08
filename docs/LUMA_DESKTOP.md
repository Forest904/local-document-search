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

L'icona desktop scelta dall'utente è ora il simbolo nel marchio interno e la
sorgente dell'ICO. Suggerimenti, menu dei filtri e dialoghi hanno superfici e
testi esplicitamente coerenti con entrambi i temi. Le etichette delle
Impostazioni non dipendono più dal colore predefinito del controllo Qt; il
catalogo usa termini coerenti per la sincronizzazione anche negli errori.
I mockup con slogan incorporati rimangono riferimento visivo: il testo
traducibile è reso dall'interfaccia.

La lista risultati usa righe più compatte: margini e distanze ridotti, titolo
da 18 px ed estratto limitato a due righe. La riga mantiene un'altezza minima
di 48 px per l'apertura con un clic e per il focus da tastiera.

## Evidenze e limiti

Verifiche sul sorgente (Windows 11 build 26200, Python 3.12.2, Qt 6.12.0):

- `backend/.venv/Scripts/python.exe -m pytest frontend/tests -q`: **39 passed**.
  Include avvio dell'entrypoint reale in processo separato, navigazione, filtri
  e reset, apertura singola da clic/Invio senza dettagli, focus e scorrimento
  tastiera nelle Impostazioni, estratti sicuri, contrasto e cataloghi IT/EN.
- Da `backend/`, `.venv/Scripts/python.exe -m pytest`: **384 passed, 6 skipped**.
  Corpus reale opt-in e casi già esclusi dalla suite ordinaria non sono PASS.
- `backend/.venv/Scripts/python.exe experiments/run_homework3.py`: **PASS**,
  dieci query e due regressioni con attesi coincidenti.
- Probe `run_v2_desktop.py` sul corpus sintetico small: **PASS** a scala 1 e 2,
  100 risultati e rispettivamente 6/8 cicli ricerca/apertura durante rebuild.
  L'opener del probe è uno stub: il risultato non prova l'applicazione esterna
  e non è un benchmark T08. Report in `experiments/results/luma-native*`.
- Catture Windows native di ingresso, caricamento, home, risultati e Impostazioni,
  incluse dimensione minima 900×640, IT/EN, chiaro/scuro e DPI differenti.
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
  L'eseguibile dello ZIP estratto fuori dal repository è rimasto avviato sia al
  primo uso, senza creare dati prima dell'informativa, sia riaprendo un catalogo
  v2 sintetico isolato. Nessun errore runtime è stato emesso in queste prove.

Un'esecuzione dei tre test QML con `QT_QPA_PLATFORM=windows` ha riportato
`3 passed` e un avviso COM `0x8001010d` dal runtime nativo. Non viene considerata
una prova pulita di accessibilità. La suite offscreen e i probe nativi sono
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
