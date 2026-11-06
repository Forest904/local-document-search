# Verifica M9 — Distribuzione e accettazione locale

Data: 6 novembre 2026. Uso personale, nessuna pubblicazione e nessun commit automatico.
**Stato: implementazione e collaudo locale completati.**
La verifica Windows 11 senza Python o strumenti di sviluppo resta aperta per scelta
dell'utente: le evidenze sul PC attuale non soddisfano quel criterio di uscita.

## Implementazione

Packaging separato in `scripts/package/`, launcher del desktop esistente,
`pyside6-deploy` standalone, ambiente non editable e lock completo distinto da quello
di sviluppo. ZIP con runtime, istruzioni, licenze, manifest e report compilatore.
SHA256 esterno dello ZIP; hash dei singoli file, sorgenti e configurazione nel manifest.
Nessun cambiamento ai contratti applicativi, al motore o alla CLI Homework.

Python 3.12.2 x64; PySide6/Shiboken 6.12.0; Nuitka 4.1.1;
Visual Studio Build Tools 2022 17.14.37411.7, MSVC installato 14.44.35207
(selezione Nuitka `--msvc=14.3`, famiglia VS 2022). Windows 11 build 26200.
`pip check` riuscito nell'ambiente di packaging; installazione backend/frontend non editable.
Riproducibilità procedurale: nessuna dichiarazione di build identiche byte per byte.

## Test automatici

- Backend: `cd backend; .venv/Scripts/python -m pytest -q` → **314 passed, 5 skipped**.
- Frontend: `cd frontend; ../backend/.venv/Scripts/python -m pytest -q` → **24 passed**.
- Script: `backend/.venv/Scripts/python -m pytest scripts/tests -q` → **17 passed**,
  inclusi **7 casi M9**.
- I cinque skip backend sono i limiti di piattaforma già documentati in M7/M8;
  nessuna suite senza test viene considerata riuscita.
- Test M9: byte del corpus riproducibili e query attese sui reader reali, PDF testuale/vuoto/protetto,
  encoding invalido, ZIP e checksum, rifiuto di runtime mancante/database nello staging,
  pulizia confinata alla directory build, benchmark completo su corpus minimo con ripristino sorgenti,
  ambiente del processo compilato isolato senza modificare quello del chiamante.

## Corpus e prestazioni backend

Comandi dalla radice:

```powershell
backend/.venv/Scripts/python experiments/m9_corpus.py experiments/results/m9-corpus
backend/.venv/Scripts/python experiments/run_m9.py experiments/results/m9-corpus "$env:TEMP/LocalDocumentSearch-M9/backend-storage" experiments/results/m9-backend.json
```

Seed **20261106**, 3.000 documenti (1.000 TXT, 1.000 Markdown, 1.000 PDF),
32.020.700 byte sorgenti e **29.993.956 byte UTF-8 estratti**, zero esclusioni/errori.
PDF sintetici multipagina, Markdown con blocco di codice escluso, vocabolario sintetico
ristretto: non rappresentano PDF complessi, scansioni o corpus linguistici generici.
Hardware: AMD Ryzen AI 7 350 con Radeon 860M, 33.598.853.120 byte RAM fisica.

| Operazione | Misura |
|---|---:|
| Build iniziale completo | 178,731 s |
| Riapertura/caricamento | 24,486 s |
| Attesa residua sync automatico dopo riapertura | 0,323 s |
| Sync senza cambiamenti | 0,268 s |
| Sync: 1 aggiunto, 1 modificato, 1 rimosso, 2.998 invariati | 79,180 s |
| Byte processati nel sync incrementale | 39 |
| Picco working set del processo backend | 991.207.424 byte (945,3 MiB) |
| Picco pagefile/commit del processo | 994.832.384 byte |

| Query / campo | Risultati | Mediana di 5 query dopo warm-up |
|---|---:|---:|
| `nome solo` / filename | 3.000 | 20,452 ms |
| `corpus comune` / content | 3.000 | 19,826 ms |
| `"alfa beta"` / content | 1.500 | 17,421 ms |
| `corpus "alfa beta"` / both | 1.500 | 19,509 ms |
| `nome corpus` / both | 0 | 1,198 ms |
| `esclusomarkdown` / content | 0 | 0,218 ms |
| `selettore00000` / content | 1 | 0,394 ms |

Tutti gli elenchi dei risultati sono confrontati con gli attesi del manifest, non solo i conteggi.
Il sync no-change e il riavvio conservano lo snapshot; quello incrementale verifica i tre diff.
Le query richiedono fino a 3.000 risultati: non sono misure della sola pagina UI da 50.
Riapertura nello stesso processo, cache OS calda; tempi complessivi senza separazione
estrazione/analisi/commit. Picchi relativi all'intera esecuzione. Build Nuitka e suite di test
sono state eseguite contemporaneamente durante parte della misura: benchmark indicativo,
non isolato e non comparabile a una misura a macchina inattiva. Nessuna soglia approvata.
Il costo del sync è coerente con la serializzazione di snapshot completi: non equivale
a rileggere tutti i sorgenti. Nessuna ottimizzazione preventiva introdotta in M9.

