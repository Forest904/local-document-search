# ADR 0013 — Installer offline e diritti v2

- **Stato:** Accepted (direzione v2), 2026-11-07; V2-D07 definita l'8 novembre 2026.
- **Contesto:** v1 offre ZIP standalone per uso personale; Windows pulito/account standard non sono stati provati sul pacchetto finale.
- **Decisione:** prima distribuzione pubblica Windows 11 x64 con wizard offline per utente, senza elevazione, runtime Python/Qt e dipendenze incluse. Upgrade tramite installer completo. Disinstallazione conserva dati v2 salvo scelta esplicita; dati v1 e sorgenti intatti. Firma non obbligatoria per la prima release, avvisi osservati documentati.
- **Diritti:** intenzione del titolare: codice a diritti riservati, uso gratuito personale/studio, professionale soggetto ad autorizzazione. Termini completi [V2-D08](../OPEN_DECISIONS.md) prima del rilascio. Componenti Qt compatibili con percorso LGPL e verifica effettiva degli obblighi [V2-D09](../OPEN_DECISIONS.md).
- **V2-D07:** Inno Setup 6.7.3, EXE 0.2.0 per utente, wizard IT/EN, Start e desktop opzionale. Upgrade completo nella stessa installazione, reinstallazione consentita, downgrade bloccato. Disinstallazione conserva i dati per default; pulizia v2 solo su scelta esplicita. Applicazione da chiudere prima dell'operazione. Nessun aggiornamento online. Compilatore e payload sono registrati nel manifest della build.
- **Scelte rinviate:** termini definitivi [V2-D08](../OPEN_DECISIONS.md) e verifica legale del payload [V2-D09](../OPEN_DECISIONS.md).
- **Relazione con v1:** sostituisce per v2 lo ZIP come artefatto di rilascio dell'[ADR 0009](0009-desktop-runtime.md); non cambia il packaging storico v1.
- **Verifica:** V2-07/V2-08, T01 e T14–T19 nella [strategia](../TEST_STRATEGY.md). [Privacy](../SECURITY_AND_PRIVACY.md).
