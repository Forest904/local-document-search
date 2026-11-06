# Test backend

Eseguire `python -m pytest` da `backend/`, dopo l'installazione di sviluppo.

- `unit/`: modelli, DTO, analyzer/parser, builder/matching, snapshot e confini statici degli import.
- `integration/`: composizione, pipeline TXT, contratti adapter, fault injection, CLI come processo reale e runner Homework.
- `fixtures/`: riservata a file sintetici; i test M3 creano i file nelle directory temporanee pytest. Il corpus Homework è definito in `experiments/run_homework3.py`.

[Evidenze M3 e skip](../../docs/M3_VERIFICATION.md); [strategia e scenari futuri](../../docs/TEST_STRATEGY.md). Nessun corpus personale.
