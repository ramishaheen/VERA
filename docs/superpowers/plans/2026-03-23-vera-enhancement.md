# VERA Enhancement & Web Interface Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all bugs in the VERA system, enhance it with multi-LLM support, and deliver a production-ready web UI where users plug in an API key and interact through VERA's full pipeline.

**Architecture:** VERA acts as a middleware proxy — it intercepts every user prompt, decomposes it into a DAG of typed tasks (math/fact/semantic/logic), routes each to the optimal engine (sympy sandbox, Wikipedia RAG, or LLM), verifies results, and returns a synthesized response with confidence metadata. A FastAPI backend serves both the OpenAI-compatible REST API and a single-page web UI that visualises the verification graph in real time.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, SymPy, OpenAI SDK (≥1.3), python-dotenv, Pydantic v2, Requests, NetworkX; frontend is vanilla HTML/CSS/JS (no build step).

---

## Chunk 1: Project Skeleton & Bug Fixes

### Task 1: Project directory structure

**Files:**
- Create: `vera/__init__.py`
- Create: `vera/models.py`
- Create: `vera/segmenter.py`
- Create: `vera/router.py`
- Create: `vera/arbitrator.py`
- Create: `vera/client.py`
- Create: `tests/__init__.py`

- [ ] Create all directories: `vera/`, `static/`, `tests/`, `docs/`
- [ ] Copy `models.py`, `segmenter.py`, `router.py`, `arbitrator.py`, `client.py` verbatim from source
- [ ] Fix `vera/__init__.py` — remove eager server import (causes VERACore init at import time, crashes without API key)

```python
# vera/__init__.py
__version__ = "1.0.0"
__author__ = "Dr. Rami Shaheen"
from .client import VERAClient
__all__ = ["VERAClient"]
```

- [ ] Commit: `git commit -m "chore: scaffold vera project structure"`

---

### Task 2: Fix engines.py

**Files:**
- Create: `vera/engines.py`

**Bugs fixed:**
1. `DeterministicSandbox.__init__` instantiates `OpenAI()` unnecessarily — sympy needs no API key, this crashes without env var.
2. Hardcoded `gpt-4.1-mini` in `SemanticEngine` — should accept model from caller.

- [ ] Remove `self.client = OpenAI()` from `DeterministicSandbox.__init__`
- [ ] Add `OPENAI_API_KEY` lazy-load (only instantiate client when `SemanticEngine.execute` is called)
- [ ] Verify `DeterministicSandbox` works without any env var
- [ ] Commit: `git commit -m "fix: remove unused OpenAI client from DeterministicSandbox"`

---

### Task 3: Enhance core.py

**Files:**
- Create: `vera/core.py`

- [ ] Load `.env` at top of file via `python-dotenv`
- [ ] Accept `api_key` param in `VERACore.__init__` (falls back to env var)
- [ ] Pass `api_key` through to `SemanticEngine`
- [ ] Commit: `git commit -m "feat: add dotenv loading and api_key param to VERACore"`

---

## Chunk 2: Enhanced Server

### Task 4: Enhance server.py

**Files:**
- Create: `vera/server.py`

- [ ] Add `CORSMiddleware` (allow all origins for local dev)
- [ ] Mount `static/` directory at `/`
- [ ] Add `POST /api/configure` endpoint — accepts `{"api_key": "...", "model": "..."}`, stores in server state, reinitialises `VERACore`
- [ ] Add `GET /api/config` endpoint — returns current model name (never the key)
- [ ] Fix `hash()` negative value bug: `str(abs(hash(user_message)))[:8]`
- [ ] Read default model from `VERA_MODEL` env var (fallback `gpt-4o-mini`)
- [ ] Expose `/vera/process` for full metadata (already exists, keep)
- [ ] Add `uvicorn.run` entrypoint with `__main__` guard and env-var port
- [ ] Commit: `git commit -m "feat: CORS, static serving, runtime config endpoint"`

---

## Chunk 3: Web UI

### Task 5: Create static/index.html

**Files:**
- Create: `static/index.html`

Single self-contained HTML file (inline CSS + JS, no bundler).

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  VERA  •  v1.0.0                    [⚙ Settings] │
├──────────────────┬──────────────────────────────┤
│                  │  ┌──────────────────────────┐ │
│   Chat window    │  │  VERA Metadata           │ │
│   (messages)     │  │  ─────────────────────── │ │
│                  │  │  ✓ Verified              │ │
│                  │  │  Confidence: 0.92        │ │
│                  │  │  Latency: 312ms          │ │
│                  │  │  Tasks: 2                │ │
│                  │  │  [▸ Execution Graph]     │ │
│                  │  └──────────────────────────┘ │
├──────────────────┴──────────────────────────────┤
│  [text input                         ] [Send]   │
└─────────────────────────────────────────────────┘
```

**Settings modal:**
- API Key (password input)
- Model selector (gpt-4o-mini, gpt-4o, gpt-4.1-mini, gpt-4.1)
- [Save] button → calls `POST /api/configure`

- [ ] Write HTML skeleton with CSS grid layout
- [ ] Implement settings modal (open/close, save to server)
- [ ] Implement chat message rendering (user + assistant bubbles)
- [ ] Implement `sendMessage()` → `POST /v1/chat/completions` → render response
- [ ] Render VERA metadata panel per response (confidence, verified badge, latency, task list)
- [ ] Add collapsible execution graph section (JSON tree)
- [ ] Add loading spinner during request
- [ ] Commit: `git commit -m "feat: add VERA web UI with metadata visualization"`

---

## Chunk 4: Config, Tests, Run Script

### Task 6: requirements.txt + .env.example + run.py

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `run.py`

- [ ] Pin updated requirements (fastapi, uvicorn, pydantic v2, openai≥1.3, sympy, networkx, requests, python-dotenv, aiofiles)
- [ ] Write `.env.example` with all env vars documented
- [ ] Write `run.py` — loads dotenv, starts uvicorn programmatically, opens browser
- [ ] Commit: `git commit -m "chore: add run.py, .env.example, updated requirements"`

---

### Task 7: Tests

**Files:**
- Create: `tests/test_vera.py`

- [ ] Test `Segmenter` — math/fact/semantic/logic classification
- [ ] Test `Router` — correct engine assigned per task type
- [ ] Test `DeterministicSandbox` — arithmetic, percentage, compound interest (no API key needed)
- [ ] Test `RAGEngine` — Wikipedia retrieval (network, can be skipped offline)
- [ ] Test `VERACore` — end-to-end with mocked `SemanticEngine` (no API key needed for offline test)
- [ ] Run: `python -m pytest tests/ -v`
- [ ] Commit: `git commit -m "test: add vera unit and integration tests"`

---

### Task 8: End-to-End Validation

- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`, insert real API key
- [ ] Run server: `python run.py`
- [ ] Open browser at `http://localhost:8000`
- [ ] Configure API key in settings modal
- [ ] Test math prompt: "Calculate compound interest on $10,000 at 5% for 3 years"
- [ ] Test fact prompt: "Who is Marie Curie?"
- [ ] Test semantic prompt: "Draft a one-paragraph introduction for a product manager role"
- [ ] Verify all three show correct VERA metadata (confidence, engine used, latency)
- [ ] Commit: `git commit -m "feat: vera v1.0 production ready"`
