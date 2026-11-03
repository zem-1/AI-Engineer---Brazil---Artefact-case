from __future__ import annotations

import json, os
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
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
    if os.getenv("LLM_PROVIDER") == "ollama":
        return run_ollama(store, message, verification)
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

def run_ollama(store, message: str, verification: str | None = None) -> dict:
    """Run the same bounded tool loop against a local Ollama server."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("LLM_MODEL", "llama3.1:8b")
    ollama_tools = [{"type": "function", "function": {"name": tool["name"], "description": tool["description"], "parameters": tool["parameters"]}} for tool in TOOL_SCHEMAS]
    messages = [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": message}]
    used, evidence = [], []
    for _ in range(4):
        payload = json.dumps({"model": model, "messages": messages, "tools": ollama_tools, "stream": False}).encode()
        request = Request(base_url + "/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=90) as response: result = json.loads(response.read().decode())
        except (URLError, HTTPError, TimeoutError) as exc:
            raise RuntimeError(f"Ollama is unavailable at {base_url}; start Ollama and pull {model}") from exc
        assistant = result.get("message", {})
        calls = assistant.get("tool_calls") or []
        messages.append(assistant)
        if not calls: return {"answer": assistant.get("content", ""), "tools": used, "evidence": evidence}
        for call in calls:
            function = call.get("function", {}); name = function.get("name"); args = function.get("arguments") or {}
            if name == "get_order_status" and verification is not None: args["verification"] = verification
            output = call_tool(store, name, args); used.append(name)
            if name == "search_policy": evidence.extend(output)
            messages.append({"role": "tool", "content": json.dumps(output, default=str, ensure_ascii=False)})
    raise RuntimeError("Ollama tool loop exceeded the maximum of 4 turns")
