# V2-12 — Reader TXT e Markdown

## Comportamento

Selezionare un risultato TXT/MD apre il file sorgente nel viewer interno in sola lettura. Il primo intervallo del contenuto indicizzato porta al frammento originale; un match solo nel nome apre dall'inizio. Per AND si usa la prima occorrenza di una clausola nel contenuto che soddisfa l'intera query. Markdown mantiene sintassi e righe del sorgente; parti escluse dall'indice rimangono visibili e ricercabili manualmente.

Ctrl+F apre una ricerca letterale nel file attuale, senza distinzione di maiuscole, con Invio/Shift+Invio e pulsanti per navigare ciclicamente. Escape chiude prima la ricerca, poi torna ai risultati. La ricerca manuale non modifica lo snapshot. L'a capo visivo è attivo inizialmente e può essere disattivato.

Il reader accetta UTF-8 strict, BOM iniziale, fino a 10 MiB, 100.000 righe fisiche e 100.000 caratteri per riga. Oltre soglia offre apertura esterna senza troncare. File con size o `mtime_ns` diversi dallo snapshot vengono mostrati dall'inizio con avviso, senza reinterpretare la query. Non rileva modifiche che preservano entrambi i metadati. Il documento aperto non si ricarica da solo.

## Implementazione e verifica

`SearchResult.text_target` contiene fingerprint e primo intervallo canonico. Una porta di lettura separata dalla ricerca prepara il sorgente soltanto all'apertura. Markdown usa i token CommonMark/tabelle della versione bloccata; coordinate sorgente Python vengono convertite in newline LF e offset UTF-16 per Qt. Mappa e buffer non vengono salvati nell'indice; lo schema desktop rimane 3.

Il `TextArea` Qt Quick riceve il contenuto in blocchi da 16.384 caratteri sul thread GUI; caricamento e ricerca manuale hanno worker separati e scartano risposte di aperture precedenti. Le prove del sorgente comprendono test backend T28 e test Qt offscreen T29. Il collaudo di installer offline, rendering Windows e Narrator resta distinto e non è attestato da questi test.

## Evidenze locali — 11 novembre 2026

- Suite backend completa: **433 passed, 6 skipped**. Dopo una piccola validazione del DTO, test mirati contratti/reader: **32 passed**.
- Suite frontend e script, escluso il test di installazione silenziosa: **118 passed, 1 deselected**. Il test escluso, eseguito in precedenza, è fallito perché l'installer ha rilevato l'applicazione aperta nella sessione Windows; non indica un errore del reader né costituisce un PASS dell'installer.
- Runner Homework 3: **PASS** su otto TXT sintetici, dieci query e due regressioni.
- Probe Qt offscreen in memoria, un ciclo con 10 MB e 100.000 righe: caricamento e popolamento progressivo dei numeri di riga in circa **7,6 s**; un evento oltre 50 ms, circa **59 ms** durante la preparazione iniziale. Non è una misura del pacchetto installato né un benchmark V2-02.
- Verifica statica del packaging: `build.py` include ricorsivamente i nuovi QML e `validate_payload` li richiede. Nessuna nuova dipendenza o modulo Qt richiesto.

Restano da provare installer completo offline su Windows pulito con account standard distinto, DPI/resa nativa e Narrator. I budget prestazionali già aperti nelle milestone precedenti non sono chiusi da queste evidenze.
