# Verifica M4 — Ingestione multiformato

Data: 6 novembre 2026. Verifica locale su Windows, Python 3.12.2, ambiente `backend/.venv`.

## Risultato

M4 implementata e verificata localmente: CLI TXT/Markdown/PDF, discovery ricorsiva ordinata e reader tramite le porte esistenti. Nessuna modifica ad analyzer, evaluator, DTO o algoritmo di pubblicazione. `TextFileDiscovery` resta disponibile per il perimetro TXT; `DocumentFileDiscovery` e il dispatcher sono usati dalla composizione CLI.

Dipendenze verificate: markdown-it-py 4.2.0, mdurl 0.1.2, pypdf 7.0.0; pytest 8.3.5. Versioni runtime fissate in pyproject e transitive registrate in requirements-dev.

## Comandi ed esiti

Da `backend/`, usando `.venv/Scripts/python`:

| Comando | Esito |
|---|---|
| `python -m pip install -e ".[dev]"` | Riuscito |
| `python -m pip check` | Nessun requisito incompatibile |
| `python -m pytest tests/integration/test_multiformat.py tests/integration/test_txt_pipeline.py -q -rs` | 69 superati, 5 saltati |
| `python -m pytest -q -rs` | 234 superati, 5 saltati |

La suite completa include la CLI come processo reale, i confini degli import e il runner Homework 3 (dieci query e due regressioni TXT). Le misure storiche della relazione Homework non sono state sostituite.

## Copertura e decisioni

- OD-06/07: Markdown CommonMark con tabelle, UTF-8 rigoroso/BOM; titoli, liste, link, alt e codice inline. Esclusione di fenced/indented code, HTML grezzo e front matter iniziale chiuso. Front matter non chiuso trattato come Markdown; whitespace impedisce fusioni tra parole. I marcatori di enfasi non spezzano una parola.
- OD-05/21: PDF reali sintetici testuali multipagina, misti, con immagini, vuoti, whitespace, punteggiatura, password necessaria e corruzione. PDF cifrati apribili con password vuota sono leggibili senza prompt. Test di errore e MemoryError su una pagina successiva verificano la conservazione dello snapshot attivo.
- Pipeline: TXT/MD vuoti e PDF con sola punteggiatura ricercabili per nome; PDF senza testo solo nel manifest e assenti dai risultati. Query frase attraverso paragrafi/pagine; errori Markdown/PDF al primo build e con snapshot precedente senza pubblicazione parziale.
- Discovery: suffissi case-insensitive, percorsi e metadati preservati, ordinamento, compatibilità TXT, junction reali e reparse point simulati verificati per entrambe le discovery.

## Limiti

Cinque skip: quattro combinazioni symlink file/directory e discovery TXT/multiformato non consentite dal privilegio Windows (WinError 1314); un caso di nomi distinti solo per maiuscole non supportato dal filesystem. Il maggior numero di skip rispetto a M3 deriva dall'estensione dei test alla nuova discovery.

CI remota Windows/Linux non verificata. Nessun OCR, benchmark prestazionale o garanzia di fedeltà al layout PDF; frasi possono attraversare pagine e paragrafi. Fixture PDF minime e sintetiche, non un corpus esaustivo di PDF reali. Nessuna persistenza, sync, job asincrono o UI introdotta. Nessun commit o push eseguito.

Riferimenti tecnici consultati: [token e configurazione MarkdownIt](https://markdown-it-py.readthedocs.io/en/latest/using.html), [API PdfReader](https://pypdf.readthedocs.io/en/latest/modules/PdfReader.html). La semantica resta quella dell'[ADR 0007](adr/0007-analysis-and-readers.md) e della [specifica di analisi](INDEXING_AND_ANALYSIS.md).
