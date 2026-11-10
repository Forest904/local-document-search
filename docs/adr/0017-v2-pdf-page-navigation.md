# ADR 0017 — Navigazione PDF alla pagina del match

- **Stato:** Accepted, 10 novembre 2026.
- **Contesto:** il PDF era ridotto a testo unico; l'apertura esterna non consentiva di raggiungere in modo affidabile la pagina della corrispondenza.
- **Decisione:** il testo canonico resta unico. Ogni PDF indicizzato conserva una sequenza immutabile di intervalli `[start,end)` sul testo canonico, uno per pagina fisica, incluse quelle vuote. La ricerca calcola la pagina della prima corrispondenza nel contenuto; se corrisponde solo il nome, usa la prima pagina. Un viewer Qt Quick PDF separato apre il sorgente locale alla pagina indicata dal risultato dello snapshot.
- **Compatibilità:** lo storage desktop passa allo schema 3 e richiede rebuild esplicito. CLI e storage v1 non cambiano. Nessuna migrazione automatica.
- **Limiti:** il file potrebbe essere cambiato dopo l'indicizzazione; non si controllano metadati all'apertura e il salto può risultare inesatto. Non sono disponibili coordinate o evidenziazione nel PDF. OCR e localizzazione geometrica restano estensioni future.
- **Alternative:** apertura esterna con parametri specifici del viewer, non uniforme; indice per pagina, incompatibile con l'attuale ricerca per documento.
- **Verifica:** T26–T27 in `TEST_STRATEGY.md` e rapporto `V2_11_PDF_PAGE_NAVIGATION.md`.

## Rifinitura del viewer

Il viewer conserva la query della risposta selezionata solo come proposta per «Trova nel PDF». La ricerca parte su Invio e usa il testo e le occorrenze del PDF aperto tramite Qt PDF; non modifica i risultati dello snapshot né interpreta AND, frasi o wildcard Luma. Un controllo locale del testo estraibile abilita il comando, lasciandolo indisponibile per documenti solo immagine. Il controllo usa un documento Qt separato in un worker e scarta risposte appartenenti a precedenti aperture.

Il componente QML Qt PDF è adattato localmente, con intestazione e licenza originali, per contenere pan, bounce e pinch. Non cambia lo schema, il backend o la CLI. L'evidenziazione geometrica dei match dello snapshot e l'OCR restano futuri; la ricerca manuale usa le evidenziazioni native Qt.
