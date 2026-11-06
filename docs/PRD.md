# PRD — Product Requirements Document

**Prodotto:** Local Document Search
**Versione specifica:** v1 (progettazione)
**Stato:** requisiti concordati; M1–M8 implementate, CLI TXT/Markdown/PDF operativa con snapshot in memoria; persistenza SQLite disponibile nel backend. Sync, lifecycle asincrono, ricerca concorrente e lock di sessione disponibili nel backend; desktop PySide6 implementato in un pacchetto separato; [evidenze M8](M8_VERIFICATION.md). Distribuzione standalone da verificare in M9.
**Target:** applicazione desktop locale Windows con backend Python indipendente dalla UI
**Relazione con il corso:** la CLI per TXT, due campi e phrase queries deve soddisfare l'Homework 3; PDF/Markdown e UI sono estensioni.

## 1. Problema e obiettivo

Permettere a un utente di scegliere una directory locale e ritrovare i documenti in base al **nome** e al **contenuto**, senza ricaricare o reindicizzare inutilmente i file a ogni avvio. La futura UI deve rimanere responsiva durante elaborazioni e sincronizzazioni.

Il motore IR deve essere implementato internamente: un indice invertito posizionale distinto per ciascuno dei campi `filename` e `content`, senza dipendenze da motori IR già pronti.

## 2. Percorsi utente

### Nuova directory

1. Utente sceglie una directory accessibile (una sola attiva).
2. Backend avvia la scansione **ricorsiva**, senza seguire symlink o junction.
3. UI mostra scansione indeterminata, poi lavorazione con statistiche e avanzamento pesato sui byte dei file elaborati.
4. Uno snapshot consistente viene persistito e attivato.
5. La barra di ricerca diventa disponibile.

### Apertura successiva

1. App recupera l'ultima directory e lo snapshot attivo.
2. La ricerca può usare lo snapshot precedente mentre il backend verifica i metadati dei file.
3. Se cambia qualcosa, una sincronizzazione incrementale costruisce un nuovo snapshot in background.
4. Lo snapshot vecchio resta disponibile fino al commit; in assenza di differenze non viene creata una versione nuova.

### Sync manuale

Il pulsante Sync avvia un controllo/sincronizzazione. Mentre il job è in corso visualizza uno spinner; al successo mostra brevemente un check e poi torna disponibile. Il ritardo del check è esclusivamente di UI, non uno stato persistente del dominio.

### Ricerca

La query interroga uno snapshot immutabile. I termini non quotati seguono AND; le virgolette denotano una frase. La ricerca predefinita su nome e contenuto trova un documento solo se **l'intera query** corrisponde almeno a uno dei due campi, senza distribuire i termini tra i campi. Un file eliminato o cambiato dopo l'ultimo snapshot può comparire ancora nei risultati; l'utente può premere Sync.

## 3. Requisiti funzionali

| ID | Requisito | Stato |
|---|---|---|
| FR-01 | Selezionare una sola directory attiva | Approvato |
| FR-02 | Discovery ricorsiva di `.txt`, `.md`, `.pdf`; non attraversare symlink/junction e non indicizzare symlink a file | Approvato |
| FR-03 | Un file = un documento logico; testo canonico unico, senza struttura pagine/segmenti | Approvato |
| FR-04 | Estrarre PDF con testo selezionabile; escludere interamente PDF senza testo; non eseguire OCR | Approvato |
| FR-05 | Estrarre Markdown come testo, escludendo i blocchi di codice | Approvato |
| FR-06 | Trattare i problemi di decodifica come errore, senza pubblicare uno snapshot incompleto | Approvato |
| FR-07 | Gestire file senza un limite applicativo di dimensione prefissato | Approvato; indici/draft in RAM, ResourceFailure esplicito |
| FR-08 | Analizzare nome e contenuto con analyzer distinti e indice posizionale proprietario per campo | Approvato |
| FR-09 | Supportare termini AND, phrase queries e ricerca per campo / entrambi | Approvato; clausole termini/frasi in AND |
| FR-10 | Persistenza degli snapshot e del testo estratto | Approvato |
| FR-11 | Individuare differenze con percorso relativo, dimensione e `mtime_ns`, senza hash del contenuto | Approvato |
| FR-12 | Sincronizzare all'apertura con directory salvata, su nuova selezione e su Sync manuale | Approvato |
| FR-13 | Rielaborare i soli file nuovi/modificati; eliminare riferimenti ai rimossi; riutilizzare quelli invariati | Approvato |
| FR-14 | Pubblicare nuovi snapshot soltanto dopo commit atomico riuscito | Approvato |
| FR-15 | Eseguire un solo job di indicizzazione alla volta; backend asincrono per UI, sincrono per CLI/test | Approvato |
| FR-16 | Mostrare fase, progresso e conteggi; scansione iniziale indeterminata, byte come misura indicativa successiva | Approvato |
| FR-17 | Consentire ricerca sul vecchio snapshot mentre si costruisce quello nuovo per la stessa cartella | Approvato |
| FR-18 | Preservare gli errori e le esclusioni nel report del job e nel manifest dove pertinente | Approvato |
| FR-19 | Consentire l'accesso al testo estratto per risultati e future anteprime | Approvato |
| FR-20 | Nessun controllo continuo dei file: cambiamenti dopo lo snapshot possono dare risultati obsoleti | Approvato |

