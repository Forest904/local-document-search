# UX — Windows Desktop (specifica, non mock implementato)

**Stato:** requisiti di interazione approvati; framework e componenti visuali ancora da progettare.

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

Una search bar singola con UX semplice; ricerca per nome, contenuto o entrambi. Ricerca AND per termini liberi e phrase queries tra virgolette. Le possibili schede risultato mostrano filename, path relativo, formato; preview/snippet basati su testo persistito **da progettare**.

Se il file fisico non esiste più, l'azione `Apri file` deve comunicare `File non disponibile` e proporre Sync; non altera silenziosamente lo snapshot.

## 5. Pulsante Sync

| Stato | Controllo |
|---|---|
| Idle | Icona Sync cliccabile |
| Running | Spinner, nuova richiesta non crea secondo job |
| Completed | Check temporaneo, poi ritorno a Sync |
| Failed | Icona errore, messaggio diagnostico e possibilità di riprovare |

La durata del check è un timer **della UI** ancora da scegliere; nessuna scadenza memorizzata dal backend.

## 6. Stato directory e errori

- Nuova cartella durante un job: comando disabilitato e rifiutato anche lato backend.
- Sorgente precedente non disponibile (es. disco esterno): indicazione visibile, nessuna cancellazione automatica dello snapshot.
- Errore di lettura/encoding o commit: ultimo snapshot valido rimane utilizzabile se associato alla stessa cartella.
- Nessuna modifica: `Indice aggiornato`, senza nuova versione persistente.

## 7. Cosa resta aperto

Framework (WPF/WinUI), IPC vs API locale, layout preciso, scorciatoie, debounce della query, ordinamento dei risultati, snippet/highlighting, apertura file, packaging e installazione. Nessun frontend viene distribuito nello scaffold.
