# Decisioni aperte per v2

Questa tabella contiene **solo scelte da approvare**. Le decisioni già prese sono nel [PRD](PRD.md) e negli [ADR](adr/README.md); le decisioni v1 restano nell'[archivio](archive/v1/OPEN_DECISIONS.md). Nessuna riga autorizza a dichiarare implementata una funzione.

| ID | Decisione da prendere | Gate | Criterio per chiuderla |
|---|---|---|---|
| V2-D04 | Strategia fisica di storage e compatibilità fra versioni v2 | V2-04, prima delle modifiche persistenti | Recovery, attivazione, retention, memoria e tempi dimostrati sul target; v1 intatta |
| V2-D05 | Formula di rilevanza e spareggi; comportamento con BOTH e filtri | V2-05, prima del ranking | Casi ordinati attesi, determinismo e assenza di nuovi match documentati |
| V2-D06 | Lunghezza, selezione e limiti degli snippet; mappe di evidenziazione fra testo e token | V2-05, prima dell'API definitiva | Esempi su frasi, Unicode, PDF e testi lunghi; coerenza con snapshot verificabile |
| V2-D07 | Strumento e formato dell'installer offline; rilevamento upgrade e opzioni wizard | V2-07, prima della build finale | Prototipo Qt Quick distribuibile, installazione/update/uninstall per utente e inventario payload verificati |
| V2-D08 | Termini completi di uso gratuito personale/studio, autorizzazione professionale e diritti sul codice | V2-07, prima della pubblicazione | Testo definitivo approvato dal titolare, coerente con i diritti delle dipendenze |
| V2-D09 | Moduli Qt effettivi e adempimenti LGPL del payload compilato | V2-07, prima della pubblicazione | Inventario, avvisi/testi, sostituibilità delle librerie e procedura verificati sul pacchetto |

V2-D01 è risolta nell'[ADR 0014](adr/0014-v2-performance-budgets.md): metodo e budget approvati dopo tre cicli `PASS` sul target. Il backend v1 misurato non soddisfa ancora tutti i budget. [Misure e limiti](V2_02_BENCHMARK.md).

V2-D02 e V2-D03 sono risolte nell'[ADR 0010](adr/0010-v2-retrieval.md): confronto delle strutture sul vocabolario V2-02, tupla ordinata ricostruita alla riapertura, grammatica `termine*` opzionale e suggerimenti distinti. [Misure V2-03](V2_03_RETRIEVAL.md).

V2-D10–D13 sono risolte nel [corpus ibrido](TEST_DATASETS.md): fonti CC BY/CC BY-SA fissate nel manifest, schema JSON 1 con hash di versione, acquisizione con cache verificata, sintetici e ground truth reale completa. Le 36 query reali sono state preparate dai testi esportati secondo il prompt e ricontrollate su tutti i 12 documenti prima del confronto col motore; note di estrazione/tokenizzazione registrate nel JSON, T21 eseguito con esito PASS. [Evidenze e limiti](ROADMAP.md#v2-01--corpus-ibrido-e-validazione-funzionale). Non serve un nuovo ADR per il solo layout dei dati di test.

I dettagli interni che non cambiano requisiti, comportamento pubblico, contratti o dipendenze possono essere decisi durante l'implementazione. Un risultato di benchmark può cambiare la scelta di struttura, non l'obbligo di avere un indice secondario ordinato. [ADR ricerca](adr/0010-v2-retrieval.md), [storage](adr/0012-v2-lifecycle-storage.md), [distribuzione](adr/0013-v2-distribution.md).
