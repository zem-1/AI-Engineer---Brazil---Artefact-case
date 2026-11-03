"""Bounded business tools. The LLM-facing layer should expose only this registry."""

from __future__ import annotations

from decimal import Decimal
from .core import Store, installments, sale_price

TOOL_NAMES = frozenset({"search_products", "get_product", "get_order_status", "price_quote", "search_policy", "get_store_info"})

def search_products(store: Store, budget: Decimal | None = None):
    return [{"product_id": p.product_id, "name": p.name, "price": p.price, "stock": p.stock, "status": p.status} for p in store.search_products(budget)]

def get_product(store: Store, product_id: int):
    product = store.get_product(product_id) if hasattr(store, "get_product") else store.products.get(product_id)
    if not product: return {"found": False}
    return {"found": True, "product_id": product.product_id, "name": product.name, "price": product.price, "stock": product.stock, "status": product.status}

def get_order_status(store: Store, order_id: int, verification: str | None = None):
    return store.get_order(order_id, verification)

def price_quote(store: Store, product_id: int, payment: str | None = None, installment_count: int | None = None):
    product = store.get_product(product_id) if hasattr(store, "get_product") else store.products.get(product_id)
    if not product: return {"found": False}
    promotion = store.get_promotion(product_id) if hasattr(store, "get_promotion") else store.promotions.get(product_id)
    result = sale_price(product, promotion, payment)
    if installment_count is not None: result["installments"] = installments(result["current_price"], installment_count)
    result["product_id"] = product_id
    return result

def search_policy(store: Store, query: str):
    return store.policy_search(query)

def get_store_info():
    return {"city": "Campo Grande/MS", "hours": "Mon-Fri 09:00-18:00; Sat 09:00-13:00; closed Sundays and holidays"}

def call_tool(store: Store, name: str, arguments: dict):
    if name not in TOOL_NAMES: raise ValueError(f"Tool is not allowed: {name}")
    functions = {"search_products": search_products, "get_product": get_product, "get_order_status": get_order_status, "price_quote": price_quote, "search_policy": search_policy, "get_store_info": lambda _store, **kwargs: get_store_info()}
    return functions[name](store, **arguments)