## 4. Requisiti non funzionali

- **Local-first:** i dati restano sul dispositivo; nessuna dipendenza cloud progettata.
- **Consistenza:** manifest, catalogo, testo persistito e posting lists appartengono alla medesima versione attiva.
- **Isolamento:** il job in corso non altera lo snapshot interrogabile.
- **Responsività:** indicizzazione fuori dal thread UI; il progresso non dipende da widget Windows.
- **Manutenibilità:** moduli separati per Domain, Application, Infrastructure, Presentation; nessuna dipendenza del core da Windows, HTTP o librerie di parsing file.
- **Determinismo:** tokenizzazione, scansione e interrogazioni riproducibili a parità di input e versioni di elaborazione.
- **Riservatezza:** il testo estratto persistito può essere sensibile; storage, log e Git devono trattarlo come dato locale dell'utente.

## 5. Non-obiettivi v1

OCR; motore IR esterno; ricerca cloud; multiutente; più directory attive; crawler di rete; monitoraggio filesystem continuo; aggiornamenti di file durante il job (esclusi per ipotesi); pausa/cancel job; indicizzazione di pagine PDF come documenti separati; ranking e scoring; snippet/highlighting; full-text SQL; microservizi.

## 6. Criteri di accettazione

- La CLI indicizza una directory TXT e restituisce correttamente risultati per `nome`/`contenuto`, AND e phrase queries.
- TXT, Markdown e PDF testuali della stessa directory sono documenti ricercabili; i PDF privi di testo non lo sono.
- Dopo riavvio, lo snapshot valido viene caricato; un corpus invariato non genera un nuovo snapshot.
- Aggiunta, modifica ed eliminazione producono una versione corretta dell'indice; la versione precedente resta consultabile durante il build.
- Un errore di lettura, decodifica o commit non promuove un indice parziale.
- Progress e status sono leggibili indipendentemente dalla UI; un secondo trigger non crea un job concorrente.
- Lo snapshot persistito contiene anche il testo estratto dei documenti validi.
- Il test di circa dieci query e le misure richieste dall'Homework 3 vengono documentati, **senza inventare i risultati**.

## 7. Assunzioni e limiti dichiarati

- Il contenuto dei file **non cambia durante la scansione/indicizzazione**, per scelta di progetto.
- La rilevazione basata su dimensione e `mtime_ns` può perdere modifiche che mantengono entrambi i valori.
- L'ordine di lettura estratto dal PDF può essere imperfetto, specie con colonne e tabelle.
- Le phrase queries possono attraversare confini originari di pagine/paragrafi, poiché il CDM è testo unico.
- La percentuale basata sui byte dei file elaborati non è una previsione del tempo residuo.
- File estremamente grandi possono esaurire le risorse: il limite applicativo è assente ma le risorse fisiche no.

Vedere [OPEN_DECISIONS.md](OPEN_DECISIONS.md) per decisioni risolte, esclusioni e verifiche assegnate.

## 8. Baseline di consegna v1

Prima CLI TXT/Homework; poi altri reader, persistenza, sync e desktop.
V1 Windows 11 x64: PySide6 Qt Widgets in-process, ZIP senza Python preinstallato.
SQLite persiste snapshot completi; indici proprietari in RAM, niente full-text SQL.
Query miste come machine "deep learning", interamente soddisfatte da un campo.
Lista ordinata per percorso, testo completo e apertura file; Invio e pagine da 50.
ClearLocalData elimina soli dati applicativi a job fermo; storage per utente, nessuna cifratura aggiuntiva.
Attivo/precedente della sola directory corrente, nessuna cache multi-directory.
Dettagli in [Contratti](INTERFACE_CONTRACTS.md), [UX](UX_WINDOWS.md), [Roadmap](ROADMAP.md).
