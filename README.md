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

### Resumo executivo

Este repositório contém um agente Python pequeno e reproduzível de atendimento para o case de AI Engineer da Artefact. Ele responde mensagens em português brasileiro e usa tools limitadas para produtos, promoções, pedidos, preços e políticas da loja.

A implementação separa fatos determinísticos do comportamento de linguagem:

- PostgreSQL guarda os dados operacionais estruturados.
- PostgreSQL + pgvector está preparado para embeddings das políticas.
- Full-text no PostgreSQL é o fallback reproduzível padrão para o manual curto.
- Python controla preços, estoque, parcelas, privacidade e elegibilidade.
- O LLM pode selecionar tools e escrever a resposta, mas não pode gerar SQL nem inventar fatos.

O modo `mock` não exige credenciais e é o caminho reprodutível de avaliação. Ollama é um provider local opcional; OpenAI também é opcional quando configurado explicitamente.

### Execução rápida

```powershell
python -m unittest discover -s tests -v
python -m app.cli evaluate
python -m app.cli chat "Qual o status do pedido 1?"
```

O mock não exige Docker, chave de API ou LLM. A suíte validada possui 15 testes unitários e 13 casos determinísticos.

### PostgreSQL e ingestão das políticas

```powershell
pip install -e ".[api,postgres]"
docker compose up -d db
$env:DATABASE_URL="postgresql://empordb:empordb@localhost:5432/emporio"
$env:DATA_BACKEND="postgres"
$env:POLICY_RETRIEVAL="lexical"
python -m app.cli ingest
python -m app.cli ingest-policy-lexical
```

`ingest` importa os seis snapshots CSV para o PostgreSQL e normaliza valores opcionais, JSON, booleanos e totais de pedidos. Pode ser repetido com segurança porque reseta as tabelas importadas antes da carga.

`ingest-policy-lexical` extrai o PDF por página e armazena chunks com metadados de origem. A busca lexical padrão não exige download de modelo e retorna documento, página, seção e conteúdo. A ingestão semântica é opcional:

```powershell
$env:POLICY_RETRIEVAL="semantic"
python -m app.cli ingest-policy
```

Os PDFs e CSVs originais do desafio permanecem locais e são excluídos intencionalmente do Git. Um avaliador público deve fornecer os arquivos localmente ou usar um fixture seguro.

### API

```powershell
pip install -e ".[api]"
$env:LLM_PROVIDER="mock"
uvicorn app.api:app --reload
```

Endpoints:

- `GET /health` informa o backend de dados ativo.
- `POST /chat` aceita `message` e `order_verification` opcional.

Exemplo:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"Tem violão disponível até R$ 700?"}'
```

### LLM local opcional com Ollama

Ollama não é necessário para instalação ou avaliação. Ele está disponível por um profile opt-in do Docker Compose:

```powershell
docker compose --profile llm up -d
docker compose exec ollama ollama pull llama3.1:8b
$env:LLM_PROVIDER="ollama"
$env:LLM_MODEL="llama3.1:8b"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:DATA_BACKEND="postgres"
uvicorn app.api:app --reload
```

O modelo fica no volume persistente `ollama_data` e não é baixado automaticamente. Se Ollama não estiver disponível, use `LLM_PROVIDER=mock`; o agente determinístico continua funcionando. O adapter OpenAI opcional exige `OPENAI_API_KEY` somente quando `LLM_PROVIDER=openai`.

### Arquitetura e decisões

```text
Mensagem do cliente (PT-BR) -> roteador limitado de agente/tools
                                  |-> PostgreSQL SQL: catálogo, promoções, pedidos
                                  |-> busca lexical ou pgvector: políticas
                                  `-> resposta fundamentada em PT-BR
```

A consideração inicial foi Python/FastAPI com SQLite para dados estruturados e consulta direta do PDF curto. O candidato escolheu um único PostgreSQL com pgvector. A arquitetura híbrida mantém fatos operacionais determinísticos em SQL/Python e oferece um caminho semântico extensível para políticas.

O manual possui apenas oito páginas, então pgvector é demonstrativo, não uma necessidade de escala atual. Suas vantagens são uma infraestrutura extensível e metadados de origem inspecionáveis. Os custos são setup do banco, gerenciamento do modelo de embeddings, validação de dimensão e complexidade de ingestão. O fallback lexical é mantido para reprodutibilidade e precisão textual.

Consulte [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) e [docs/DECISION_LOG.md](docs/DECISION_LOG.md).

### Tools e segurança

Tools permitidas:

- `search_products`
- `get_product`
- `get_order_status`
- `price_quote`
- `search_policy`
- `get_store_info`

Proteções:

- nenhum SQL arbitrário gerado pelo modelo;
- queries PostgreSQL parametrizadas;
- estoque ativo exige status ativo e quantidade positiva;
- PIX não acumula com promoção ativa;
- moeda e parcelas são calculadas deterministicamente;
- consulta de pedido exige verificação demonstrativa correspondente;
- dados de contato de clientes não são retornados;
- prompt injection, limites de SQL e tentativas de PII são testados;
- a verificação demonstrativa não é autenticação de produção.

As respostas para clientes são PT-BR; identificadores, tools, APIs e documentação técnica são em inglês.

### Avaliação e exemplos

```powershell
python -m unittest discover -s tests -v
python -m app.cli evaluate
```

A suíte cobre roteamento, estoque, promoções, PIX, parcelas, evidência de políticas, solicitações fora do escopo, privacidade, limites de tools, prompt injection, tentativas de SQL arbitrário, proteção de PII e fluxo multi-tool. Os exemplos públicos estão em [examples/](examples/).

### Limitações

- Os CSVs originais de clientes e os PDFs da política são inputs locais do desafio e não estão no repositório público.
- A busca lexical é o caminho validado padrão. A ingestão semântica depende do download do modelo de embeddings configurado.
- Function calling com Ollama está implementado, mas exige um modelo Ollama local para um transcript LLM real.
- O mock valida roteamento e segurança deterministicamente; não mede qualidade linguística de LLM.
- Os CSVs são snapshots, não dados de comércio em tempo real.
- Produção exigiria sessões autenticadas, integração com comércio, logs redigidos, auditoria e monitoramento.

### Declaração de desenvolvimento assistido por IA

Codex e outros assistentes de IA ajudaram a elaborar código, testes, documentação e casos de avaliação. O candidato revisou a arquitetura e executou os comandos reportados. Nenhuma credencial, benchmark inventado ou histórico Git falsificado foi incluído.

### Rastreabilidade

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — limites e trade-offs do sistema.
- [docs/DECISION_LOG.md](docs/DECISION_LOG.md) — evolução de SQLite para PostgreSQL + pgvector.
- [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md) — execuções reais e limitações.
- [examples/](examples/) — exemplos públicos de interação.
