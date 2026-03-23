# VERA Installation Guide

## Requirements

- Python 3.11+
- pip
- Internet connection (for Wikipedia RAG; not needed for math/LM Studio)
- An LLM API key **or** LM Studio running locally

---

## Option A — OpenAI (Cloud)

### 1. Clone and install
```bash
git clone https://github.com/ramishaheen/VERA.git
cd VERA
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-openai-key
VERA_MODEL=gpt-4o-mini
```

### 3. Start
```bash
python run.py
```

Opens `http://localhost:8000` in your browser.

---

## Option B — LM Studio (Local / Offline)

LM Studio lets you run open-source LLMs (LLaMA, Mistral, Phi, etc.) on your own machine with no API costs.

### 1. Install LM Studio
Download from https://lmstudio.ai and install a model (e.g. `llama-3.2-1b-instruct`).

### 2. Start the Local Server in LM Studio
- Open LM Studio → **Local Server** tab
- Load your model
- Click **Start Server** (default port: 1234)

### 3. Configure VERA
```env
OPENAI_API_KEY=lm-studio
VERA_MODEL=llama-3.2-1b-instruct
VERA_BASE_URL=http://localhost:1234/v1
```

For LM Studio on a different machine:
```env
VERA_BASE_URL=http://192.168.100.39:1234/v1
```

### 4. Start
```bash
python run.py
```

### 5. Auto-detect model name
In the VERA web UI: **⚙ Settings → LM Studio → 🔍 Fetch Models**

This queries your LM Studio server and auto-populates the exact model identifier.

---

## Option C — Docker

```bash
# OpenAI
docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 ghcr.io/ramishaheen/vera:latest

# LM Studio (assuming LM Studio runs on the host)
docker run \
  -e OPENAI_API_KEY=lm-studio \
  -e VERA_MODEL=llama-3.2-1b-instruct \
  -e VERA_BASE_URL=http://host.docker.internal:1234/v1 \
  -p 8000:8000 \
  ghcr.io/ramishaheen/vera:latest
```

Build locally:
```bash
docker build -t vera:latest .
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your API key. Use `"lm-studio"` for LM Studio. |
| `VERA_MODEL` | `gpt-4o-mini` | Default model name |
| `VERA_BASE_URL` | *(empty)* | Custom base URL. Empty = OpenAI. |
| `VERA_HOST` | `0.0.0.0` | Server bind host |
| `VERA_PORT` | `8000` | Server port |

---

## Troubleshooting

### "Connection refused" when calling the API
Make sure `python run.py` is running and check the port is not in use:
```bash
netstat -an | findstr 8000
```

### "Could not reach LM Studio"
- Ensure LM Studio's Local Server is started (green status)
- Check the IP/port is correct — use **🔍 Fetch Models** to probe it
- On Windows, check the firewall allows port 1234

### "No user message found"
Ensure your request JSON contains at least one message with `"role": "user"`.

### Math gives "Could not extract mathematical expression"
VERA now falls back to the LLM automatically for incomplete math prompts. Provide numbers for precise deterministic results (e.g. "10000 at 5% for 3 years").
