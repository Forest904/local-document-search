# Decisioni aperte per v2

Questa tabella contiene **solo scelte da approvare**. Le decisioni già prese sono nel [PRD](PRD.md) e negli [ADR](adr/README.md); le decisioni v1 restano nell'[archivio](archive/v1/OPEN_DECISIONS.md). Nessuna riga autorizza a dichiarare implementata una funzione.

| ID | Decisione da prendere | Gate | Criterio per chiuderla |
|---|---|---|---|
| V2-D01 | Corpus prestazionale distinto dal corpus funzionale, hardware di riferimento, metodologia e budget numerici per p95 query, avvio, build, sync e picco RAM | V2-02, prima delle ottimizzazioni | Misure baseline ripetibili, soglie approvate e riportate nel piano di test |
| V2-D02 | Struttura dell'indice secondario ordinato, rappresentazione per campo e serializzazione | V2-03, prima del codice indice | Confronto di lookup, prefissi, costruzione, memoria e restart sul target; invarianti snapshot descritti |
| V2-D03 | Sintassi, limiti e paginazione dei prefissi; soglie e comportamento dei suggerimenti | V2-03, prima dei contratti definitivi | Esempi positivi/negativi, limiti di costo e casi di regressione CLI approvati |
| V2-D04 | Strategia fisica di storage e compatibilità fra versioni v2 | V2-04, prima delle modifiche persistenti | Recovery, attivazione, retention, memoria e tempi dimostrati sul target; v1 intatta |
| V2-D05 | Formula di rilevanza e spareggi; comportamento con BOTH e filtri | V2-05, prima del ranking | Casi ordinati attesi, determinismo e assenza di nuovi match documentati |
| V2-D06 | Lunghezza, selezione e limiti degli snippet; mappe di evidenziazione fra testo e token | V2-05, prima dell'API definitiva | Esempi su frasi, Unicode, PDF e testi lunghi; coerenza con snapshot verificabile |
| V2-D07 | Strumento e formato dell'installer offline; rilevamento upgrade e opzioni wizard | V2-07, prima della build finale | Prototipo Qt Quick distribuibile, installazione/update/uninstall per utente e inventario payload verificati |
| V2-D08 | Termini completi di uso gratuito personale/studio, autorizzazione professionale e diritti sul codice | V2-07, prima della pubblicazione | Testo definitivo approvato dal titolare, coerente con i diritti delle dipendenze |
| V2-D09 | Moduli Qt effettivi e adempimenti LGPL del payload compilato | V2-07, prima della pubblicazione | Inventario, avvisi/testi, sostituibilità delle librerie e procedura verificati sul pacchetto |
| V2-D10 | Fonti Internet, file e permessi di riuso per il nucleo reale IT/EN TXT/MD/PDF | V2-01, prima dell'acquisizione | Elenco approvato con provenienza e condizioni esplicite per ciascun documento |
| V2-D11 | Schema del manifest, percorsi e identificazione delle versioni del corpus/ground truth | V2-01, prima del generatore/downloader | Formato documentato, verificabile e collegato alle query attese |
| V2-D12 | Procedura di download, hash, cache e segnalazione dei file saltati | V2-01, prima della suite reale | Corpus incompleto non produce PASS; acquisizione e retry riproducibili |
| V2-D13 | Composizione dei sintetici riusando Homework/M9 e procedura Astra per le liste attese | V2-01, prima della validazione | Casi funzionali coperti, ground truth distinta dall'output del motore e controlli strutturali definiti |

Il [corpus ibrido](TEST_DATASETS.md) fissa i comportamenti approvati; V2-D10…D13 sono scelte di integrazione ancora aperte. Non serve un nuovo ADR per il solo layout dei dati di test.

I dettagli interni che non cambiano requisiti, comportamento pubblico, contratti o dipendenze possono essere decisi durante l'implementazione. Un risultato di benchmark può cambiare la scelta di struttura, non l'obbligo di avere un indice secondario ordinato. [ADR ricerca](adr/0010-v2-retrieval.md), [storage](adr/0012-v2-lifecycle-storage.md), [distribuzione](adr/0013-v2-distribution.md).
