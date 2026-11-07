# ADR 0005 — Policy di discovery, estrazione e gestione errori

- **Status:** Accepted (design)
- **Context:** il corpus contiene TXT, Markdown e PDF testuali con qualità variabile e file potenzialmente molto grandi.
- **Decision:** scansione ricorsiva; ignorare symlink/junction di directory **e** symlink a file; Markdown senza blocchi di codice; PDF immagine senza testo esclusi completamente; nessun OCR; encoding invalido/reader inatteso → errore e nessun commit; nessun limite massimo di dimensione prefissato; assunzione di sorgenti statiche durante il job.
- **Alternatives considered:** OCR, indicizzare filename dei PDF immagine, seguire symlink, correggere caratteri invalidi automaticamente, imporre limite arbitrario sui file.
- **Consequences:** comportamento prevedibile e meno false assunzioni sui contenuti; scansioni parzialmente incomplete in presenza di errori, possibili ResourceFailure su file enormi; OCR escluso intenzionalmente.
- **v1 clarification (2026-11-06):** UTF-8 strict con BOM, markdown-it-py e pypdf con policy in [ADR 0007](0007-analysis-and-readers.md); memoria e ResourceFailure in [ADR 0008](0008-sqlite-snapshots.md).
- **Related:** [PRD](../archive/v1/PRD.md), [Indexing & Analysis](../archive/v1/INDEXING_AND_ANALYSIS.md).
