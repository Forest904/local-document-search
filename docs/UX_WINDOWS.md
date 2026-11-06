# UX — Windows Desktop (specifica, non mock implementato)

**Stato:** requisiti di interazione approvati; PySide6 Qt Widgets scelto, implementazione non iniziata.

## 1. Schermata iniziale

Quando non è selezionata una directory: selettore cartella e spiegazione dei formati supportati. Nessuna search bar attiva finché non esiste uno snapshot valido per la directory corrente.

## 2. Prima indicizzazione

1. Utente seleziona una cartella.
2. UI mostra una fase di **scansione indeterminata**, con conteggio dei file rilevati se disponibile.
3. Terminata la scansione, mostra `n file elaborati / n totali` e progresso pesato per dimensione dei file nuovi/modificati; fase e file corrente visibili.
4. Durante build e commit mostra stato esplicito anche se i byte dei file sono già stati completati.
5. Dopo commit la ricerca si attiva e il pulsante Sync può mostrare temporaneamente un check.

La percentuale sui byte **non** è una stima del tempo mancante. Un file PDF piccolo ma complesso può richiedere più tempo di un TXT grande.

## 3. Apertura successiva

Caricamento rapido dello snapshot persistito. Sync automatico in background. La ricerca rimane disponibile sullo snapshot precedente e la UI indica chiaramente `Aggiornamento in corso: i risultati potrebbero non riflettere le modifiche più recenti`.

Nessuna notifica di cambiamento istantanea: il backend confronta i file solo ai trigger stabiliti.

## 4. Ricerca

Search bar con selettore nome/contenuto/entrambi; Invio avvia la query, senza debounce o ricerca automatica. Clausole termini/frasi in AND, incluse combinazioni miste. Lista con filename, path relativo e formato, ordinata lessicograficamente per percorso preservato; pagine da 50. Selezione risultato apre testo completo mediante GetDocument(snapshot_id), senza snippet/highlighting.

Se il file fisico non esiste più, l'azione `Apri file` deve comunicare `File non disponibile` e proporre Sync; non altera silenziosamente lo snapshot.

## 5. Pulsante Sync

| Stato | Controllo |
|---|---|
| Idle | Icona Sync cliccabile |
| Running | Spinner, nuova richiesta non crea secondo job |
| Completed | Check temporaneo, poi ritorno a Sync |
| Failed | Icona errore, messaggio diagnostico e possibilità di riprovare |

Polling status ogni 200 ms; check di successo per 1,5 secondi, timer solo UI. Reused=true mantiene il job corrente senza simulare un nuovo avvio.

## 6. Stato directory e errori

- Nuova cartella durante un job: comando disabilitato e rifiutato anche lato backend.
- Sorgente precedente non disponibile (es. disco esterno): indicazione visibile, nessuna cancellazione automatica dello snapshot.
- Errore di lettura/encoding o commit: ultimo snapshot valido rimane utilizzabile se associato alla stessa cartella.
- Nessuna modifica: `Indice aggiornato`, senza nuova versione persistente.

## 7. Lifecycle, dati e distribuzione

UI/backend nello stesso processo, query e sync fuori dal thread UI. Risposte superate non sostituiscono richiesta/directory correnti.
Una sola istanza sullo storage; chiusura durante job mostra attesa e conclude dopo il job, senza cancel.
Snapshot incompatibile: ricerca disabilitata fino a rebuild riuscito. Versione rimossa: invitare a ripetere ricerca.
Prima di indicizzare informare che il testo viene salvato localmente anche se il sorgente diventa assente.
Pulizia con conferma, disabilitata durante job: elimina dati applicativi, non documenti; torna alla schermata iniziale.
Apertura file tramite adapter desktop del sistema operativo, senza shell costruita con input utente.
ZIP Windows 11 x64 pyside6-deploy standalone, senza Python preinstallato. Nessun frontend implementato nello scaffold.
