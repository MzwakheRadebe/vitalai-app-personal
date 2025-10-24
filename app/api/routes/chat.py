"""Chat route

This module exposes a minimal chat endpoint that proxies to a configurable
AI backend. It supports two styles of backends:

1) Simple backends expecting `{ "prompt": "..." }` at `POST /chat`
2) OpenAI-compatible backends at `POST /v1/chat/completions` which expect
   `{ model, messages: [{ role, content }], ... }` and reply with
   `choices[0].message.content`.

If the AI backend is unreachable or errors, we return a graceful stub
response so the rest of the API and docs remain functional.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import httpx
import logging
from time import monotonic
from app.config import get_settings


router = APIRouter(prefix="/chat")
logger = logging.getLogger("chat")

# Naive in-memory rate limiter (per-IP), suitable for beginner local dev.
# For production, use a proper store (Redis) and sliding window algorithm.
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 30
_rate_state: dict[str, tuple[float, int]] = {}


class ChatRequest(BaseModel):
    """Incoming chat request with a single `prompt`.

    Keep this simple; downstream AI services can format complex prompts
    themselves. If we need system/assistant roles later, extend here.
    """
    prompt: str = Field(
        ..., min_length=1, max_length=1000,
        description="User message (1–1000 characters)."
    )


class ChatResponse(BaseModel):
    """Outgoing response with a single `reply` string."""
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    # Load runtime configuration (reads from `.env` via pydantic-settings)
    settings = get_settings()
    base = settings.ai_service_url.rstrip("/")

    # Basic input validation (extra safety beyond Pydantic constraints)
    p = req.prompt.strip()
    if not p:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    if len(p) > 1000:
        raise HTTPException(status_code=400, detail="Prompt exceeds 1000 characters")

    # Naive per-IP rate limiting (in-memory, resets every window)
    ip = request.client.host if request.client else "unknown"
    now = monotonic()
    start, count = _rate_state.get(ip, (now, 0))
    if now - start > RATE_LIMIT_WINDOW_SECONDS:
        start, count = now, 0
    count += 1
    _rate_state[ip] = (start, count)
    if count > RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    # Log inbound prompt length and client IP for team visibility
    logger.info(f"/api/chat request ip=%s prompt_len=%d", ip, len(p))

    # Local AI hook removed to avoid confusion; relying on external AI or stub.

    # Decide protocol: OpenAI-compatible vs simple `/chat`.
    # We detect `/v1` in the URL to decide payload/response parsing.
    use_openai = base.endswith("/v1") or "/v1" in base or base.endswith("/v1/chat/completions")
    if use_openai:
        target = base if base.endswith("/v1/chat/completions") else f"{base}/chat/completions"
    else:
        target = f"{base}/chat"

    try:
        # Single outbound call with a short timeout; increase if your backend is slow.
        # Include Authorization header if AI_API_KEY is configured.
        headers = {}
        if settings.ai_api_key:
            headers["Authorization"] = f"Bearer {settings.ai_api_key}"

        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            if use_openai:
                payload = {
                    "model": settings.ai_model,
                    "messages": [{"role": "user", "content": p}],
                    "stream": False,
                }
            else:
                payload = {"prompt": p}

            r = await client.post(target, json=payload)
            r.raise_for_status()
            data = r.json()

            if use_openai:
                try:
                    reply = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content")
                    )
                except Exception:
                    reply = None
            else:
                reply = data.get("reply") or data.get("text")

            if not reply:
                reply = str(data)
            logger.info("/api/chat response ip=%s reply_len=%d", ip, len(reply))
            return ChatResponse(reply=reply)
    except Exception:
        # Graceful fallback so the endpoint works even without an AI service.
        # This keeps docs usable and confirms request plumbing during local dev.
        stub = f"[stub] VitalAI received: {p}"
        logger.warning("/api/chat stub-response ip=%s reply_len=%d", ip, len(stub))
        return ChatResponse(reply=stub)