## Pacchetto e accettazione

Artefatto: `dist/LocalDocumentSearch-0.1.0-windows-x64.zip`, **30.860.547 byte**, 87 file.
SHA256: `9f593ee628ccd36a43e80bc6ec579e16fc429a9b913051c6ab9771fd648e89ea`.
CRC dello ZIP e tutti gli hash dei file nel manifest verificati; gli hash dei sorgenti
di backend/frontend/packaging corrispondono al working tree collaudato.
Il manifest dichiara correttamente il working tree non ancora committato.

Build eseguita con `backend/.venv/Scripts/python scripts/package/build.py`.
Plugin Qt limitati a `platforms,styles`; inclusi Core/Gui/Widgets e QtNetwork richiesto
dalle dipendenze effettive, senza QtPdf/QtSvg/WebEngine. I PDF sono letti da pypdf.
Due correzioni nella preparazione: controllo del percorso Nuitka `qt-plugins` e opzioni
di esclusione plugin separate (Nuitka 4.1.1 non separa la lista delle esclusioni su virgola).
La build finale e il collaudo usano entrambe le correzioni.

ZIP estratto fuori dal repository in `%TEMP%/LocalDocumentSearch-M9/Pacchetto con spazi è/`.
Il launcher di prova usa PATH limitato a System32, rimuove le variabili Python/Qt e
imposta LOCALAPPDATA nella sola sessione figlia sotto `LocalDocumentSearch-M9/gui/appdata`.
Nessuna modifica alle variabili dell'account o ai dati personali.

| Scenario sul processo compilato | Esito osservato |
|---|---|
| Avvio e informativa, selezione cartella | PASS, nessun Python nel PATH del processo |
| Corpus piccolo, 20 TXT + 20 MD + 20 PDF | PASS, `corpus comune` restituisce 60 risultati |
| Paginazione | PASS, pagina 1 e pagina 2, Successiva disabilitata sull'ultima |
| Anteprima PDF | PASS, testo di `cartella00/NomeSolo00020.pdf` disponibile |
| Clausole miste `corpus "alfa beta"` | PASS, 30 risultati |
| Seconda istanza sullo stesso storage | PASS, `StorageFailure: Storage occupato o lock non acquisibile` |
| UTF-8 invalido durante sync | PASS, ExtractionFailure osservabile e snapshot precedente invariato |
| Correzione errore + add/modify/remove | PASS, nuovo snapshot con 60 documenti; `incrementale` trova i due documenti nuovi/modificati |
| Apri file | PASS, `aggiunto.txt` aperto in Notepad, testo sintetico corretto |
| Chiusura e riapertura senza cambiamenti | PASS, stesso snapshot attivo |
| Arresto forzato durante estrazione di 3.000 aggiunte | PASS, processo terminato; al riavvio lock disponibile e vecchio snapshot ricercabile |
| Ricerca durante sync dopo recovery | PASS, due risultati `incrementale` sullo snapshot precedente, UI risponde |
| Chiusura durante sync | PASS, messaggio di attesa, exit code 0 dopo commit; 3.060 documenti persistiti |
| Sorgente temporaneamente assente | PASS, SourceUnavailable, ricerca e anteprima persistite disponibili |
| Apri file assente | PASS, FileNotFoundError con invito a Sync |
| Pulizia dati a job fermo | PASS dopo rilascio di un handle esterno: nessuno snapshot, tabelle settings/selection/owned vuote, 3.060 sorgenti invariati byte per byte |

Durante il primo tentativo di pulizia, il processo di ispezione del collaudo teneva aperta
una connessione SQLite: `with sqlite3.connect(...)` termina la transazione ma non chiude
la connessione. Su Windows questo ha impedito l'eliminazione del file, producendo
`StorageFailure: Pulizia database da riprovare`. Rilasciato l'handle e riavviata l'app,
la sorgente ripristinata è stata ricostruita; la successiva pulizia è riuscita. È un errore
del controllo esterno, non una modifica necessaria al prodotto. I controlli finali usano
chiusura esplicita delle connessioni. Rimangono solo il database di controllo vuoto e il
file di lock, coerentemente con il lifecycle esistente. Nessun file personale coinvolto.

Il test di chiusura dopo recovery ha registrato un picco working set del processo compilato
di **1.176.772.608 byte (1.122,3 MiB)** e peak pagefile di 1.100.087.296 byte.
La sessione compilata sul corpus piccolo ha registrato 192.376.832 byte (183,5 MiB).
Campionamento ogni 100 ms: valori per sessione, non per fase. La durata di sessione include
attese dell'operatore e non viene presentata come tempo build/query; le misure temporali
controllate restano quelle del runner backend sopra riportate.

