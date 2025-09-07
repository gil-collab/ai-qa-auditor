from __future__ import annotations

from fastapi import FastAPI

from .schemas import AuditInput, AuditOutput
from .scorer import run_audit


app = FastAPI(title="AI QA Auditor", version="0.1.0")


@app.get("/")
def health() -> dict:
    return {"status": "ok"}


@app.post("/audit", response_model=AuditOutput)
def audit(payload: AuditInput) -> AuditOutput:
    return run_audit(payload)

