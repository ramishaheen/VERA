# VERA API Reference

Base URL: `http://localhost:8000` (default)

Interactive docs: `http://localhost:8000/docs`

---

## Authentication

VERA itself does not require authentication for local deployment. The API key you configure is forwarded to the downstream LLM provider.

---

## Endpoints

### POST `/v1/chat/completions`
OpenAI-compatible endpoint. Drop-in replacement for OpenAI's Chat Completions API.

**Request**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Calculate 15% of 2000"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

**Response**
```json
{
  "id": "vera-0a1b2c3d",
  "object": "chat.completion",
  "created": 1742000000,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "Calculate 15% of 2000: 300"},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 6,
    "completion_tokens": 6,
    "total_tokens": 12
  },
  "vera_metadata": {
    "verified": true,
    "confidence": 0.99,
    "latency_ms": 14.3,
    "model_used": "llama-3.2-1b-instruct",
    "execution_graph": {
      "tasks": {
        "task_0": {
          "id": "task_0",
          "type": "math",
          "engine": "deterministic_sandbox",
          "content": "Calculate 15% of 2000",
          "result": "300",
          "verified": true,
          "dependencies": []
        }
      },
      "execution_order": ["task_0"],
      "metadata": {
        "original_prompt": "Calculate 15% of 2000",
        "num_tasks": 1,
        "task_types": ["math"]
      }
    },
    "verification_results": [
      {
        "task_id": "task_0",
        "verified": true,
        "confidence": 0.99,
        "details": "Deterministic sandbox result verified"
      }
    ]
  }
}
```

---

### POST `/vera/process`
Full VERA response including complete execution graph and verification details.

**Request** — same as `/v1/chat/completions`

**Response**
```json
{
  "response": "Calculate 15% of 2000: 300",
  "verified": true,
  "confidence": 0.99,
  "latency_ms": 14.3,
  "model_used": "llama-3.2-1b-instruct",
  "execution_graph": { ... },
  "verification_results": [ ... ]
}
```

---

### POST `/api/compare`
Returns both a VERA-processed response and a direct LLM response for the same prompt. Useful for demonstrating VERA's value.

**Request** — same as `/v1/chat/completions`

**Response**
```json
{
  "vera": {
    "response": "Calculate 15% of 2000: 300",
    "verified": true,
    "confidence": 0.99,
    "latency_ms": 14.3,
    "execution_graph": { ... },
    "verification_results": [ ... ]
  },
  "direct": {
    "response": "15% of 2000 is 300.",
    "verified": false,
    "confidence": null,
    "latency_ms": null
  }
}
```

---

### POST `/api/configure`
Update LLM configuration at runtime. No server restart required.

**Request**
```json
{
  "api_key": "sk-your-key",
  "model": "gpt-4o-mini",
  "base_url": "http://192.168.100.39:1234/v1"
}
```
All fields optional. Omit `base_url` for OpenAI default.

**Response**
```json
{
  "status": "configured",
  "model": "gpt-4o-mini",
  "provider": "openai"
}
```
Provider values: `"openai"` | `"lm_studio"` | `"custom"`

---

### GET `/api/config`
Returns current configuration. The API key is **never returned**.

**Response**
```json
{
  "model": "llama-3.2-1b-instruct",
  "provider": "lm_studio",
  "base_url": "http://192.168.100.39:1234/v1",
  "api_key_set": true
}
```

---

### POST `/api/fetch-models`
Probe an LM Studio (or any OpenAI-compatible) server and return its available models. Used by the web UI's "Fetch Models" button.

**Request**
```json
{
  "base_url": "http://192.168.100.39:1234",
  "api_key": "lm-studio"
}
```
The `/v1` suffix is added automatically — pass the bare host:port.

**Response**
```json
{
  "status": "ok",
  "base_url": "http://192.168.100.39:1234/v1",
  "models": [
    "llama-3.2-1b-instruct",
    "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b",
    "text-embedding-nomic-embed-text-v1.5"
  ]
}
```

---

### GET `/health`
Liveness probe.

**Response**
```json
{"status": "healthy", "version": "1.0.0", "timestamp": 1742000000}
```

---

### GET `/v1/models` and `/vera/models`
List models known to VERA.

---

## Python Client

```python
from vera.client import VERAClient

client = VERAClient(base_url="http://localhost:8000")

# OpenAI-compatible
response = client.chat_completions(
    messages=[{"role": "user", "content": "Calculate 10% of 500"}],
    model="llama-3.2-1b-instruct"
)
print(response["choices"][0]["message"]["content"])
print(response["vera_metadata"]["confidence"])

# Full VERA response
response = client.vera_process(
    messages=[{"role": "user", "content": "Who is Marie Curie?"}]
)
print(response["response"])
print(response["verified"])

# Configure at runtime
client.configure(
    api_key="sk-...",
    model="gpt-4o-mini",
    base_url=None  # use OpenAI default
)

# Health check
print(client.health_check())
```

---

## Error Responses

```json
{
  "detail": "No user message found in messages list"
}
```

| HTTP Code | Meaning |
|---|---|
| `400` | Bad request (empty prompt, missing user message) |
| `502` | Could not reach the configured LLM endpoint |
| `500` | Internal VERA error |
