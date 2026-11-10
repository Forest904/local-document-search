# Homework 3 — Relazione

## 1. Progetto e ambiente

- **Progetto:** Local Document Search, milestone M3.
- **Repository:** https://github.com/Forest904/local-document-search
- **Data della prova:** 6 novembre 2026.
- **Ambiente:** Windows-11-10.0.26200-SP0; Python 3.12.2; processore AMD64 Family 26 Model 96 Stepping 0, AuthenticAMD.
- **Versione corpus:** 1, definita in [run_homework3.py](../../experiments/run_homework3.py).
- **Ambito:** CLI TXT, motore locale proprietario, snapshot volatile. Nessuna dipendenza runtime esterna.

## 2. Architettura e analyzer

La discovery ricorsiva e il reader appartengono a infrastructure. Application orchestra il build completo e la ricerca attraverso porte; il dominio contiene analyzer, parser, builder e matching senza I/O. La CLI riceve una directory e interroga il medesimo backend destinato alla futura UI.

Il filename viene privato del solo suffisso finale supportato. L'analyzer separa CamelCase, acronimo/parola e lettere/cifre: `RomaTre.txt` diventa `roma`, `tre`; `Unicode2026.TXT` diventa `unicode`, `2026`. Questo rende ricercabili nomi compatti comuni nei documenti. Il contenuto non applica queste separazioni, per preservare parole e identificatori così come appaiono nel testo.

Entrambi gli analyzer applicano NFC, casefold e nuovamente NFC, preservando gli accenti. Sequenze di lettere/numeri e segni combinanti associati formano token; punteggiatura, apostrofi e underscore separano. Non si applicano stemming o rimozione di stop word: semantica semplice, indipendente dalla lingua, con tutte le posizioni disponibili per le frasi. `caffè` e `caffe` restano distinti.

Due indici separati memorizzano `termine → document_id → posizioni`, a partire da zero per ciascun campo. AND richiede tutti i termini nello stesso campo; una frase richiede posizioni consecutive e ordinate, comprese occorrenze ripetute. BOTH unisce i documenti che soddisfano l'intera query nel nome oppure nel contenuto, senza distribuire le clausole tra campi e senza duplicati. I risultati sono ordinati per percorso relativo, senza ranking.

Il reader decodifica UTF-8 rigoroso e rimuove un eventuale BOM iniziale, preservando le newline. I TXT vuoti restano ricercabili per nome. Errori di lettura o encoding impediscono l'attivazione del candidato; il precedente snapshot rimane intatto.

## 3. Corpus sintetico e misure

I file sono creati in una directory temporanea, con contenuti UTF-8 e newline LF deterministici; nessun dato personale. Il runner contiene gli attesi espliciti, ricavati leggendo questi testi e non dal motore.

| Percorso | Contenuto |
|---|---|
| `RomaTre.txt` | Roma Tre studia machine deep learning. data data. |
| `sub/RomaNote.txt` | Roma antica ospita tre scuole. machine learning. |
| `MachineLearning.txt` | modelli statistici |
| `machine.txt` | deep learning |
| `DataNotes.txt` | data mining data |
| `sub/DeepLearning.txt` | deep learning machine |
| `Empty.txt` | (vuoto) |
| `Unicode2026.TXT` | L'acqua e il caffè. |

| Misura | Risultato |
|---|---|
| TXT scoperti | 8 |
| TXT indicizzati | 8 |
| Esclusioni / errori | 0 / 0 |
| Byte sorgenti elaborati | 192 |
| Durata build iniziale completo | 0.016752 s |

La misura proviene dalla CLI reale: `perf_counter` copre discovery, estrazione, analisi, build, validazione e attivazione in memoria; esclude avvio del processo e validazione iniziale dell'argomento directory. È una singola esecuzione, con cache del sistema operativo non controllata. Non sono stati misurati separatamente i due campi, la RAM massima o i tempi delle query. Questo corpus minimo verifica correttezza, non prestazioni su larga scala.

## 4. Dieci query eseguite

