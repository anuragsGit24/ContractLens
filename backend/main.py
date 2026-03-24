from __future__ import annotations

from backend.services import model_singleton  # noqa: F401
from backend.services import risk_scorer  # noqa: F401

from fastapi import FastAPI
from backend.api.routes import router
app = FastAPI(
    title="ContractLens API",
    version="0.1.0",
    description="Indian Legal Contract Analysis System",
)
app.include_router(router)
@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "ContractLens",
        "docs": "/docs",
        "health": "/v1/health",
    }