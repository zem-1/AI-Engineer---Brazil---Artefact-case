# Evaluation results

## English

This file records executions, not expected behavior. Run `python -m unittest discover -s tests -v` and `python -m app.cli evaluate`. The deterministic suite contains ten cases covering routing, availability, promotions, privacy, policy evidence, unsupported requests, thresholds, stock, and a combined sequence. Results must be appended only after the command is actually run.

### 2026-11-03 — local execution

- `python -m unittest discover -s tests -v`: **5 passed**.
- `python -m app.cli evaluate`: **10 passed, 0 failed**.
- Execution mode: deterministic local mock; no LLM, Docker, or PostgreSQL was used.
- Limitation: the policy fixture is not yet produced by PDF ingestion, so this does not validate pgvector retrieval.
- PostgreSQL ingestion code is implemented but was not executed in this environment because Docker, psycopg, pypdf, and sentence-transformers were not installed.

The local mock does not call an LLM and does not claim semantic vector quality. Policy evidence is inspectable through `document`, `section`, and `page`; the current local fixture is a minimal verified subset until the Postgres ingestion path is run against the PDF. The multi-tool case is a routing smoke test, not proof of production authorization.

## Português (Brasil)

Este arquivo registra execuções reais, não resultados esperados. Rode `python -m unittest discover -s tests -v` e `python -m app.cli evaluate`. A suíte determinística contém dez casos de roteamento, disponibilidade, promoções, privacidade, evidência de política, solicitações fora do escopo, parcelas, estoque e sequência combinada. Só acrescente resultados depois de executar os comandos.

O mock local não chama um LLM e não afirma qualidade semântica de vetores. A evidência de política pode ser inspecionada por `document`, `section` e `page`; o fixture local é um subconjunto mínimo até a ingestão PostgreSQL ser executada com o PDF. O caso multi-tool é um smoke test de roteamento, não uma autorização de produção.
