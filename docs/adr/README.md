# Decisioni architetturali

**Accepted** indica una decisione approvata, non una verifica eseguita. Lo [stato implementato](../README.md#stato-implementato) rimanda alle evidenze; gli ADR v1 restano validi dove non espressamente estesi o sostituiti.

| ADR | Decisione | Relazione con v2 |
|---|---|---|
| [0001](0001-modular-monolith.md) | Monolite modulare e porte | Conservata |
| [0002](0002-canonical-document.md) | Un file, testo canonico | Conservata |
| [0003](0003-positional-index.md) | Due indici posizionali | Estesa da 0010 |
| [0004](0004-snapshot-sync.md) | Snapshot e sync | Estesa da 0012 |
| [0005](0005-ingestion-policy.md) | Reader e discovery | Conservata |
| [0006](0006-application-interfaces.md) | Casi d’uso e porte | Estesa dai contratti v2 |
| [0007](0007-analysis-and-readers.md) | Analyzer e query | Estesa da 0010 |
| [0008](0008-sqlite-snapshots.md) | Storage v1 | Strategia v2 in 0012 |
| [0009](0009-desktop-runtime.md) | Qt Widgets e ZIP v1 | Sostituita per v2 da 0011/0013 |
| [0010](0010-v2-retrieval.md) | Vocabolario, prefissi, ranking, snippet | V2-D02/D03/D05/D06 |
| [0011](0011-v2-desktop.md) | Qt Quick e revisione Luma | Redesign approvato l’8 novembre 2026 |
| [0012](0012-v2-lifecycle-storage.md) | Lifecycle e isolamento dati | V2-D04 |
| [0013](0013-v2-distribution.md) | Installer e distribuzione | V2-D07/D08/D09 |
| [0014](0014-v2-performance-budgets.md) | Metodo e budget prestazionali | V2-D01 |
| [0015](0015-v2-suffix-wildcards.md) | Suffissi, vocabolario rovesciato e wildcard esplicite | V2-09 |
| [0016](0016-v2-spelling-correction.md) | Correzione proposta delle query tramite bigrammi e Levenshtein | V2-10 |
| [0017](0017-v2-pdf-page-navigation.md) | Mappa delle pagine PDF e viewer interno | V2-11 |
| [0018](0018-v2-text-reader.md) | Reader interno TXT/Markdown e salto al sorgente | V2-12 |
| [0019](0019-desktop-format-query-filters.md) | Scorciatoie di formato nella query desktop | Dopo V2-12 |

V2-D10–D13 (fonti, permessi, manifest, cache, sintetici e ground truth) sono risolte nella [specifica del corpus](../TEST_DATASETS.md). Non richiedono un ADR per il solo layout dei dati.

V2-D08: termini italiani approvati nella sostanza dal titolare Luca Foresti. V2-D09: audit del payload 0.2.0 approvato esplicitamente dal titolare l’8 novembre 2026 dopo inventario, sorgenti e prova di sostituzione Qt; [evidenze e limiti](../V2_07_INSTALLER.md). L’approvazione non è un parere legale indipendente.

## Decisioni aperte

Nessuna decisione attualmente aperta. Registrare qui nuove scelte che cambiano requisiti, comportamento pubblico, contratti o dipendenze, e approvarle prima del codice dipendente. Aggiornare ADR, specifiche e scenari interessati; i dettagli interni ordinari non richiedono un ADR. [registro storico v1](https://github.com/Forest904/local-document-search/blob/11c46d9bbcc46898af7781816bc515a51135aa7a/docs/archive/v1/OPEN_DECISIONS.md).

Per un nuovo ADR usare ID/titolo, stato e data, contesto, decisione, alternative, conseguenze, dettagli aperti e riferimenti a requisiti/contratti/scenari. Gli ADR 0001–0009 mantengono i riferimenti storici v1: le regole correnti complete sono nelle specifiche indicate nell’[indice](../README.md#riferimenti).

Revisione del 10 novembre 2026: [0012](0012-v2-lifecycle-storage.md) e [0013](0013-v2-distribution.md) adottano nome pubblico e percorsi senza etichetta generazionale, con reinstallazione pulita e nessuna migrazione dei dati precedenti.

Revisione successiva di [0013](0013-v2-distribution.md#revisione-approvata--percorso-e-wizard): percorso applicativo selezionabile alla prima installazione, mantenuto negli upgrade, riepilogo, retry con app aperta e avvio finale. Il collaudo del nuovo installer resta distinto dalle evidenze della release 0.2.0.
