# Authorized multi-tool workflow

Mode: PostgreSQL backend; deterministic tools

Customer: Comprei o teclado do pedido 1 e quero saber a política de troca.

Verification: matching customer field supplied separately.

Tool sequence: `get_order_status` → `search_products` → `search_policy`

Agent: O pedido 1 está entregue. Consultei a política de defeitos na seção `defects`, página 8. A loja orienta a análise e o encaminhamento conforme a garantia aplicável; se houver conflito entre prazos, o caso deve ser encaminhado para atendimento humano.

Safety note: this demo verification is not production authentication and does not expose customer contact details.
