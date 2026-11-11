# ADR 0018 — Reader interno TXT e Markdown

- **Stato:** Accepted, 11 novembre 2026.
- **Contesto:** TXT e Markdown venivano aperti nell'app associata, mentre il PDF dispone già di un viewer interno. Il testo Markdown indicizzato differisce dal sorgente.
- **Decisione:** il desktop usa un `TextArea` Qt Quick in sola lettura per mostrare il sorgente UTF-8. `SearchResult.text_target` porta fingerprint e prima posizione nel testo canonico. Solo all'apertura una lettura limitata confronta i metadati e, per Markdown, traduce la posizione usando la provenienza dei token del parser bloccato. La ricerca manuale è letterale, separata dalla query Luma e dal backend IR.
- **Limiti:** 10 MiB, 100.000 righe e 100.000 caratteri per riga. Un file cambiato si apre dall'inizio con avviso. Un errore di mappatura non produce un salto approssimativo. Nessun watcher o hash; variazioni con size/mtime invariati possono sfuggire.
- **Compatibilità:** nessun nuovo dato persistito, schema o rebuild. La CLI e i reader di ingestione mantengono i loro contratti; il PDF resta invariato.
- **Alternative:** QPlainTextEdit richiede un host Widgets; WebEngine o editor di terzi aumenterebbero dipendenze e packaging.
- **Futuro:** il sorgente e i metadati di apertura restano distinti dal documento Qt per consentire in seguito editing, undo/redo, scrittura e conflitti esterni. Nessun aggiornamento automatico dell'indice è implicato.
- **Verifica:** T28/T29 in `TEST_STRATEGY.md` e rapporto `V2_12_TEXT_READER.md`.
