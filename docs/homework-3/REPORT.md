---
title: "Local Document Search"
subtitle: "Relazione Homework 3 ed evoluzione del progetto"
author: "Luca Foresti"
date: "10 novembre 2026"
lang: it-IT
---

# Obiettivo

L'Homework 3 richiede un programma che indicizzi i file TXT di una directory del laptop in due campi distinti, **nome** e **contenuto**, e risponda da console a ricerche per termini e frasi. Richiede inoltre circa dieci query di prova, il numero di file indicizzati, il tempo di indicizzazione e la motivazione degli analyzer. Il progetto è disponibile nel [repository Local Document Search](https://github.com/Forest904/local-document-search). La CLI resta utilizzabile autonomamente; la successiva applicazione desktop Luma usa lo stesso backend.

La prova didattica usa un corpus sintetico e riproducibile. Le misure del prodotto successivo sono riportate a parte perché usano un altro corpus, hardware e metodo. Il [runner Homework](https://github.com/Forest904/local-document-search/blob/main/experiments/run_homework3.py) contiene file, query e risultati attesi espliciti.

# Metodo di indicizzazione e ricerca

La discovery ricorsiva e i reader sono nell'infrastruttura; l'application orchestra indicizzazione e ricerca; il dominio implementa analyzer, parser e indici senza I/O. Ogni file è un documento. La CLI legge una directory e poi le query dalla console.

Per il **nome** si elimina il solo suffisso finale supportato. L'analyzer separa CamelCase e passaggi fra lettere e cifre: `RomaTre.txt` produce `roma`, `tre`; `Unicode2026.TXT` produce `unicode`, `2026`. Sono confini utili nei nomi compatti. Nel **contenuto** non si introducono queste separazioni, così parole e identificatori seguono il testo originale. Entrambi i campi applicano normalizzazione Unicode NFC, casefold e ancora NFC; punteggiatura, apostrofi e underscore separano i token, mentre gli accenti restano significativi. Non si applicano stemming né rimozione di stop word: `caffè` e `caffe` rimangono distinti e tutte le posizioni servono alle frasi.

Il motore mantiene due indici invertiti posizionali, uno per campo: `termine → documento → posizioni`. Una ricerca con più termini richiede la loro presenza **nello stesso campo**; una frase richiede posizioni consecutive nell'ordine indicato, anche per termini ripetuti. La modalità *entrambi* unisce i documenti che soddisfano l'intera query nel nome oppure nel contenuto: non combina metà query fra i campi. La CLI restituisce i percorsi relativi ordinati e non applica ranking. Il reader TXT usa UTF-8 rigoroso, rimuove l'eventuale BOM iniziale e lascia indicizzabili per nome anche i file vuoti.

# Prova Homework: corpus, tempo e query

Il runner crea otto TXT UTF-8 in una directory temporanea, con newline LF. Il corpus comprende nomi compatti, una sottocartella, un file vuoto e testo accentato. La legenda identifica i documenti nella tabella delle query; tutti i percorsi sono relativi alla directory temporanea.

| ID | Documento | Contenuto rilevante |
|:--|:--|:--|
| A | `RomaTre.txt` | Roma Tre studia machine deep learning. data data. |
| B | `sub/RomaNote.txt` | Roma antica ospita tre scuole. machine learning. |
| C | `MachineLearning.txt` | modelli statistici |
| D | `machine.txt` | deep learning |
| E | `DataNotes.txt` | data mining data |
| F | `sub/DeepLearning.txt` | deep learning machine |
| G | `Empty.txt` | vuoto |
| H | `Unicode2026.TXT` | L'acqua e il caffè. |

**Esecuzione del 10 novembre 2026:** Windows 11 build 26200, Python 3.12.2, AMD64 Family 26 Model 96 Stepping 0, revisione `8938d76`. La CLI ha scoperto e indicizzato **8 TXT**, senza esclusioni o errori, elaborando **192 byte sorgenti**. Il build iniziale completo è durato **0,012814 s**. Il timer della CLI comprende discovery, lettura, analisi, costruzione, validazione e attivazione in memoria; esclude l'avvio del processo. È una sola esecuzione con cache del sistema operativo non controllata, quindi non costituisce un benchmark di scala.

La tabella confronta i documenti attesi, determinati dal corpus, con quelli effettivamente restituiti. Gli ID seguono l'ordine dei percorsi stampati dalla CLI.

| # | Query console | Attesi | Ottenuti | Esito |
|--:|:--|:--|:--|:--|
| 1 | `nome roma` | A, B | A, B | PASS |
| 2 | `contenuto inesistente` | ∅ | ∅ | PASS |
| 3 | `contenuto machine learning` | A, F, B | A, F, B | PASS |
| 4 | `contenuto learning machine` | A, F, B | A, F, B | PASS |
| 5 | `contenuto "deep learning"` | A, D, F | A, D, F | PASS |
| 6 | `contenuto "roma tre"` | A | A | PASS |
| 7 | `nome "roma tre"` | A | A | PASS |
| 8 | `contenuto ROMA` | A, B | A, B | PASS |
| 9 | `contenuto "data data"` | A | A | PASS |
| 10 | `contenuto learning` | A, D, F, B | A, D, F, B | PASS |

Le query 3–4 confermano che l'AND non dipende dall'ordine dei termini. La 6 esclude B perché `roma` e `tre` non sono adiacenti nel testo; la 9 esclude E perché `mining` separa i due `data`. Sono passate anche due regressioni aggiuntive: `entrambi machine "deep learning"` e `machine "deep learning"` restituiscono entrambe **A, F**. D è escluso: `machine` è nel nome e `deep learning` nel contenuto, ma nessuno dei due campi soddisfa da solo l'intera query.

# Evoluzione fino a Luma v2

Le milestone successive hanno esteso i reader a **Markdown e PDF testuali** e aggiunto snapshot persistenti in SQLite, sincronizzazione incrementale e ricerca sul precedente snapshot durante l'aggiornamento. Il commit del nuovo snapshot è atomico; l'annullamento cooperativo prima del commit preserva quello attivo. Il diff si basa su percorso, dimensione e `mtime_ns`. Reader ed esclusioni rimangono distinti: un PDF senza testo utile può essere escluso, mentre un errore che impedisce di costruire un candidato completo lascia attivo lo snapshot precedente.

Il retrieval v2 mantiene i due indici posizionali e aggiunge un vocabolario ordinato per campo, prefissi espliciti e suggerimenti separati dalla query. Filtri per formato e cartella, ordinamento per rilevanza, snippet ed evidenziazione usano la versione acquisita del documento, senza rileggere il sorgente durante la ricerca. La CLI Homework conserva sintassi e ordine per percorso. La [roadmap v2](https://github.com/Forest904/local-document-search/blob/main/docs/ROADMAP.md) e i [contratti](https://github.com/Forest904/local-document-search/blob/main/docs/INTERFACE_CONTRACTS.md) descrivono questi comportamenti.

Luma offre l'interfaccia Windows in Qt Quick: selezione cartella, indicizzazione in background, risultati con estratti, anteprima e apertura del file; include italiano/inglese, temi e navigazione da tastiera. La versione **0.2.0** è stata distribuita tramite [installer offline per utente](https://github.com/Forest904/local-document-search/releases/tag/v0.2.0). Il [registro V2-08](https://github.com/Forest904/local-document-search/blob/main/docs/V2_08_ACCEPTANCE.md) distingue test automatici, benchmark del pacchetto e collaudo manuale su un PC pulito.

Sul **pacchetto 0.2.0**, il benchmark target su Windows 11, Ryzen AI 7 350, 32 GB RAM e SSD ha usato 10.000 file e 299.948.099 byte estratti, tre cicli, cinque warm-up e cento campioni per query. La tabella riporta i massimi del run completo; l'avvio termina quando la ricerca è disponibile e il sync incrementale modifica 100 file, ne aggiunge 100 e ne rimuove 100.

| Misura sul pacchetto | Massimo osservato |
|:--|--:|
| Build iniziale | 215,01 s |
| Avvio fino alla ricerca | 9,53 s |
| Sync senza modifiche | 0,781 s |
| Sync incrementale 100/100/100 | 5,04 s |
| Query p95 | 97,52 ms |
| Working set | 1.359,1 MiB |

La cache OS non è stata svuotata. Un ciclo di un run precedente, poi interrotto, aveva raggiunto **103,48 ms** di p95 per una frase, oltre la soglia di 100 ms: segnala variabilità vicina al limite. Il run finale completo rispetta i budget approvati, ma quell'osservazione resta rilevante per interpretarli. Il PC pulito ha verificato i flussi offline e accessibili, ma non ne ha misurato i tempi.

La verifica della release ha combinato suite sul sorgente (**461 test superati, 6 saltati**), CI Windows e Ubuntu, corpus reale opt-in (**6 test superati**) e collaudo dell'installer su Windows offline con account standard distinto. Le prove manuali hanno coperto i reader, il cambio directory, il recupero dopo errore, l'apertura dei file, lingua, temi, tastiera e Narrator. Il collaudo e i tempi del benchmark provengono da macchine diverse: il secondo non rappresenta una misura del PC pulito. Il candidato verificato corrisponde alla release pubblicata 0.2.0, identificata nel registro con commit e SHA-256 dell'installer.

# Riproduzione e limiti

La scelta di mantenere due campi separati rende esplicita la semantica della ricerca: un documento può comparire perché soddisfa la query nel nome oppure nel testo, senza produrre un falso positivo sommando evidenze eterogenee. Le posizioni nell'indice consentono di controllare l'adiacenza delle parole senza scorrere ogni documento a ogni query. La normalizzazione Unicode è condivisa fra indicizzazione e ricerca; la separazione ulteriore nel solo nome risponde invece alla struttura tipica dei nomi di file. L'assenza di stemming e stop word evita trasformazioni dipendenti dalla lingua e conserva esempi come `data data`, utili per verificare le frasi.

Il corpus Homework è intenzionalmente piccolo: gli attesi possono essere controllati leggendo gli otto testi e il tempo di build resta facile da ripetere. La sua durata, nell'ordine dei millisecondi, dipende sensibilmente dalla macchina e dalla cache. Per valutare la scala del prodotto sono stati quindi usati un carico separato, metriche dichiarate e tre cicli sul pacchetto. Anche lì il p95 vicino alla soglia invita a leggere intervallo e condizioni della prova, non soltanto un numero isolato. La suite automatica controlla invarianti e regressioni; il collaudo manuale verifica che installer e interfaccia funzionino nel contesto d'uso previsto. Sono evidenze complementari.

La persistenza v2 introduce un compromesso: riaprire e sincronizzare rapidamente un indice completo richiede storage e gestione delle versioni, ma permette di mantenere visibili risultati coerenti mentre un nuovo candidato viene costruito. I risultati si riferiscono sempre a uno snapshot acquisito; una modifica sul disco diventa visibile dopo il sync. Il confronto con i metadati è economico, ma non rileva modifiche che lasciano identici dimensione e timestamp. Nelle anteprime PDF si vede il testo estratto, senza riprodurre la disposizione grafica delle pagine. Questi limiti descrivono il comportamento effettivo del prodotto.

Dalla radice del repository, dopo `python -m pip install -e ".[dev]"` nella directory `backend/`, eseguire:

```powershell
backend/.venv/Scripts/python.exe experiments/run_homework3.py
```

Il runner avvia la CLI in un processo separato, confronta percorsi e totali con gli attesi, stampa JSON con ambiente e trascrizione e restituisce codice 1 se una prova fallisce. Il corpus di otto TXT verifica la correttezza, ma non misura la RAM o i tempi di query né rappresenta la varietà dei documenti reali. Per il prodotto v2 rimangono esclusi OCR, ricerca semantica e sorveglianza continua; modifiche che conservano dimensione e timestamp possono sfuggire al sync. Le frasi nei PDF operano sul testo estratto, il cui ordine può differire dal layout visivo.

La CLI soddisfa i requisiti didattici con due indici, analyzer motivati e dieci query verificate. L'evoluzione v2 mostra come lo stesso motore sia stato portato a un'applicazione locale distribuibile, mantenendo verifiche e misure riferite ai rispettivi artefatti.
