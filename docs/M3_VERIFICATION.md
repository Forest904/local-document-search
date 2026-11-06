# Verifica M3 — CLI TXT e Homework 3

**Data:** 6 novembre 2026. **Esito:** verificata localmente con i limiti indicati; nessuna verifica CI remota o Linux effettuata in questa sessione.

## Ambiente e comandi

Windows 11 (10.0.26200), Python 3.12.2, ambiente virtuale `backend/.venv`, pytest 8.3.5. Nessuna nuova dipendenza runtime.

Dalla radice è stata eseguita l'installazione editable con `backend/.venv/Scripts/python -m pip install -e "./backend[dev]"`: riuscita. Equivalente, da `backend/` con ambiente attivo: `python -m pip install -e ".[dev]"`.

Da `backend/`:

```powershell
.venv/Scripts/python -m pytest -q -rs
.venv/Scripts/python -m pip check
```

**194 test superati, 3 saltati**, 197 raccolti (145 precedenti, 52 nuovi casi M3). `pip check`: nessun requisito incompatibile. Il primo controllo del piano con Python globale richiedeva `PYTHONPATH=src`; la verifica finale usa il package effettivamente installato nella venv e prova anche l'entry point installato.

## Evidenze

- Discovery TXT ordinata, suffissi case-insensitive, sottodirectory, basename duplicati, hard link e Unicode distinto.
- UTF-8 rigoroso, BOM rimosso, newline preservate, TXT vuoti, file scomparso e errori di scansione.
- Repository con candidato separato e attivazione soltanto dopo validazione; prove di fallimento in save, validate e activate, recupero dopo errore e mantenimento del precedente.
- Fallimento iniziale senza snapshot, encoding invalido, errore inatteso del reader e MemoryError simulato durante lettura/pubblicazione.
- Ricerca senza snapshot, query invalide, zero risultati, 53 risultati paginati, offset oltre il totale, acquisizione unica dello snapshot e nessuna rilettura dei sorgenti dopo il build.
- Sessione CLI come processo reale: prefissi, frasi/clausole miste, query invalida recuperabile, EOF, argomenti/path errati, build fallito, pagine complete. Ctrl+C verificato in-process tramite KeyboardInterrupt; non è stata iniettata una sequenza Ctrl+C in una console nativa.
- Confini architetturali AST e suite M1/M2 ancora verdi.

## Skip e limiti della piattaforma

Due test di symlink reali (file e directory) saltati: Windows restituisce WinError 1314, privilegio non disponibile. Il terzo skip riguarda `A.txt`/`a.txt`, non distinti su questo filesystem. Restano da eseguire su ambiente appropriato.

Junction reale Windows creata e verificata con successo; il test rimuove soltanto la junction e verifica che il target esista ancora. Hard link e nomi Unicode composti/decomposti verificati. Test simulati aggiuntivi verificano che entry symlink/reparse point vengano ignorate senza attraversamento, ma non sostituiscono i due test reali saltati.

Nessuna verifica di concorrenza, crash recovery, SQLite o packaging: non fanno parte di M3. La sessione è bloccante, con un writer; non dichiara thread safety o lock tra processi. I test non dimostrano comportamento su corpus modificati durante il build, esclusi per ipotesi.

## Esperimento Homework

Dalla radice:

```powershell
backend/.venv/Scripts/python experiments/run_homework3.py
```

Otto TXT sintetici, 192 byte, zero errori/esclusioni. Dieci query e due regressioni BOTH/clausole miste PASS. La misura registrata per la relazione è **0,016752 s** per il build iniziale completo, una singola esecuzione con cache OS non controllata. Non misura avvio processo o validazione iniziale dell'argomento; non è un benchmark di scala. L'output JSON e la trascrizione della misura sono conservati localmente in `experiments/results/m3.json` (ignorato da Git).

[Relazione compilata](homework-3/REPORT.md), [corpus/runner e attesi](../experiments/run_homework3.py). URL GitHub reale fornito dall'utente e verificato pubblico durante la pianificazione. La relazione non è stata inviata e le modifiche non sono state committate o pubblicate.
