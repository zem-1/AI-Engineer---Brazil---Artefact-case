from pathlib import Path
from app.core import Store, respond, sale_price, installments

CASES = [
 ("product availability", lambda s: "search_products" in respond(s, "Tem violão disponível até R$ 700?")["tools"]),
 ("promotion no stacking", lambda s: (lambda pid: not sale_price(s.products[pid], s.promotions[pid], "pix")["pix_stacked"])(next(pid for pid, promo in s.promotions.items() if promo.active))),
 ("privacy gate", lambda s: not respond(s, "Qual o status do pedido 1?")["answer"].startswith("O pedido")),
 ("authorized order", lambda s: respond(s, "Qual o status do pedido 1?", "3")["answer"].startswith("O pedido")),
 ("policy evidence", lambda s: bool(respond(s, "Qual a regra de PIX?")["evidence"])),
 ("unsupported request", lambda s: "Posso ajudar" in respond(s, "Qual o placar do jogo?")["answer"]),
 ("tool routing", lambda s: respond(s, "Como funciona o arrependimento?")["tools"] == ["search_policy"]),
 ("installment threshold", lambda s: not installments(__import__('decimal').Decimal("49"), 3)["eligible"]),
 ("active stock filter", lambda s: all(p.status == "active" and p.stock > 0 for p in s.search_products())),
 ("multi-tool sequence", lambda s: respond(s, "Comprei um teclado no pedido 1 e quero saber a política de troca", "3")["tools"] == ["get_order_status", "search_products", "search_policy"]),
]

def run(store=None):
    store = store or Store(Path(__file__).resolve().parents[1])
    failed = 0
    for name, check in CASES:
        ok = bool(check(store)); print(f"{'PASS' if ok else 'FAIL'} {name}"); failed += not ok
    return int(failed)

if __name__ == "__main__": raise SystemExit(run())
