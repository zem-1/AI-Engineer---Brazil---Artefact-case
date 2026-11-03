# Empório da Música — AI customer-support agent

## Executive summary

This repository contains a small, reproducible Python support agent for the Artefact AI Engineer case. It answers customer messages in Brazilian Portuguese and uses bounded tools for products, promotions, orders, pricing, and store policies.

The implementation separates deterministic business facts from language-model behavior:

- PostgreSQL stores structured operational data.
- PostgreSQL + pgvector is prepared for policy embeddings.
- PostgreSQL full-text retrieval is the reproducible default fallback for the short policy manual.
- Python owns pricing, stock, installment, privacy, and eligibility decisions.
- An LLM may select tools and write the final answer, but cannot generate SQL or invent business facts.

The default `mock` mode requires no credentials and is the reproducible evaluation path. Ollama is an optional local LLM provider; OpenAI is optional when explicitly configured.

## Quickstart

```powershell
python -m unittest discover -s tests -v
python -m app.cli evaluate
python -m app.cli chat "Qual o status do pedido 1?"
```

The local mock mode requires no Docker, API key, or LLM. The validated suite currently contains 15 unit tests and 13 deterministic evaluation cases.

## PostgreSQL and policy ingestion

```powershell
pip install -e ".[api,postgres]"
docker compose up -d db
$env:DATABASE_URL="postgresql://empordb:empordb@localhost:5432/emporio"
$env:DATA_BACKEND="postgres"
$env:POLICY_RETRIEVAL="lexical"
python -m app.cli ingest
python -m app.cli ingest-policy-lexical
```

`ingest` imports the six local CSV snapshots into PostgreSQL and normalizes optional values, JSON fields, booleans, and order totals. It can be repeated safely because it resets imported tables first.

`ingest-policy-lexical` extracts the policy PDF by page and stores source-aware chunks. The default lexical retrieval avoids requiring a model download and returns document, page, section, and content evidence. Semantic ingestion is optional:

```powershell
$env:POLICY_RETRIEVAL="semantic"
python -m app.cli ingest-policy
```

The original challenge PDFs and CSVs remain local and are intentionally excluded from Git. A public evaluator must provide source files locally or use a safe fixture.

## API

```powershell
pip install -e ".[api]"
$env:LLM_PROVIDER="mock"
uvicorn app.api:app --reload
```

Endpoints:

- `GET /health` reports the active data backend.
- `POST /chat` accepts `message` and optional `order_verification`.

Example:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"Tem violão disponível até R$ 700?"}'
```

## Optional local LLM with Ollama

Ollama is not required for installation or evaluation. It is available through an opt-in Docker Compose profile:

```powershell
docker compose --profile llm up -d
docker compose exec ollama ollama pull llama3.1:8b
$env:LLM_PROVIDER="ollama"
$env:LLM_MODEL="llama3.1:8b"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:DATA_BACKEND="postgres"
uvicorn app.api:app --reload
```

The model is stored in the persistent `ollama_data` volume and is not downloaded automatically. If Ollama is unavailable, use `LLM_PROVIDER=mock`; the deterministic agent remains functional. The optional OpenAI adapter requires `OPENAI_API_KEY` only when `LLM_PROVIDER=openai`.

## Architecture and decision rationale

```text
Customer message (PT-BR) -> bounded agent/tool router
                               |-> PostgreSQL SQL: catalog, promotions, orders
                               |-> lexical retrieval or pgvector: policies
                               `-> grounded PT-BR response
```

The initial consideration was Python/FastAPI with SQLite for structured data and direct lookup of the short policy PDF. The applicant explicitly chose one PostgreSQL database with pgvector. The hybrid architecture keeps operational facts deterministic in SQL/Python while providing an extensible semantic retrieval path for policies.

The manual is only eight pages, so pgvector is demonstrative rather than required by current scale. Its advantages are one extensible retrieval infrastructure and inspectable source metadata. Its trade-offs are database setup, embedding-model management, dimension validation, and ingestion complexity. Lexical fallback is retained for reproducibility and exact policy wording.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/DECISION_LOG.md](docs/DECISION_LOG.md).

## Bounded tools and safety

Allowed tools:

- `search_products`
- `get_product`
- `get_order_status`
- `price_quote`
- `search_policy`
- `get_store_info`

