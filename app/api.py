"""Optional FastAPI adapter around the deterministic agent."""

from pathlib import Path
from .core import Store, respond

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - dependency is optional for local mock mode
    FastAPI = None

if FastAPI:
    app = FastAPI(title="Empório da Música support agent")
    store = Store(Path(__file__).resolve().parents[1])

    class ChatRequest(BaseModel):
        message: str
        order_verification: str | None = None

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "deterministic-mock"}

    @app.post("/chat")
    def chat(request: ChatRequest):
        return respond(store, request.message, request.order_verification)
else:
    app = None
