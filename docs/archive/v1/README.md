# Archivio v1 — riferimento storico

Le specifiche e le verifiche M0–M9 sono conservate nella revisione Git **`11c46d9bbcc46898af7781816bc515a51135aa7a`**, presente anche su GitHub. Questa revisione conserva i documenti: non identifica necessariamente i binari descritti nei singoli report, alcuni costruiti da working tree modificati.

Consulta l’[archivio completo a revisione fissa](https://github.com/Forest904/local-document-search/tree/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1), l’[indice originale](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/README.md) o il [report M9 integrale](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/M9_VERIFICATION.md). Le [specifiche correnti](../../README.md) sono autonome dall’archivio; gli [ADR](../../adr/README.md) e il materiale [Homework 3](../../homework-3/README.md) restano nel checkout.

## Recupero locale senza modificare il checkout

Da un clone che contiene la revisione, anche offline:

```powershell
git show 11c46d9bbcc46898af7781816bc515a51135aa7a:docs/archive/v1/M9_VERIFICATION.md
git archive --format=zip --output=../local-document-search-v1-docs.zip 11c46d9bbcc46898af7781816bc515a51135aa7a docs/archive/v1
```

Il secondo comando esporta tutti i documenti storici fuori dal repository; usare un nome di output libero per non sovrascrivere un’esportazione esistente. Se il clone è shallow e non contiene il commit, acquisirne prima la storia con `git fetch --unshallow origin` (richiede rete).

## Riepilogo M9

**M9 v1 resta parzialmente accettata.** Prevale l’aggiornamento del **7 novembre 2026** rispetto alle prove del primo ZIP del 6 novembre. Il pacchetto corrente di quel report è `LocalDocumentSearch-0.1.0-windows-x64.zip`, 86 file, SHA-256 `d045595d30e425567f5a06f8897082e3856f226e1c600537334fc07990cfe895`. Il manifest indica base `de93bab01f8f4af058c368190da040336ccf6a45` con working tree modificato; CRC, hash payload e sorgenti verificati, senza build da commit pulito.

Ambiente: Windows 11 build 26200, Python 3.12.2 x64, PySide6/Shiboken 6.12.0, Nuitka 4.1.1, MSVC 14.44.35207 (VS Build Tools 17.14.37411.7), Ryzen AI 7 350 e circa 32 GB RAM.

| Evidenza del 7 novembre | Esito e perimetro |
|---|---|
| Suite sorgente | Backend **317 passed, 5 skipped** (quattro symlink senza privilegi e un caso case-sensitive), frontend **25 passed**, script **17 passed**; pip check riuscito. |
| Homework | Dieci query e due regressioni superate su otto TXT sintetici. |
| ZIP sul PC di sviluppo | Profilo isolato, percorso con spazi/Unicode, ambiente Python/Qt ripulito: informativa, riapertura, no-change, ricerca/pagina 2 di 60 risultati, anteprima PDF, errore PDF corrotto con diagnostica sicura, correzione/retry, chiusura/restart. |
| Fault harness compilato separato | Arresti prima/dopo commit, SQLITE_FULL, MemoryError simulato, errore scrittura e tre terminazioni in competizione col commit (0/1/10 ms): snapshot vecchio o nuovo completo e lock riacquisibile. Non è il binario distribuito. |
| CI | Verde Windows/Ubuntu sulla sola baseline; modifiche collaudate non inviate alla CI, log dettagliati degli skip non accessibili anonimamente. |

Misura backend ripetuta senza build/test simultanei: corpus sintetico seed 20261106, **3.000 documenti** (1.000 per formato), **29.993.956 byte** di testo. Build **105,448 s**, riapertura **20,781 s**, no-change **0,205 s**, sync con un’aggiunta/modifica/rimozione **46,550 s**, picco working set **944,9 MiB**. Cache calda e riapertura nello stesso processo; nessun budget approvato, nessun confronto diretto con T08 v2. Tempi GUI includono attese dell’operatore e non sono benchmark.

Sul nuovo ZIP mancavano prove complete di cambio directory/rebuild, pulizia rifiutata durante job, PDF protetto/senza testo/misto, TXT/MD vuoti e ricerca/anteprima sotto carico. Windows pulito senza Python/tool e account standard distinto erano rinviati, quindi non verificati. I test sorgente e il collaudo del primo ZIP non certificano automaticamente quello successivo; i fault simulati non provano resistenza a perdita fisica di alimentazione o OOM non intercettabile.

Le lacune M9-G01–G07 sono state chiuse **sul candidato v2**, secondo la [matrice di accettazione](../../V2_08_ACCEPTANCE.md#matrice-dei-gate), senza cambiare l’esito storico v1. Corpus, ZIP e report grezzi restano fuori Git; il commit conserva la documentazione, non questi artefatti.
