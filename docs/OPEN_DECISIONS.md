# Decisioni aperte per v2

Questa tabella contiene **solo scelte da approvare**. Le decisioni già prese sono nel [PRD](PRD.md) e negli [ADR](adr/README.md); le decisioni v1 restano nell'[archivio](archive/v1/OPEN_DECISIONS.md). Nessuna riga autorizza a dichiarare implementata una funzione.

Nessuna decisione di questo registro è attualmente aperta.

V2-D07 è risolta nell'[ADR 0013](adr/0013-v2-distribution.md): Inno Setup 6.7.3 e installer EXE 0.2.0 per utente, wizard IT/EN, upgrade completo, reinstallazione consentita, downgrade bloccato e dati v2 conservati per default.

V2-D08 è risolta nell'[ADR 0013](adr/0013-v2-distribution.md) e nei [termini italiani](../scripts/package/TERMS-IT.txt), approvati nella sostanza dal titolare. Il payload collaudato contiene gli stessi testi IT/EN; [verifica](V2_07_INSTALLER.md).

V2-D09 è risolta: l'8 novembre 2026 Luca Foresti, titolare, ha approvato esplicitamente l'audit documentato del payload 0.2.0 dopo la presentazione di inventario, sorgenti e prova di sostituzione Qt. [Evidenze e limiti](V2_07_INSTALLER.md). L'approvazione non costituisce un parere legale indipendente.

V2-D05 e V2-D06 sono risolte nell'[ADR 0010](adr/0010-v2-retrieval.md): priorità al nome e frequenza delle posizioni distinte nei campi completi; una finestra di 240 caratteri e intervalli Unicode sul testo acquisito.

V2-D01 è risolta nell'[ADR 0014](adr/0014-v2-performance-budgets.md): metodo e budget approvati dopo tre cicli `PASS` sul target. Il backend v1 misurato non soddisfa ancora tutti i budget. [Misure e limiti](V2_02_BENCHMARK.md).

V2-D04 è risolta nell'[ADR 0012](adr/0012-v2-lifecycle-storage.md): storage SQLite v2 separato e compatto, versioni immutabili per documento, retention e recovery esplicito. Tre cicli target `PASS` e budget V2-D01 rispettati localmente. [Misure e limiti](V2_04_STORAGE.md).

V2-D02 e V2-D03 sono risolte nell'[ADR 0010](adr/0010-v2-retrieval.md): confronto delle strutture sul vocabolario V2-02, tupla ordinata ricostruita alla riapertura, grammatica `termine*` opzionale e suggerimenti distinti. [Misure V2-03](V2_03_RETRIEVAL.md).

V2-D10–D13 sono risolte nel [corpus ibrido](TEST_DATASETS.md): fonti CC BY/CC BY-SA fissate nel manifest, schema JSON 1 con hash di versione, acquisizione con cache verificata, sintetici e ground truth reale completa. Le 36 query reali sono state preparate dai testi esportati secondo il prompt e ricontrollate su tutti i 12 documenti prima del confronto col motore; note di estrazione/tokenizzazione registrate nel JSON, T21 eseguito con esito PASS. [Evidenze e limiti](ROADMAP.md#v2-01--corpus-ibrido-e-validazione-funzionale). Non serve un nuovo ADR per il solo layout dei dati di test.

I dettagli interni che non cambiano requisiti, comportamento pubblico, contratti o dipendenze possono essere decisi durante l'implementazione. Un risultato di benchmark può cambiare la scelta di struttura, non l'obbligo di avere un indice secondario ordinato. [ADR ricerca](adr/0010-v2-retrieval.md), [storage](adr/0012-v2-lifecycle-storage.md), [distribuzione](adr/0013-v2-distribution.md).