| # | Query console | Attesi | Ottenuti | Esito |
|---|---|---|---|---|
| 1 | `nome roma` | `RomaTre.txt`, `sub/RomaNote.txt` | `RomaTre.txt`, `sub/RomaNote.txt` | PASS |
| 2 | `contenuto inesistente` | Nessuno | Nessuno | PASS |
| 3 | `contenuto machine learning` | `RomaTre.txt`, `sub/DeepLearning.txt`, `sub/RomaNote.txt` | `RomaTre.txt`, `sub/DeepLearning.txt`, `sub/RomaNote.txt` | PASS |
| 4 | `contenuto learning machine` | `RomaTre.txt`, `sub/DeepLearning.txt`, `sub/RomaNote.txt` | `RomaTre.txt`, `sub/DeepLearning.txt`, `sub/RomaNote.txt` | PASS |
| 5 | `contenuto "deep learning"` | `RomaTre.txt`, `machine.txt`, `sub/DeepLearning.txt` | `RomaTre.txt`, `machine.txt`, `sub/DeepLearning.txt` | PASS |
| 6 | `contenuto "roma tre"` | `RomaTre.txt` | `RomaTre.txt` | PASS |
| 7 | `nome "roma tre"` | `RomaTre.txt` | `RomaTre.txt` | PASS |
| 8 | `contenuto ROMA` | `RomaTre.txt`, `sub/RomaNote.txt` | `RomaTre.txt`, `sub/RomaNote.txt` | PASS |
| 9 | `contenuto "data data"` | `RomaTre.txt` | `RomaTre.txt` | PASS |
| 10 | `contenuto learning` | `RomaTre.txt`, `machine.txt`, `sub/DeepLearning.txt`, `sub/RomaNote.txt` | `RomaTre.txt`, `machine.txt`, `sub/DeepLearning.txt`, `sub/RomaNote.txt` | PASS |

Le query 3 e 4 dimostrano l'indipendenza dall'ordine nell'AND. La query 6 esclude `sub/RomaNote.txt`, dove `roma` e `tre` non sono adiacenti. La query 9 esclude `DataNotes.txt`, che contiene due `data` separati da `mining`.

Due regressioni aggiuntive, `entrambi machine "deep learning"` e `machine "deep learning"`, restituiscono entrambe soltanto `RomaTre.txt` e `sub/DeepLearning.txt` (PASS). `machine.txt` è correttamente escluso: il termine è nel nome e la frase nel contenuto, quindi nessun campo soddisfa da solo l'intera query.

## 5. Riproduzione

Dalla radice del repository, dopo l'installazione del backend:

```powershell
backend/.venv/Scripts/python experiments/run_homework3.py
```

Il runner crea il corpus temporaneo, avvia una sessione CLI come processo separato, invia le dieci query più le due regressioni e confronta percorsi e totali con gli attesi. Stampa JSON con ambiente, tempi e trascrizione completa; esce con codice 1 in caso di differenze. I tempi cambiano tra esecuzioni. L'output locale della misura riportata è in `experiments/results/m3.json`, ignorato da Git; contenuti sintetici, attesi e procedura sono versionati nel runner.

Per una sessione manuale, con ambiente virtuale attivo:

```powershell
local-document-search "C:\percorso\documenti"
```

## 6. Verifiche e limiti

Suite locale: **194 test superati, 3 saltati**, `pip check` riuscito. I tre skip riguardano symlink file/directory (privilegio Windows non disponibile) e due nomi distinti solo per case su filesystem non sensibile alle maiuscole. Sono passati i test con junction reale, hard link e nomi Unicode distinti, oltre alle prove simulate del filtro link/reparse point. Dettagli in [Verifica M3](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/M3_VERIFICATION.md).

Gli snapshot sono soltanto in RAM e vengono ricostruiti a ogni sessione. Ricerca e risultati non rileggono i sorgenti: modifiche successive al build restano invisibili fino alla nuova sessione. Persistenza, sync incrementale, Markdown/PDF e UI non sono implementati da M3. Il corpus è statico durante il build; non si proteggono modifiche concorrenti. La CI remota e Linux non sono stati verificati in questa esecuzione.

## 7. Risultato

La CLI soddisfa i requisiti TXT, due campi, AND e frasi, con dieci query verificate e misure reali. La relazione è pronta nel repository locale; commit, push e invio al docente non sono stati effettuati.
