# Architecture

## English

The agent is a small Python service with deterministic, whitelisted tools. Customer messages are routed to catalog SQL functions, privacy-gated order lookup, or store-policy retrieval. The intended persistence layer is one PostgreSQL database with `pgvector`:

```text
PT-BR message -> bounded agent/tool router
                    |-> PostgreSQL SQL: products, promotions, orders
                    |-> PostgreSQL pgvector: policy chunks + evidence metadata
                    `-> grounded PT-BR response
```

The initial implementation consideration was SQLite for structured data plus direct lookup of the short policy document. The applicant explicitly requested evaluation of PostgreSQL with pgvector. The adopted hybrid keeps prices, stock, promotions, and order access deterministic in SQL/Python while using semantic retrieval for policy text. The model may select bounded tools, but it cannot generate SQL or decide prices, discounts, eligibility, or authorization.

pgvector is deliberately demonstrative rather than required by the current eight-page manual. It provides one extensible retrieval path if the policy corpus grows, keeps document/page/section/version evidence inspectable, and satisfies the case's RAG requirement. The trade-offs are additional database setup, embedding-model/dimension management, ingestion complexity, and the need for lexical fallback when exact wording matters. Local mock mode does not claim to validate pgvector quality.

The source PDFs and CSV snapshots remain local and are not public repository inputs. A public submission must provide a safe evaluator fixture or documented source-acquisition procedure before claiming fully reproducible ingestion. Demo order verification is not production authentication.

## Português (Brasil)

O agente é um serviço Python pequeno com ferramentas determinísticas e permitidas. As mensagens são direcionadas para funções SQL de catálogo, consulta de pedido protegida por privacidade ou recuperação das políticas da loja. A persistência prevista é um único PostgreSQL com `pgvector`.

A consideração inicial era usar SQLite para dados estruturados e consulta direta do documento curto. O candidato solicitou explicitamente avaliar PostgreSQL com pgvector. A arquitetura híbrida adotada mantém preços, estoque, promoções e acesso a pedidos determinísticos em SQL/Python, usando busca semântica para o texto das políticas. O modelo pode selecionar ferramentas limitadas, mas não pode gerar SQL nem decidir preços, descontos, elegibilidade ou autorização.

O pgvector é demonstrativo, não necessário para o manual atual de oito páginas. Ele deixa um caminho extensível para um corpus maior e torna documento/página/seção/versão inspecionáveis, ao custo de setup adicional, controle de dimensões do modelo de embeddings e complexidade de ingestão. O mock local não afirma validar a qualidade do pgvector.
