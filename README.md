# Empório da Música — AI support agent

## English

Small, reproducible Python customer-support prototype for the Artefact AI Engineer case. The agent uses deterministic tools for catalog, promotions, order privacy, and policy evidence. The customer-facing language is Brazilian Portuguese. The intended production persistence layer is one PostgreSQL database with `pgvector`: SQL stores operational data and vectors store policy chunks. No model is allowed to create SQL or calculate prices.

This repository is intentionally small. The local evaluation runner works without credentials or third-party packages; the FastAPI and PostgreSQL path is enabled by the optional dependencies and Docker Compose.

```powershell
python -m unittest discover -s tests -v
python -m app.cli evaluate
python -m app.cli chat "Tem violão disponível até R$ 700?"
```

For optional OpenAI tool calling, install the API extra, set `LLM_PROVIDER=openai`, `LLM_MODEL`, and `OPENAI_API_KEY` in the environment, then run the API. Without a key, keep `LLM_PROVIDER=mock`; the deterministic agent remains available and no successful LLM execution is claimed.

Install the runtime extras for API/Postgres execution with `pip install -e .[api,postgres]`, copy `.env.example` to `.env`, then start `docker compose up -d db`. Run `python -m app.cli ingest` for the six CSVs and `python -m app.cli ingest-policy-lexical` for reproducible PDF extraction and PostgreSQL full-text evidence. Use `python -m app.cli ingest-policy` when the embedding model is available for pgvector semantic retrieval. The source CSV/PDF files remain local by design.

The original recommendation was SQLite plus direct policy lookup. The applicant explicitly chose PostgreSQL + pgvector; that choice is preserved and documented in [docs/DECISION_LOG.md](artefact_codex_handoff/docs/DECISION_LOG.md). See [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md) for actual executions and limitations. Codex assisted with implementation and documentation; all claims in this README are limited to commands actually run.

## Português (Brasil)

Este é um protótipo Python pequeno e reproduzível de atendimento para o case da Artefact. O agente usa ferramentas determinísticas para catálogo, promoções, privacidade de pedidos e evidências de políticas. A linguagem para o cliente é PT-BR. A persistência prevista é um único PostgreSQL com `pgvector`: SQL guarda dados operacionais e vetores guardam trechos das políticas. O modelo não pode criar SQL nem calcular preços.

O avaliador local funciona sem credenciais ou pacotes de terceiros; o caminho FastAPI/PostgreSQL é habilitado pelas dependências opcionais e pelo Docker Compose.

Para usar PostgreSQL e a recuperação de políticas, instale `pip install -e .[api,postgres]`, copie `.env.example` para `.env`, inicie `docker compose up -d db`, rode `python -m app.cli ingest` para os CSVs e `python -m app.cli ingest-policy-lexical` para o PDF. Use `python -m app.cli ingest-policy` quando o modelo de embeddings estiver disponível. Os arquivos-fonte permanecem locais por decisão de segurança.

Para usar function calling opcional com OpenAI, defina `LLM_PROVIDER=openai`, `LLM_MODEL` e `OPENAI_API_KEY`. Sem chave, mantenha `LLM_PROVIDER=mock`; o agente determinístico continua disponível e nenhuma execução LLM bem-sucedida é afirmada sem teste real.

Os comandos acima executam os testes, a avaliação determinística e o CLI. Para a execução com banco, instale os extras, copie `.env.example` para `.env`, inicie `docker compose up -d db` e rode `python -m app.cli ingest`. Os CSVs/PDFs devem estar em `Desafio Técnico AI Engineer 2026/data/`.

Consulte [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md) para execuções reais e limitações. O Codex auxiliou a implementação e a documentação; nenhum resultado é declarado sem evidência de execução.