Safeguards:

- no model-generated arbitrary SQL;
- parameterized PostgreSQL queries;
- active stock requires active status and positive quantity;
- PIX is not stacked with an active promotion;
- currency and installment calculations are deterministic;
- order lookup requires a matching demo verification value;
- customer contact data is not returned;
- prompt injection, SQL-boundary, and PII attempts are tested;
- demo verification is not production authentication.

Customer-facing responses are PT-BR; identifiers, tools, APIs, and technical documentation are English.

## Evaluation and examples

```powershell
python -m unittest discover -s tests -v
python -m app.cli evaluate
```

The suite covers routing, stock, promotions, PIX stacking, installments, policy evidence, unsupported requests, privacy, tool boundaries, prompt injection, arbitrary SQL attempts, PII protection, and a multi-tool workflow. Public examples are in [examples/](examples/).

## Limitations

- Original customer CSVs and policy PDFs are local challenge inputs and are not public repository contents.
- Lexical policy retrieval is the validated default. Semantic ingestion depends on downloading the configured embedding model.
- Ollama tool calling is implemented but requires a local Ollama model for a real LLM transcript.
- Mock mode validates routing and safety deterministically; it does not measure LLM language quality.
- CSVs are snapshots, not live commerce data.
- Production would require authenticated sessions, upstream commerce integration, redacted logs, audit controls, and monitoring.

## AI-assisted development disclosure

Codex and other AI assistants helped draft implementation code, tests, documentation, and evaluation cases. The applicant reviewed the architecture and executed the reported commands. No credentials, fabricated benchmarks, or fabricated Git history are included.

## Traceability

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system boundaries and trade-offs.
- [docs/DECISION_LOG.md](docs/DECISION_LOG.md) — SQLite to PostgreSQL + pgvector evolution.
- [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md) — actual executions and limitations.
- [examples/](examples/) — public interaction examples.

## Português (Brasil)

### Resumo

Este repositório contém um agente Python pequeno e reproduzível de atendimento ao cliente para o case de AI Engineer da Artefact. O agente responde em português brasileiro e usa tools limitadas para produtos, promoções, pedidos, preços e políticas da loja.

A separação principal é entre fatos determinísticos e comportamento de linguagem: PostgreSQL guarda os dados operacionais; a recuperação de políticas usa full-text por padrão e possui caminho opcional com pgvector; Python controla preços, estoque, parcelas, privacidade e elegibilidade; o LLM apenas seleciona tools e redige a resposta.

### Execução rápida

```powershell
python -m unittest discover -s tests -v
python -m app.cli evaluate
python -m app.cli chat "Qual o status do pedido 1?"
```

O mock não exige Docker, chave de API ou LLM. Para PostgreSQL, instale `pip install -e ".[api,postgres]"`, rode `docker compose up -d db`, defina `DATABASE_URL`, e execute `python -m app.cli ingest` e `python -m app.cli ingest-policy-lexical`.

### Ollama opcional

Ollama não é obrigatório. Para usar um LLM local:

```powershell
docker compose --profile llm up -d
docker compose exec ollama ollama pull llama3.1:8b
$env:LLM_PROVIDER="ollama"
$env:LLM_MODEL="llama3.1:8b"
$env:OLLAMA_BASE_URL="http://localhost:11434"
```

O modelo fica no volume persistente `ollama_data` e não é baixado automaticamente. Sem Ollama, use `LLM_PROVIDER=mock`.

### Arquitetura e segurança

A consideração inicial foi SQLite com consulta direta do PDF curto. O candidato escolheu PostgreSQL + pgvector para manter dados estruturados em SQL e criar um caminho RAG extensível para políticas. Como o manual possui apenas oito páginas, o fallback lexical é o caminho validado e reproduzível.

Não há SQL arbitrário gerado pelo modelo. Estoque, preços, descontos, parcelas e autorização são determinísticos. Consultas de pedido exigem validação demonstrativa e não retornam PII.

### Avaliação e limitações

O projeto possui testes para roteamento, estoque, promoções, PIX, parcelas, políticas, privacidade, prompt injection, SQL arbitrário e PII. O modo mock valida segurança e roteamento, mas não mede qualidade linguística de LLM. Ollama e embeddings semânticos são opcionais; os resultados realmente executados estão em [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md).
