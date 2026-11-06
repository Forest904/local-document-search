# Test backend

M1 include test eseguibili con `python -m pytest` da `backend/`, dopo l'installazione di sviluppo.

- `unit/`: modelli, snapshot, DTO e confini statici degli import, inclusi esempi di violazioni.
- `integration/`: solo composizione minima con sostituti locali; nessun adapter operativo verificato.
- `fixtures/`: riservata a file sintetici delle milestone successive. M1 costruisce i dati sintetici nei test.

Risultati in [Verifica M1](../../docs/M1_VERIFICATION.md); scenari futuri in [Test Strategy](../../docs/TEST_STRATEGY.md).
