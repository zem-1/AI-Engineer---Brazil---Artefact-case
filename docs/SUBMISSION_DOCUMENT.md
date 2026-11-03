# Artefact AI Engineer — Written Case Submission

## English

### Project

**Empório da Música — AI customer-support agent**

This project is a small, reproducible Python support agent for a fictional Brazilian musical-instrument store. It responds in Brazilian Portuguese and grounds operational answers in catalog/order data and store-policy evidence.

### Architecture

The agent uses bounded tools over one PostgreSQL database. SQL handles products, categories, promotions, orders, and order items. Policy text is extracted into page-aware chunks and retrieved through PostgreSQL full-text search by default, with an optional pgvector embedding path. Python owns pricing, stock, installment, eligibility, and privacy decisions. An optional LLM selects tools and drafts answers; it cannot generate SQL or invent business facts.

The initial consideration was SQLite plus direct lookup of the short policy PDF. The applicant chose PostgreSQL + pgvector to demonstrate an extensible RAG path without introducing a second vector service. The policy manual is only eight pages, so lexical retrieval is the validated reproducible default and pgvector is an extensible demonstrator. The trade-offs are setup, embedding-model management, dimension validation, and ingestion complexity.

### Reproduction

```powershell
pip install -e ".[api,postgres]"
docker compose up -d db
$env:DATABASE_URL="postgresql://empordb:empordb@localhost:5432/emporio"
python -m app.cli ingest
python -m app.cli ingest-policy-lexical
python -m unittest discover -s tests -v
python -m app.cli evaluate
```

Ollama is optional:

```powershell
docker compose --profile llm up -d
docker compose exec ollama ollama pull llama3.1:8b
$env:LLM_PROVIDER="ollama"
$env:LLM_MODEL="llama3.1:8b"
$env:OLLAMA_BASE_URL="http://localhost:11434"
```

### Safety and evaluation

The allowed tools are product search, product lookup, order status, price quote, policy search, and store information. Tests cover active stock, discount stacking, installment thresholds, privacy gates, unsupported requests, prompt injection, arbitrary SQL attempts, PII protection, source metadata, and a multi-tool workflow. The local validation executed 15 unit tests and 13 deterministic evaluation cases. PostgreSQL CSV ingestion was executed twice with identical counts, and lexical policy ingestion produced 8 chunks.

The original customer CSVs and policy PDF remain local and are excluded from the public repository. Demo identity verification is not production authentication. CSVs are snapshots, not live commerce data.

### AI assistance disclosure

Codex and other AI assistants helped draft implementation code, tests, documentation, and evaluation cases. The applicant reviewed the architecture and executed the reported commands. No credentials, fabricated benchmarks, or fabricated Git history are included.

## Português (Brasil)

### Projeto

**Empório da Música — agente de atendimento com IA**

Este projeto é um agente Python pequeno e reproduzível para uma loja brasileira fictícia de instrumentos musicais. Ele responde em português brasileiro e fundamenta as respostas em dados de catálogo/pedidos e evidências das políticas da loja.

### Arquitetura

O agente usa tools limitadas sobre um único PostgreSQL. SQL trata produtos, categorias, promoções, pedidos e itens de pedido. O texto das políticas é extraído em chunks com páginas e recuperado por full-text no PostgreSQL por padrão, com caminho opcional de embeddings no pgvector. Python controla preços, estoque, parcelas, elegibilidade e privacidade. Um LLM opcional seleciona tools e redige respostas; não pode gerar SQL nem inventar fatos.

A consideração inicial foi SQLite com consulta direta do PDF curto. O candidato escolheu PostgreSQL + pgvector para demonstrar um caminho RAG extensível sem adicionar um segundo serviço vetorial. Como o manual tem apenas oito páginas, a busca lexical é o padrão validado e reproduzível; pgvector é um demonstrador extensível. Os custos são setup, gerenciamento do modelo de embeddings, validação de dimensão e ingestão.

### Reprodução

Os comandos da seção `English` executam a instalação, iniciam PostgreSQL, importam os CSVs, ingerem a política e rodam os testes. Ollama é opcional e pode ser iniciado pelo profile Docker `llm`; o mock continua sendo o caminho padrão sem chave ou modelo local.

### Segurança e avaliação

As tools permitidas são busca de produtos, consulta de produto, status de pedido, cotação, busca de política e informações da loja. Os testes cobrem estoque ativo, acúmulo de descontos, parcelas, privacidade, solicitações fora do escopo, prompt injection, SQL arbitrário, PII, metadados de fonte e fluxo multi-tool. A validação local executou 15 testes unitários e 13 casos determinísticos. A ingestão dos CSVs foi executada duas vezes com contagens idênticas, e a ingestão lexical gerou 8 chunks.

Os CSVs originais de clientes e o PDF da política permanecem locais e estão fora do repositório público. A verificação demonstrativa de identidade não é autenticação de produção. Os CSVs são snapshots, não dados em tempo real.

### Declaração de assistência de IA

Codex e outros assistentes de IA ajudaram a elaborar código, testes, documentação e casos de avaliação. O candidato revisou a arquitetura e executou os comandos reportados. Nenhuma credencial, benchmark inventado ou histórico Git falsificado foi incluído.
