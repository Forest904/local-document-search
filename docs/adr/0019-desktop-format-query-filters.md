# ADR 0019 — Scorciatoie di formato nella query desktop

- **Stato:** Accepted, 2026-11-11.
- **Contesto:** i filtri formato sono disponibili nelle Impostazioni, ma l'utente può volerli indicare direttamente mentre cerca.
- **Decisione:** il desktop consuma `.txt`, `.md` e `.pdf` come elementi separati da spazi, fuori dalle virgolette e senza distinzione di maiuscole. Le estensioni sostituiscono i formati della sessione, con OR fra formati diversi. I token consumati spariscono dalla barra; se non restano termini, la home mostra il filtro senza avviare la ricerca. Nomi come `relazione.pdf`, frasi ed estensioni sconosciute restano query. Campo, cartella e ordine sono conservati. Il riepilogo offre solo un'icona per il reset completo delle opzioni; Impostazioni è raggiungibile dalla home.
- **Conseguenze:** la trasformazione avviene nel controller desktop prima di `SearchRequest` e usa il filtro `formats` esistente. CLI e grammatica backend restano invariate. La selezione dei suggerimenti segue lo stesso invio della barra.
- **Verifica:** scenari desktop aggiunti a [TEST_STRATEGY](../TEST_STRATEGY.md), test controller/QML e regressioni CLI.
