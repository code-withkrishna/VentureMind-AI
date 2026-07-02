"""
VentureMind AI — FastAPI backend server.
Exposes POST /analyze for the Next.js frontend.
Run: uvicorn api_server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
import sqlite3
import time
import uuid
from dataclasses import asdict
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, field_validator
except ImportError:
    raise ImportError("Run: pip install fastapi uvicorn")

from core.config import ROOT_DIR, Settings
from core.orchestrator import AgentathonOrchestrator

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="VentureMind AI",
    description="AI Investment Committee — 6-agent startup validation pipeline",
    version="2.0.0",
    docs_url="/docs",
    redoc_url=None,
)

logger = logging.getLogger("venturemind.api")


def _allowed_origins() -> list[str]:
    default_origins = [
        "http://localhost:3000",
        "https://venture-mind-ai-eight.vercel.app",
    ]
    configured = (os.getenv("FRONTEND_URL") or "").strip()
    if not configured:
        return default_origins
    extras = [origin.strip() for origin in configured.split(",") if origin.strip()]
    # Keep deterministic order while removing duplicates.
    return list(dict.fromkeys(default_origins + extras))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Lazy-load orchestrator (avoids Settings error at import time) ─────────────

_orchestrator: AgentathonOrchestrator | None = None

def get_orchestrator() -> AgentathonOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentathonOrchestrator()
    return _orchestrator

# ── Request / Response schemas ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    idea: str
    question: str | None = None   # Accept either field name

    @field_validator("idea")
    @classmethod
    def validate_idea(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Startup idea must be at least 10 characters.")
        if len(v) > 2000:
            v = v[:2000]
        return v

# ── Serialization helpers ─────────────────────────────────────────────────────

def _clean(obj: Any) -> Any:
    """Recursively convert dataclass / non-JSON-safe objects to dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _clean(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(i) for i in obj]
    return obj

def result_to_json(result: Any, idea: str, duration_ms: int) -> dict:
    """
    Convert ResearchRunResult → the shape the Next.js route.ts normalizer expects.
    Keeps all keys the normalizer's asString/asNumber helpers handle gracefully.
    """
    raw = _clean(result)
    return {
        "id":                  raw.get("run_id", uuid.uuid4().hex[:12]),
        "run_id":              raw.get("run_id", ""),
        "idea":                idea,
        "user_question":       idea,
        "timestamp":           int(time.time() * 1000),
        "processing_time_ms":  duration_ms,
        "final_brief":         raw.get("final_brief", {}),
        "trace":               raw.get("trace", []),
        "observations":        raw.get("observations", []),
    }

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> JSONResponse:
    db_path = ROOT_DIR / "data" / "agent_memory.sqlite"
    db_status = "connected"
    db_error = None

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path, timeout=3) as connection:
            connection.execute("SELECT 1")
    except Exception as exc:
        db_status = "disconnected"
        db_error = "Database connectivity check failed."
        logger.exception("Health check database connectivity failure: %s", exc)

    overall_status = "ok" if db_status == "connected" else "degraded"
    response: dict[str, Any] = {
        "status": overall_status,
        "service": "VentureMind AI",
        "version": "2.0.0",
        "environment": (os.getenv("ENVIRONMENT") or os.getenv("RENDER_ENVIRONMENT") or "unknown"),
        "database": {"status": db_status},
    }
    if db_error:
        response["database"]["message"] = db_error
    status_code = 200 if db_status == "connected" else 503
    return JSONResponse(status_code=status_code, content=response)

@app.post("/analyze")
async def analyze(payload: AnalyzeRequest) -> dict:
    idea = payload.idea or payload.question or ""
    idea = idea.strip()
    if not idea:
        raise HTTPException(status_code=400, detail="Startup idea is required.")

    try:
        orchestrator = get_orchestrator()
    except RuntimeError as exc:
        logger.exception("Analyzer configuration error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Analyzer is not configured. Contact support to configure required provider keys.",
        )

    t0 = time.time()
    try:
        result = orchestrator.run(idea)
    except Exception as exc:
        logger.exception("Analysis execution failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again shortly.")

    duration_ms = int((time.time() - t0) * 1000)
    return result_to_json(result, idea, duration_ms)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
