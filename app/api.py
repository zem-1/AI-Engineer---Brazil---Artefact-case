"""Optional FastAPI adapter around the deterministic agent."""

from pathlib import Path
import os
from .core import Store
from .agent import run_agent

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - dependency is optional for local mock mode
    FastAPI = None

if FastAPI:
    app = FastAPI(title="Empório da Música support agent")
    if os.getenv("DATA_BACKEND", "mock") == "postgres":
        from .postgres import PostgresStore
        store = PostgresStore()
        backend = "postgres"
    else:
        store = Store(Path(__file__).resolve().parents[1])
        backend = "mock"

    class ChatRequest(BaseModel):
        message: str
        order_verification: str | None = None

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": backend}

    @app.post("/chat")
    def chat(request: ChatRequest):
        return run_agent(store, request.message, request.order_verification)
else:
    app = None
