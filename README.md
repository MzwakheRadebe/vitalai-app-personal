# AI-Powered Healthcare Chatbot Backend (FastAPI)

FastAPI backend scaffolding for the hospital admin automation system.

## Setup

1. Create a `.env` from `.env.example` and update values.
2. Install Python 3.11+.
3. Install dependencies:

```
pip install -r requirements.txt
```

## Run Locally

```
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open API docs at `http://localhost:8000/docs`.

## Endpoints

- `GET /health` → service health
- `GET /api/health` → API health
- `POST /api/chat` → send a prompt to VitalAI (stub reply)
  - Body: `{ "prompt": "Hello" }`
  - Reply: `{ "reply": "..." }`
  - If `AI_SERVICE_URL` is unreachable, returns a stub echo prefixed with `[stub]`.
- Appointments (SQLite-backed)
  - `GET /api/appointments` → list all appointments (ordered by `starts_at`)
  - `POST /api/appointments` → create appointment `{ patient_name, clinician, starts_at, ends_at }`
    - Conflict rule: for the same `clinician`, times must not overlap. Returns `409` on overlap.
  - `GET /api/appointments/id/{id}` → fetch one
  - `PUT /api/appointments/id/{id}` → update (same conflict rule applies)
  - `DELETE /api/appointments/id/{id}` → delete
- FAQ (SQLite-backed)
  - `GET /api/faq` → list FAQs (seeded with two examples on first run)
  - `POST /api/faq` → create `{ question, answer }`
  - `GET /api/faq/id/{id}` → fetch one
  - `PUT /api/faq/id/{id}` → update
  - `DELETE /api/faq/id/{id}` → delete

## Managed AI (Recommended)

- Default config uses a managed, OpenAI-compatible API for lower setup stress.
- Set these in `.env`:
  - `AI_SERVICE_URL=https://api.openai.com/v1`
  - `AI_MODEL=gpt-4o-mini`
  - `AI_API_KEY=sk-...` (your provider key)
- Restart the server after changes.
- Test:
  - `GET /api/health` shows `ai_backend.url` and basic status.
  - `POST /api/chat` with `{ "prompt": "Hello" }` returns a real model reply when the key is set.

## Observability & Safety (Beginner-Friendly)

- Chat logging: The backend logs `/api/chat` requests with client IP and prompt length, and logs response length. This helps the team debug without exposing content.
- Rate limiting: A naive in-memory per-IP limit (default: 30 requests per 60 seconds) protects local dev. It returns `429` if exceeded. For production, replace with Redis-backed sliding window.

### How to see logs

- Run the server in a terminal. When you call `POST /api/chat`, the terminal prints lines like:
  - `INFO chat: /api/chat request ip=127.0.0.1 prompt_len=23`
  - `INFO chat: /api/chat response ip=127.0.0.1 reply_len=128`
  - If the AI backend is unreachable, you’ll see a warning: `WARNING chat: /api/chat stub-response ...`

### Rate limit testing

- In Swagger, repeatedly click `Execute` on `POST /api/chat` more than 30 times within a minute to see `429 Rate limit exceeded`.
- This limit resets each minute; it’s only meant for beginner local development.

## Developer Notes: Chat Proxy Behavior

- The backend auto-detects whether `AI_SERVICE_URL` is an OpenAI-compatible endpoint or a simple `/chat` service.
- If the URL contains `/v1` or ends with `/v1/chat/completions`, it sends `POST /v1/chat/completions` with:
  - `model`: read from `AI_MODEL` (default `gpt-4o-mini`)
  - `messages`: `[ { role: "user", content: <prompt> } ]`
  - `stream`: `false`
- Otherwise, it sends `POST /chat` with `{ prompt: <prompt> }`.
- Response parsing:
  - OpenAI style: `choices[0].message.content`
  - Simple style: `reply` or `text`
- Any error from the AI backend returns a graceful stub: `{"reply": "[stub] VitalAI received: <prompt>"}`.
  - The stub response is also logged so you can spot connectivity issues quickly.

### Local Example

```
AI_SERVICE_URL=http://localhost:11434/v1
AI_MODEL=llama3.1:latest
```

Then in Swagger, call `POST /api/chat` with body `{ "prompt": "Hello there" }`.
Expected response: `{ "reply": "..." }` from the local AI; if Ollama isn’t running, you’ll get the stub response.

## Configuration

Key environment variables:

- `MYSQL_URL`, `MONGO_URL`, `SQLITE_PATH` (default `./local_offline.db`)
- `JWT_SECRET`, `ENCRYPTION_KEY`
- `ALLOWED_ORIGINS` (comma-separated)
- `AI_SERVICE_URL`

## Next

- Auth (JWT + RBAC)
- Appointments CRUD and availability
- Offline outbox (SQLite) and sync worker
- Triage endpoint contract with AI service
 - Connect `/api/chat` to real AI service at `AI_SERVICE_URL` and add streaming