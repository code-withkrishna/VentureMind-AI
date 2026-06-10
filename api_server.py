"""
VentureMind AI — FastAPI backend server.
Exposes POST /analyze for the Next.js frontend.
Run: uvicorn api_server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, field_validator
except ImportError:
    raise ImportError("Run: pip install fastapi uvicorn")

from core.config import Settings
from core.orchestrator import AgentathonOrchestrator

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="VentureMind AI",
    description="AI Investment Committee — 6-agent startup validation pipeline",
    version="2.0.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Lock down to your Vercel URL in production
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
async def health() -> dict:
    return {"status": "ok", "service": "VentureMind AI", "version": "2.0.0"}

@app.post("/analyze")
async def analyze(payload: AnalyzeRequest) -> dict:
    idea = payload.idea or payload.question or ""
    idea = idea.strip()
    if not idea:
        raise HTTPException(status_code=400, detail="Startup idea is required.")

    try:
        orchestrator = get_orchestrator()
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analyzer not configured: {e}. Set GROQ_API_KEY and SERPER_API_KEY.",
        )

    t0 = time.time()
    try:
        result = orchestrator.run(idea)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    duration_ms = int((time.time() - t0) * 1000)
    return result_to_json(result, idea, duration_ms)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
