# Authorized multi-tool workflow

Mode: PostgreSQL backend; deterministic tools

Customer: Comprei o teclado do pedido 1 e quero saber a política de troca.

Verification: matching customer field supplied separately.

Tool sequence: `get_order_status` → `search_products` → `search_policy`

Agent: O pedido foi consultado somente após a validação do titular. A política aplicável deve ser confirmada com a evidência documental; regras ambíguas ou casos jurídicos são encaminhados para atendimento humano.

Safety note: this demo verification is not production authentication and does not expose customer contact details.
