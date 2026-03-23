"""
Production-ready FastAPI server for VERA.

Features:
- OpenAI-compatible /v1/chat/completions endpoint
- VERA-specific /vera/process endpoint (full metadata)
- Runtime configuration via /api/configure (set API key, model, base URL)
- Serves the web UI from /static
- CORS enabled (all origins for local/dev; restrict in production)
- Structured logging
"""

import os
import logging
import time
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from .core import VERACore

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vera.server")

# ── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="VERA API",
    description="Verification, Execution, Reasoning, Arbitration – Hybrid Neuro-Symbolic LLM Middleware",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state ────────────────────────────────────────────────────────────
# VERACore is initialised lazily so the server starts even without an API key.
_vera_core: Optional[VERACore] = None


def get_vera_core() -> VERACore:
    """Return the global VERACore instance, creating it if needed."""
    global _vera_core
    if _vera_core is None:
        _vera_core = VERACore()
    return _vera_core


# ── Static files (web UI) ───────────────────────────────────────────────────
_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ── Pydantic models ─────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o-mini"
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024


class ConfigureRequest(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None  # e.g. "http://192.168.100.39:1234/v1" for LM Studio


class FetchModelsRequest(BaseModel):
    base_url: str          # e.g. "http://192.168.100.39:1234"
    api_key: Optional[str] = "lm-studio"


# ── Health ──────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe."""
    return {"status": "healthy", "version": "1.0.0", "timestamp": int(time.time())}


@app.get("/", tags=["System"])
async def root():
    """Serve the web UI."""
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "VERA API is running. See /docs for endpoints."})


# ── Runtime configuration ───────────────────────────────────────────────────
@app.post("/api/configure", tags=["Configuration"])
async def configure(req: ConfigureRequest):
    """
    Update VERA's LLM configuration at runtime.

    - For OpenAI:    api_key="sk-...", model="gpt-4o-mini", base_url=null
    - For LM Studio: api_key="lm-studio" (any value), base_url="http://localhost:1234/v1", model="<your-model>"
    - For custom:    api_key="...", base_url="https://your-proxy/v1", model="..."
    """
    core = get_vera_core()
    core.reconfigure(
        model=req.model,
        api_key=req.api_key,
        base_url=req.base_url if req.base_url else None,
    )
    logger.info(
        "Configuration updated: model=%s, base_url=%s",
        core.model,
        core.base_url or "OpenAI default",
    )
    return {
        "status": "configured",
        "model": core.model,
        "provider": _detect_provider(core.base_url),
    }


@app.get("/api/config", tags=["Configuration"])
async def get_config():
    """Return current configuration (API key is never returned)."""
    core = get_vera_core()
    return {
        "model": core.model,
        "provider": _detect_provider(core.base_url),
        "base_url": core.base_url,
        "api_key_set": bool(core.api_key),
    }


@app.post("/api/fetch-models", tags=["Configuration"])
async def fetch_models(req: FetchModelsRequest):
    """
    Probe a LM Studio (or any OpenAI-compatible) endpoint and return available models.
    Strips trailing slashes and /v1 so users can paste any URL format.
    """
    import requests as req_lib

    # Normalise URL — accept with or without /v1
    base = req.base_url.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]

    try:
        headers = {"Authorization": f"Bearer {req.api_key or 'lm-studio'}"}
        r = req_lib.get(f"{base}/v1/models", headers=headers, timeout=6)
        r.raise_for_status()
        data = r.json()
        models = [m["id"] for m in data.get("data", [])]
        return {
            "status": "ok",
            "base_url": f"{base}/v1",
            "models": models,
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach {base}/v1/models — {str(e)}",
        )


def _detect_provider(base_url: Optional[str]) -> str:
    if not base_url:
        return "openai"
    if "localhost" in base_url or "127.0.0.1" in base_url:
        return "lm_studio"
    return "custom"


