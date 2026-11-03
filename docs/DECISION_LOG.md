# Decision log

## English

### D-001 — Initial architecture consideration

- **Attribution:** Assistant recommendation.
- **Decision:** Consider FastAPI/Python, SQLite for structured operational data, direct targeted lookup for the short policy PDF, and native tool calling.
- **Reasoning:** This was the smallest reasonable approach for a short, mostly static policy document and the case's emphasis on clear behavior.
- **Status:** Superseded as the target architecture; no claim that it was implemented.

### D-002 — PostgreSQL + pgvector evaluation

- **Attribution:** Applicant/user decision.
- **Decision:** Evaluate one PostgreSQL database with pgvector, retaining SQL for structured operational facts and semantic retrieval for store policies.
- **Reasoning:** Demonstrates an extensible RAG path while avoiding a second vector service. The eight-page document does not require vectors for scale, so the choice is an interview demonstrator with setup and embedding-maintenance costs.
- **Status:** Current architecture target.

### D-003 — Deterministic business rules

- **Attribution:** Assistant engineering recommendation, adopted for implementation.
- **Decision:** Keep stock, promotion stacking, currency rounding, installments, and privacy checks in deterministic Python/SQL functions.
- **Reasoning:** Numerical, authorization, and policy-eligibility decisions must not be invented by an LLM.

### D-004 — AI-assisted development disclosure

- **Attribution:** Codex implementation with applicant review.
- **Decision:** Codex and other AI assistants may help draft code and documentation, but execution claims remain tied to commands and tests actually run. No credentials are embedded and no AI-generated history is fabricated.

## Português (Brasil)

O registro acima preserva a evolução real: a recomendação inicial considerou SQLite e consulta direta; o candidato decidiu avaliar PostgreSQL com pgvector; a solução atual combina SQL determinístico para dados estruturados e busca semântica para políticas. O uso de Codex/assistentes de IA é declarado, e os resultados só são considerados válidos quando verificados por execução real.
