# Dominio: documenti, snapshot e risultati

**Implementato v1:** tipi e invarianti nel [modello storico](archive/v1/DOMAIN_MODEL.md). **Approvato v2:** estensioni qui descritte, ancora da implementare. [Codice di dominio](../backend/src/local_document_search/domain/).

Un file è un documento logico identificato dalla directory e dal percorso relativo preservato. Il catalogo lega `DocumentId`, formato, nome, fingerprint (`size_bytes`, `mtime_ns`) e testo estratto. Rename equivale a rimozione e aggiunta. Il manifest distingue INDEXED ed EXCLUDED; errori reader interrompono il candidato e non diventano esclusioni.

Lo snapshot immutabile comprende manifest, catalogo, due indici posizionali (`filename`, `content`) e un vocabolario ordinato secondario coerente per campo. V2-03 lo implementa come tupla delle chiavi dell'indice, ricostruita anche alla riapertura. Le posting hanno posizioni crescenti. Un termine del vocabolario deve corrispondere al medesimo termine nell'indice primario della stessa versione; pubblicazione/retention sono un'unica unità logica. Nessuna query legge un draft.

La query mantiene clausole AND e frasi consecutive. In BOTH ciascun campo deve soddisfare tutte le clausole. Un prefisso esplicito `termine*`, abilitato da opzione, opera sul vocabolario del campo; i suggerimenti non cambiano la query in corso. [Limiti V2-D03](adr/0010-v2-retrieval.md). Ranking e filtri non trasformano una non corrispondenza in match.

Risultato e anteprima portano lo `snapshot_id` necessario per recuperare testo, snippet ed evidenziazioni della stessa versione. Il testo canonico rimane unico: niente pagine PDF, coordinate o rendering. La rappresentazione dei segmenti evidenziati è [contratto logico](INTERFACE_CONTRACTS.md), da fissare tecnicamente in V2-05.

La CLI conserva i DTO e la semantica v1, senza nuovi default. Incompatibilità di schema/processing v2 richiede recovery o rebuild secondo la decisione [V2-D04](OPEN_DECISIONS.md); non è consentito cercare in dati interpretati con versione sbagliata.
