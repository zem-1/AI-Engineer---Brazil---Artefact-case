from __future__ import annotations

import csv, re, unicodedata
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal("0.01")

@dataclass(frozen=True)
class Product:
    product_id: int; name: str; price: Decimal; stock: int; status: str; category_id: int

@dataclass(frozen=True)
class Promotion:
    product_id: int; percent: Decimal; description: str; active: bool

@dataclass(frozen=True)
class Order:
    order_id: int; customer_id: int; status: str; total: Decimal

def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)

def sale_price(product: Product, promotion: Promotion | None, payment: str | None = None) -> dict:
    original = money(product.price)
    promo = money(original * (1 - promotion.percent / 100)) if promotion and promotion.active else original
    pix = payment == "pix"
    current = promo if promotion and promotion.active else (money(original * Decimal("0.95")) if pix else original)
    return {"original_price": original, "promotion_price": promo if promotion and promotion.active else None,
            "current_price": current, "pix_stacked": False,
            "pix_discount_ignored": bool(pix and promotion and promotion.active)}

def installments(total: Decimal, count: int) -> dict:
    if count not in range(1, 13): raise ValueError("installment count must be 1..12")
    minimum = Decimal("50") if count <= 3 else Decimal("80") if count <= 6 else Decimal("100")
    return {"eligible": total >= minimum, "minimum_total": minimum, "installment": money(total / count)}

class Store:
    def __init__(self, root: Path):
        data = root / "Desafio Técnico AI Engineer 2026" / "data"
        data_candidates = [p for p in root.glob("*/data") if (p / "desafio_tecnico_ai_eng - products.csv").exists()]
        if not data_candidates:
            raise FileNotFoundError("Could not find source data directory with products CSV")
        data = data_candidates[0]
        self.products = self._products(data / "desafio_tecnico_ai_eng - products.csv")
        self.promotions = self._promotions(data / "desafio_tecnico_ai_eng - promotions.csv")
        self.orders = self._orders(data / "desafio_tecnico_ai_eng - orders.csv")
        self.order_items = self._rows(data / "desafio_tecnico_ai_eng - order_items.csv")
        self.policy = [{"document": "políticas_da_loja.pdf", "section": "payment", "page": 4, "text": "PIX tem 5% sobre o preço de lista e não acumula com promoção."},
                       {"document": "políticas_da_loja.pdf", "section": "returns", "page": 6, "text": "Arrependimento deve ser solicitado em até 7 dias corridos do recebimento."},
                       {"document": "políticas_da_loja.pdf", "section": "exchanges", "page": 7, "text": "Trocas por preferência devem ser solicitadas em até 7 dias, observando as condições do produto."},
                       {"document": "políticas_da_loja.pdf", "section": "defects", "page": 8, "text": "Em caso de defeito, a loja orienta o atendimento para análise e encaminhamento conforme a garantia aplicável."}]

    @staticmethod
    def _rows(path):
        with path.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
    def _products(self, p): return {int(r["product_id"]): Product(int(r["product_id"]), r["name"], Decimal(r["price_brl"]), int(r["stock_quantity"]), r["status"], int(r["category_id"])) for r in self._rows(p)}
    def _promotions(self, p): return {int(r["product_id"]): Promotion(int(r["product_id"]), Decimal(r["discount_percent"]), r["description"], r["is_active"] == "1") for r in self._rows(p)}
    def _orders(self, p): return {int(r["order_id"]): Order(int(r["order_id"]), int(r["customer_id"]), r["status"], Decimal(r["total_brl"]) / 100) for r in self._rows(p)}
    def search_products(self, budget=None):
        return [p for p in self.products.values() if p.status == "active" and p.stock > 0 and (budget is None or p.price <= budget)]
    def get_order(self, order_id, verification=None):
        order = self.orders.get(order_id)
        if not order or verification != str(order.customer_id): return {"authorized": False, "reason": "verification_required"}
        return {"authorized": True, "order_id": order.order_id, "status": order.status, "total": order.total}
    def policy_search(self, query):
        normalize = lambda value: "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn")
        normalized = normalize(query)
        terms = set(re.findall(r"[a-z0-9]+", normalized))
        def score(item):
            value = len(terms & set(re.findall(r"[a-z0-9]+", normalize(item["text"]))))
            if item["section"] == "defects" and any(word in normalized for word in ("defeito", "garantia")): value += 10
            if item["section"] == "exchanges" and "troca" in normalized and not any(word in normalized for word in ("defeito", "garantia")): value += 10
            return value
        ranked = sorted(self.policy, key=score, reverse=True)
        return ranked[:1]

def respond(store: Store, message: str, order_verification: str | None = None) -> dict:
    text = message.lower(); tools = []; evidence = []
    is_order = "pedido" in text or "entrega" in text
    is_product = any(w in text for w in ("produto", "violão", "guitarra", "teclado", "disponível", "preço", "r$"))
    is_policy = any(w in text for w in ("pix", "arrependimento", "troca", "política"))
    if is_order and is_product and is_policy:
        m = re.search(r"(?:pedido|#)\s*(\d+)", text); order_id = int(m.group(1)) if m else 0
        order = store.get_order(order_id, order_verification); tools.append("get_order_status")
        products = store.search_products(); tools.append("search_products")
        evidence = store.policy_search(text); tools.append("search_policy")
        if order.get("authorized"):
            answer = f"O pedido {order_id} está {status_pt(order['status'])}. Posso verificar produtos e a política aplicável; a evidência consultada é {evidence[0]['section']} (página {evidence[0]['page']})."
        else:
            answer = "Não vou expor o pedido sem validação do titular. Posso, ainda assim, consultar produtos e a política geral da loja."
    elif is_product:
        budget_match = re.search(r"(?:r\$\s*|até\s*)([\d.,]+)", text)
        budget = Decimal(budget_match.group(1).replace(".", "").replace(",", ".")) if budget_match else None
        products = store.search_products(budget); tools.append("search_products")
        answer = f"Encontrei {len(products)} produto(s) ativo(s) em estoque" + (f" até R$ {budget:.2f}." if budget else ".")
    elif is_order:
        m = re.search(r"(?:pedido|#)\s*(\d+)", text); order_id = int(m.group(1)) if m else 0
        result = store.get_order(order_id, order_verification); tools.append("get_order_status")
        answer = f"O pedido {order_id} está {status_pt(result['status'])}." if result.get("authorized") else "Para consultar o pedido, preciso validar um dado do titular. Não vou expor informações apenas com o número do pedido."
    elif is_policy:
        evidence = store.policy_search(text); tools.append("search_policy")
        answer = evidence[0]["text"] if evidence else "Não encontrei uma política aplicável; vou encaminhar para atendimento."
    else:
        answer = "Posso ajudar com instrumentos, disponibilidade, pedidos e políticas da loja."
    return {"answer": answer, "tools": tools, "evidence": evidence}

def status_pt(status: str) -> str:
    return {"delivered": "entregue", "processing": "em processamento", "shipped": "enviado", "cancelled": "cancelado", "pending": "pendente"}.get(status, status)
