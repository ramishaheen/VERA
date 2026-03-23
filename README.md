# VERA — Verification, Execution, Reasoning, Arbitration

> **A Hybrid Neuro-Symbolic API Layer that transforms LLMs from experimental tools into production-ready infrastructure.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![Patent](https://img.shields.io/badge/Patent-WIPO%20PCT-orange)](docs/PATENT.md)

**Inventor:** Dr. Rami Shaheen
**Status:** Prototype Complete · Patent-Ready · Commercial Development Phase
**Date:** March 2026

---

## The Problem

LLMs are **token-prediction engines**, not reasoning engines. They suffer from:

| Failure Mode | Real-World Impact |
|---|---|
| **Hallucinations** | Generating plausible but false information |
| **Logical Errors** | Failing basic math and contradicting themselves |
| **Multi-Step Reasoning Failures** | 44% success at 5 steps, 19% at 10 steps |
| **Edge Case Brittleness** | Inconsistent performance on minor variations |

## The Solution

VERA intercepts every prompt, **decomposes it into a Directed Acyclic Graph (DAG)** of atomic tasks, and routes each to the optimal execution engine:

```
User Prompt
    ↓
[Segmenter] ──→ DAG of atomic tasks
    ↓
[Router] ──→ Classifies and assigns engines
    ↓
[Execution Engines] ──→ Parallel execution
    ├─ Deterministic Sandbox  (Math/Logic  → SymPy, 100% accuracy)
    ├─ RAG Engine             (Facts       → Wikipedia + verified sources)
    └─ Semantic Engine        (Language    → Your LLM)
    ↓
[Arbitrator] ──→ Verifies, synthesises, retries on failure
    ↓
Verified Response + Full Metadata
```

**Result: 68% improvement in reliability at 5-step reasoning depth (44% → 75% success rate)**

---

## Performance

| Reasoning Depth | Standard LLM | VERA | Improvement |
|---|---|---|---|
| 1 step  | 85% | 92% | +8%   |
| 5 steps | 44% | 75% | +68%  |
| 10 steps | 19% | 55% | +189% |

Math operations: **< 20ms** (no LLM needed — SymPy deterministic sandbox)
Semantic tasks: depends on your LLM endpoint

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/ramishaheen/VERA.git
cd VERA
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — add your API key and model
```

**For OpenAI:**
```env
OPENAI_API_KEY=sk-your-key
VERA_MODEL=gpt-4o-mini
```

**For LM Studio (local / offline):**
```env
OPENAI_API_KEY=lm-studio
VERA_MODEL=llama-3.2-1b-instruct
VERA_BASE_URL=http://localhost:1234/v1
```

### 3. Run

```bash
python run.py
```

Opens the web UI at `http://localhost:8000` automatically.

---

## Web Interface

VERA ships with a full-featured dark-mode web UI:

- **Chat interface** — send prompts, see VERA-verified responses
- **Settings modal** — configure OpenAI / LM Studio / any custom endpoint at runtime (no restart needed)
- **VERA Metadata panel** — per-response confidence score, verification status, latency, model used
- **Execution Graph sidebar** — see every atomic task, which engine handled it, and its result
- **Compare Mode** — toggle to see VERA output vs. raw LLM output side by side

---

## LLM Provider Support

| Provider | Config |
|---|---|
| **OpenAI** | `api_key=sk-...`, `base_url=null` |
| **LM Studio (local)** | `api_key=lm-studio`, `base_url=http://HOST:1234/v1` |
| **Any OpenAI-compatible API** | Set `base_url` to your endpoint |

The Settings modal includes a **🔍 Fetch Models** button that auto-detects available models from your LM Studio server.

---

## API Reference

VERA exposes an **OpenAI-compatible REST API** — it's a drop-in replacement:

```python
# Before (direct OpenAI)
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model="gpt-4o", messages=[...])

# After (via VERA — same format, verified output)
import requests
response = requests.post("http://localhost:8000/v1/chat/completions", json={
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Your prompt"}]
})
```

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | OpenAI-compatible, returns verified response + `vera_metadata` |
| `POST` | `/vera/process` | Full VERA response with complete execution graph |
| `POST` | `/api/compare` | Side-by-side: VERA response vs direct LLM response |
| `POST` | `/api/configure` | Set API key, model, base URL at runtime |
| `GET`  | `/api/config` | Current configuration (key never returned) |
| `POST` | `/api/fetch-models` | Probe an LM Studio server and return its model list |
| `GET`  | `/health` | Liveness check |
| `GET`  | `/docs` | Interactive Swagger API docs |

### Response format

```json
{
  "choices": [{"message": {"role": "assistant", "content": "..."}}],
  "vera_metadata": {
    "verified": true,
    "confidence": 0.92,
    "latency_ms": 312,
    "model_used": "llama-3.2-1b-instruct",
    "execution_graph": {
      "tasks": {"task_0": {"type": "math", "engine": "deterministic_sandbox", "result": "300"}},
      "execution_order": ["task_0"]
    },
    "verification_results": [
      {"task_id": "task_0", "verified": true, "confidence": 0.99, "details": "Deterministic sandbox result verified"}
    ]
  }
}
```

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full technical deep-dive.

```
vera/
├── segmenter.py    # Parses prompts → DAG of atomic tasks
├── router.py       # Classifies tasks → assigns execution engines
├── engines.py      # DeterministicSandbox · RAGEngine · SemanticEngine
├── arbitrator.py   # Verifies results · synthesises final response
├── core.py         # VERACore orchestrator (main entry point)
├── server.py       # FastAPI server (REST API + web UI serving)
└── client.py       # Python client library
```

---

## Testing

```bash
# Unit tests (no API key needed)
python -m pytest tests/ -v -m "not integration and not network"

# With internet (Wikipedia RAG tests)
python -m pytest tests/ -v -m "not integration"

# Full suite (requires API key)
python -m pytest tests/ -v
```

---

## Docker

```bash
docker build -t vera:latest .
docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 vera:latest
```

---

## Patent

VERA is covered by a WIPO PCT patent application.
See [`docs/PATENT.md`](docs/PATENT.md) for full claims.

**Title:** *System and Method for Segmented Neuro-Symbolic Routing and Verification of Large Language Model Prompts*

---

## Presentation

📊 [`docs/presentation/VERA_Presentation.pptx`](docs/presentation/VERA_Presentation.pptx)

*Radically Enhancing LLM Outcomes Through Segmented Neuro-Symbolic Routing*

---

## License

VERA is proprietary software. All rights reserved.
© 2026 Dr. Rami Shaheen

For licensing inquiries: rami@vera-ai.com

---

*VERA: Transform LLMs into Production-Ready Infrastructure*
