from __future__ import annotations

import json, os
from .core import respond
from .tools import call_tool

TOOL_SCHEMAS = [
    {"type": "function", "name": "search_products", "description": "Find active products in stock, optionally below a budget.", "parameters": {"type": "object", "properties": {"budget": {"type": ["number", "null"]}}, "additionalProperties": False}},
    {"type": "function", "name": "get_product", "description": "Get a product by ID.", "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}}, "required": ["product_id"], "additionalProperties": False}},
    {"type": "function", "name": "get_order_status", "description": "Get an order only after matching identity verification.", "parameters": {"type": "object", "properties": {"order_id": {"type": "integer"}, "verification": {"type": ["string", "null"]}}, "required": ["order_id"], "additionalProperties": False}},
    {"type": "function", "name": "price_quote", "description": "Calculate deterministic price and installments.", "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}, "payment": {"type": ["string", "null"]}, "installment_count": {"type": ["integer", "null"]}}, "required": ["product_id"], "additionalProperties": False}},
    {"type": "function", "name": "search_policy", "description": "Retrieve store policy evidence with source metadata.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}},
    {"type": "function", "name": "get_store_info", "description": "Get store location and opening hours.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
]

INSTRUCTIONS = """You are a friendly Brazilian Portuguese music-store attendant. Use only the provided tools for operational facts and policies. Never invent prices, stock, order data, authorization, or policy rules. Do not reveal order information without matching verification. If evidence is missing or ambiguous, say so and escalate. Keep answers concise and in PT-BR."""

def run_agent(store, message: str, verification: str | None = None) -> dict:
    if os.getenv("LLM_PROVIDER", "mock") == "mock":
        return respond(store, message, verification)
    if os.getenv("LLM_PROVIDER") != "openai": raise RuntimeError("Unsupported LLM_PROVIDER; use mock or openai")
    try: from openai import OpenAI
    except ImportError as exc: raise RuntimeError("Install API support with: pip install -e '.[api]'") from exc
    if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    client = OpenAI(); model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    response = client.responses.create(model=model, instructions=INSTRUCTIONS, input=message, tools=TOOL_SCHEMAS)
    calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
    if not calls: return {"answer": response.output_text, "tools": [], "evidence": []}
    inputs = list(response.output)
    used = []
    evidence = []
    for call in calls:
        args = json.loads(call.arguments or "{}")
        if call.name == "get_order_status" and verification is not None: args["verification"] = verification
        result = call_tool(store, call.name, args); used.append(call.name)
        if call.name == "search_policy": evidence.extend(result)
        inputs.append({"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(result, default=str, ensure_ascii=False)})
    final = client.responses.create(model=model, instructions=INSTRUCTIONS, input=inputs, tools=TOOL_SCHEMAS)
    return {"answer": final.output_text, "tools": used, "evidence": evidence}
