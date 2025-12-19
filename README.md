# Premium Secure AI Backend – README

A **production-grade**, **Zero-Trust**, **GPU-aware** AI-inference API that exposes **OpenAI** and **local Ollama** models (Phi, Llama-2, Mistral, etc.) through a **single hardened endpoint**.

| Key Pillars |
|-------------|
| 🔐 **Argon2** password hashing (GPU-resistant) |
| 🛡️ **Zero-Trust** mindset – every request is hostile until proven otherwise |
| 🔥 **LLM-Firewall** – prompt-injection / PII / toxicity blocking **before** the model |
| ⚡ **Scoped JWTs** – 60 s tokens, least-privilege, no long-lived secrets |
| 🕵️ **Full audit trail** – every access & inference is JSON-logged |
| 🚀 **Ollama-ready** – run **Microsoft Phi**, Llama-2, Mistral **locally** with **same security** |
| 📊 **Multi-dimensional rate-limit** – requests + tokens + GPU-seconds |
| 🔌 **Docker-Compose** – one command → Redis + API + Ollama (optional) |

---

## Why Argon2 & Zero-Trust?

| Threat | Classic Approach | This Project |
|--------|------------------|--------------|
| **Credential stuffing** | bcrypt/SHA-1 | **Argon2-id** (`memory=128 MB`, `parallelism=8`) – kills GPU crackers |
| **Token abuse** | permanent API keys | **60-s scoped JWT** (`scope:["llm:generate"]`, `max_tokens`) |
| **Prompt injection** | log after damage | **Infra-level firewall** blocks **before** inference |
| **GPU-DoS** | none | **Token cap + timeout + queue isolation** |
| **Data exfiltration** | open vector DB | **Per-user namespace + query limits** |
| **Insider trust** | flat network | **Zero-Trust** – no implicit trust, full audit |

---

## Quick Start (no Docker)

### 1. Prerequisites
- Python ≥ 3.10
- Ollama installed & running (`ollama serve`)
- Pull Phi (or any model):

```bash
ollama pull phi        # or llama2, mistral …
```

### 2. Clone & install
```bash
git clone <repo>
cd Secure-AI-System-Architecture
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure
Copy `.env.example` → `.env` and adjust:

```env
SECRET_KEY=change-me-256-bit
REDIS_URL=redis://localhost:6379/0   # optional (disable for quick test)
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Start
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 30-Second Smoke Test (Postman / cURL)

| Step | Request | Postman Body / Headers |
|------|---------|------------------------|
| **Login** | `POST /auth/login` | `{"username":"admin","password":"secure_admin_pass"}` |
| **Scoped token** | `POST /auth/scoped-token` | **Bearer** `<userToken>`<br>`{"model":"phi","max_tokens":128,"scopes":["llm:generate"]}` |
| **Generate** | `POST /api/v1/llm/generate` | **Headers:** `X-LLM-Token: <llmToken>`<br>**Body:** `{"prompt":"Explain zero-trust.","model":"phi","max_tokens":64}` |

**Response:**
```json
{
  "content": "Zero-trust security assumes no user or device is trustworthy by default...",
  "model": "phi",
  "tokens_used": 28,
  "latency_ms": 2143
}
```

---

## Docker-Compose (full stack)

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    container_name: secureai_redis
    command: redis-server --save 60 1 --loglevel warning
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5


  api:
    build: .
    container_name: secureai_api
    ports:
      - "8000:8000"
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app

```

Start everything:

```bash
docker compose up -d
docker exec -it <ollama-container> ollama pull phi
```


---

## Security Checklist

| Control | Implementation |
|---------|----------------|
| Password hashing | Argon2-id (GPU/ASIC resistant) |
| Authentication | 15-min user JWT |
| Authorization | 60-s scoped LLM JWT (`scope`, `max_tokens`) |
| Prompt filter | Regex + toxicity + PII detection **before** model |
| Rate limit | Requests / tokens / GPU-seconds (Redis) |
| Audit | Every access & inference logged |
| Transport | TLS (add reverse proxy) |
| Secrets | ENV vars only, no hard-coded keys |

---

## Extending

- Add model: put it in Ollama → add key to `adapters` dict → done.
- Change hash cost: edit `ARGON2_*` vars in `.env`.
- New scope: add to `ScopedTokenRequest` and update zero-trust check.
- Metrics: expose `/metrics` (Prometheus) inside `main.py`.

---

## License

MIT – feel free to embed in commercial or academic projects.

---

**Happy secure prompting!**