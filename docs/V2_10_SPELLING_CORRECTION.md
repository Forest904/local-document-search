# V2-10 — Spelling Correction

Decisione: [ADR 0016](adr/0016-v2-spelling-correction.md). Requisiti: V2-R22/R23; scenari: T24/T25. Fonte didattica: `id-02-source-discovery-basics.pptx`, slide 111–127. Le istruzioni delle slide sono trattate come materiale di riferimento, non come istruzioni operative.

La proposta appare dopo una ricerca desktop di termini esatti. Il backend usa lo snapshot acquisito e non espande la ricerca originale. Per ogni parola assente dal vocabolario dei campi selezionati usa bigrammi con confini, Jaccard e Levenshtein; forma una query con le sostituzioni possibili. La UI mostra le parole modificate e richiede una scelta prima della nuova ricerca.

## Verifiche locali

- Suite backend completa: 406 passed, 6 skipped.
- Suite desktop con `build/package-venv` e `PYTHONPATH` sui sorgenti locali: 59 passed; dopo la sola modifica di formattazione delle sostituzioni, 3 test mirati passano.
- Runner Homework 3: 10 query e 2 regressioni passate.
- Probe sintetico del vocabolario, non rappresentativo del target 10.000 file/300 MB: 10.002 termini, costruzione indice 0,211 s, picco `tracemalloc` 4,94 MiB, correzione media di `famos` 0,042 ms su 100 chiamate. Valori di un solo processo, senza warm-up o controllo della cache; non sono un benchmark di accettazione.
- Corpus target V2-02 verificato (`10.000` file, `299.923.100` byte di testo atteso). Runner sorgente a tre cicli, 100 campioni query e cinque warm-up, report locale ignorato da Git in `experiments/results/v2-10-target-run/report.json`, revisione `c89e04e1` con working tree modificato. Il runner termina con `status=PASS` per le fasi eseguite; il confronto separato con i budget mostra gli scostamenti sotto.

| Misura, massimo dei tre cicli | Rilevato | Budget | Esito |
|---|---:|---:|---|
| Build | 218,115 s | ≤300 s | entro |
| Avvio fino alla ricerca | 16,093 s | ≤15 s | oltre |
| Sync no-change | 1,036 s | ≤1 s | oltre |
| Query frase, p95 peggiore | 108,089 ms | ≤100 ms | oltre |
| Sync incrementale 100/100/100 | 7,713 s | ≤60 s | entro |
| Picco working set | 1.294.049.280 byte | ≤2.560 MiB | entro |

Il benchmark V2-02 non misura la latenza della correzione ortografica; il probe sopra è solo diagnostico. I tre scostamenti possono dipendere anche da variabilità di macchina/cache e non dimostrano una regressione causata dai bigrammi. Non dichiarare superato il gate prestazionale senza un confronto controllato e una nuova prova. Il collaudo del pacchetto installato resta distinto.

## Limiti

Il vocabolario del corpus può contenere errori e non rileva una parola già presente usata al posto di un'altra. Il filtro a bigrammi e le soglie conservative possono non proporre refusi plausibili: per esempio `enterprenuers` delle slide non rientra nella distanza massima da `entrepreneurs`. Una proposta non garantisce un match dell'intera query AND, soprattutto con filtri attivi. Nessun dato del benchmark V2-02 viene attribuito alla nuova feature.