# ── OpenAI-compatible endpoint ───────────────────────────────────────────────
@app.post("/v1/chat/completions", tags=["LLM"])
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions processed through VERA.
    Drop-in replacement for OpenAI's API.
    """
    user_message = _extract_user_message(request.messages)

    try:
        vera_response = get_vera_core().process(user_message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Processing error")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "id": f"vera-{abs(hash(user_message)):08x}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": vera_response.response},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(vera_response.response.split()),
            "total_tokens": len(user_message.split()) + len(vera_response.response.split()),
        },
        "vera_metadata": {
            "verified": vera_response.verified,
            "confidence": vera_response.confidence,
            "latency_ms": vera_response.latency_ms,
            "model_used": vera_response.model_used,
            "execution_graph": vera_response.execution_graph.to_dict(),
            "verification_results": [
                {
                    "task_id": vr.task_id,
                    "verified": vr.verified,
                    "confidence": vr.confidence,
                    "details": vr.details,
                }
                for vr in vera_response.verification_results
            ],
        },
    }


# ── Full VERA endpoint ───────────────────────────────────────────────────────
@app.post("/vera/process", tags=["VERA"])
async def vera_process(request: ChatCompletionRequest):
    """
    Process a prompt through VERA and return full verification metadata.
    """
    user_message = _extract_user_message(request.messages)

    try:
        vera_response = get_vera_core().process(user_message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Processing error")
        raise HTTPException(status_code=500, detail=str(e))

    return vera_response.to_dict()


# ── Side-by-side comparison ──────────────────────────────────────────────────
@app.post("/api/compare", tags=["VERA"])
async def compare(request: ChatCompletionRequest):
    """
    Returns two responses for the same prompt:
      - vera_response: processed through the full VERA pipeline
      - direct_response: sent straight to the LLM, bypassing VERA
    """
    user_message = _extract_user_message(request.messages)
    core = get_vera_core()

    # Run both in parallel
    import asyncio, concurrent.futures

    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def run_vera():
        return core.process(user_message)

    def run_direct():
        try:
            resp = core.semantic_engine.client.chat.completions.create(
                model=core.model,
                messages=[{"role": "user", "content": user_message}],
                temperature=0.7,
                max_tokens=1024,
            )
            return resp.choices[0].message.content, True
        except Exception as e:
            return f"LLM Error: {e}", False

    vera_future = loop.run_in_executor(executor, run_vera)
    direct_future = loop.run_in_executor(executor, run_direct)
    vera_result, (direct_text, direct_ok) = await asyncio.gather(vera_future, direct_future)

    return {
        "vera": {
            "response": vera_result.response,
            "verified": vera_result.verified,
            "confidence": vera_result.confidence,
            "latency_ms": vera_result.latency_ms,
            "execution_graph": vera_result.execution_graph.to_dict(),
            "verification_results": [
                {"task_id": vr.task_id, "verified": vr.verified,
                 "confidence": vr.confidence, "details": vr.details}
                for vr in vera_result.verification_results
            ],
        },
        "direct": {
            "response": direct_text,
            "verified": False,
            "confidence": None,
            "latency_ms": None,
        },
    }


# ── Models list ──────────────────────────────────────────────────────────────
@app.get("/vera/models", tags=["VERA"])
@app.get("/v1/models", tags=["LLM"])
async def list_models():
    """List models known to VERA."""
    return {
        "object": "list",
        "data": [
            {"id": m, "object": "model", "owned_by": "vera"}
            for m in [
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4.1-mini",
                "gpt-4.1",
                "gpt-3.5-turbo",
                "lm-studio-local",
            ]
        ],
    }


# ── Helpers ──────────────────────────────────────────────────────────────────
def _extract_user_message(messages: List[Message]) -> str:
    for msg in messages:
        if msg.role == "user":
            return msg.content
    raise HTTPException(status_code=400, detail="No user message found in messages list")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("VERA_HOST", "0.0.0.0")
    port = int(os.getenv("VERA_PORT", "8000"))
    uvicorn.run("vera.server:app", host=host, port=port, reload=False, log_level="info")