L'arresto forzato è stato effettuato durante estrazione, non durante il commit SQLite.
I fault test prima/durante/dopo commit restano quelli automatici M5–M7: non vengono
presentati come rieseguiti in ciascuna finestra del processo compilato.
Procedura ripetibile: [packaging](../scripts/package/README.md) e
[esperimenti](../experiments/README.md). Risultati grezzi e corpus sono esclusi da Git.
Controlli finali: `git diff --check` e link Markdown locali validi; nessun artefatto,
snapshot o corpus generato incluso fra le modifiche versionabili.

## Limiti di uscita

- Windows pulito senza Python/tool di sviluppo: **non verificato**.
- Account standard distinto e macchina esterna: **non verificati**.
- CI remota e distribuzione pubblica: **non eseguite**.
- Nessuna misura dimostra sicurezza contro esaurimento di memoria non intercettabile
  o interruzione fisica dell'alimentazione; valgono i limiti e i test di fault injection M5–M7.

## Aggiornamento corrente — 7 novembre 2026

La sezione precedente documenta l'artefatto storico. Dopo la correzione degli ID e del
report FR-18, l'artefatto corrente è `dist/LocalDocumentSearch-0.1.0-windows-x64.zip`,
SHA256 `d045595d30e425567f5a06f8897082e3856f226e1c600537334fc07990cfe895`.
Lo ZIP contiene 86 file; CRC, hash del payload e hash dei sorgenti del manifest coincidono.
Il manifest registra HEAD `de93bab01f8f4af058c368190da040336ccf6a45` con working
tree modificato. La build è identificabile tramite gli hash, ma non proviene da un commit pulito.
La toolchain è Python 3.12.2 x64, Nuitka 4.1.1, PySide6/Shiboken6 6.12.0 e MSVC
14.44.35207 (VS Build Tools 17.14.37411.7); percorso e hash del compilatore installato
sono nel manifest. Sono presenti QtNetwork e gli avvisi dei componenti effettivi.

Verifiche sorgente correnti: backend **317 passed, 5 skipped** (quattro casi symlink
senza privilegi Windows e un caso di nomi distinti solo per maiuscole su filesystem
insensibile), frontend **25 passed**, script **17 passed**; `pip check` riuscito.
Il runner Homework ha superato dieci query e due regressioni su otto TXT sintetici.
La CI verde su Windows e Ubuntu riguarda soltanto il commit baseline; i log dettagliati
degli skip non erano accessibili anonimamente. Queste modifiche non sono state inviate alla CI.

Misura backend ripetuta, senza build o suite simultanee, sul corpus M9 di 3.000 documenti
e 29.993.956 byte estraibili: build 105,448 s, riapertura 20,781 s, no-change 0,205 s,
incrementale 46,550 s; picco working set 990.765.056 byte (944,9 MiB). Riapertura a
cache calda, stessa metodologia e nessuna soglia prestazionale nuova. I risultati grezzi
restano fuori Git.

Il nuovo ZIP è stato estratto fuori repository in un percorso con spazi e Unicode, con
LOCALAPPDATA isolato e variabili Python/Qt pulite nel processo figlio. Sono stati osservati
informativa, apertura dello snapshot, sync no-change, ricerca e pagina 2 di 60 risultati,
anteprima PDF, errore su PDF corrotto con percorso relativo e motivo sicuro nei Dettagli
ultimo job, correzione del corpus e retry riuscito, chiusura e riavvio senza errori.
Picchi delle due sessioni GUI: 200.609.792 e 151.392.256 byte; le durate includono
attese dell'operatore e non sono benchmark.

L'harness compilato **separato dal prodotto distribuito**, costruito con Nuitka 4.1.1 e
`--msvc=14.3`, ha superato arresto prima e dopo commit, `SQLITE_FULL` su database
isolato, `MemoryError` simulato, errore di scrittura e tre terminazioni esterne in
competizione con il commit (ritardi 0, 1 e 10 ms). Al riavvio ogni prova ha trovato uno
snapshot completo vecchio o nuovo e il lock riacquisibile. Le terminazioni in competizione
non identificano il punto interno di flush; non dimostrano resistenza a perdita fisica di
alimentazione o OOM non intercettabile.

**Stato:** M9 resta parzialmente accettata. Sullo ZIP corrente non sono ancora documentati
il ciclo completo di cambio directory e rebuild, pulizia rifiutata durante job, la matrice
di PDF protetto/senza testo/misto e TXT/MD vuoti, né ricerca e anteprima sotto carico.
I test sorgente M5–M8 coprono parte di questi comportamenti ma non costituiscono una prova
del nuovo pacchetto. La prova Windows pulito/account standard distinto è stata rinviata
esplicitamente dall'utente alle versioni successive e resta non verificata.
