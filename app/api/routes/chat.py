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

    # Per-IP rate limiting — respect X-Forwarded-For for deployments behind proxies
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
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
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are VitalAI, a medical triage assistant for South African clinics and hospitals. "
                                "When a user describes symptoms, assess the severity and respond with: "
                                "1) A brief, clear explanation of what the symptoms may indicate. "
                                "2) A severity level: LOW (monitor at home), MEDIUM (see a doctor soon), "
                                "HIGH (urgent medical attention needed), or CRITICAL (go to emergency immediately). "
                                "3) Practical next steps. "
                                "Always remind users you are an AI assistant and not a substitute for professional medical advice. "
                                "Keep responses concise and easy to understand."
                            ),
                        },
                        {"role": "user", "content": p},
                    ],
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
        # No AI service configured or unreachable — return a smart demo response
        # based on keywords so users can test the full flow without an API key.
        reply = _demo_triage(p)
        logger.warning("/api/chat demo-response ip=%s reply_len=%d", ip, len(reply))
        return ChatResponse(reply=reply)


def _demo_triage(prompt: str) -> str:
    """Keyword-based triage used when no AI service is configured.

    Gives realistic-looking responses for local development and demos.
    Replace with a real AI key in production for accurate medical guidance.
    """
    p = prompt.lower()

    if any(w in p for w in ["chest pain", "heart attack", "can't breathe", "cannot breathe", "stroke", "unconscious", "faint"]):
        return (
            "🔴 CRITICAL — This sounds like a medical emergency.\n\n"
            "Please call emergency services (10177 or 112) immediately or go to your nearest emergency room.\n\n"
            "Do not drive yourself. Stay calm and keep the person still until help arrives.\n\n"
            "⚠️ VitalAI is an AI assistant — always seek immediate professional help in emergencies."
        )

    if any(w in p for w in ["high fever", "severe", "vomiting blood", "bleeding", "broken", "fracture", "seizure", "collapse"]):
        return (
            "🟠 HIGH severity detected.\n\n"
            f"Your symptoms ({prompt}) suggest you need urgent medical attention.\n\n"
            "Next steps:\n"
            "• Visit your nearest clinic or hospital today\n"
            "• Do not wait if symptoms worsen\n"
            "• Bring your ID and any current medication\n\n"
            "⚠️ VitalAI is an AI assistant and not a substitute for professional medical advice."
        )

    if any(w in p for w in ["fever", "headache", "pain", "sore throat", "cough", "nausea", "dizzy", "tired", "fatigue", "flu", "cold"]):
        return (
            "🟡 MEDIUM severity.\n\n"
            f"Your symptoms ({prompt}) are worth monitoring and may need medical attention.\n\n"
            "Next steps:\n"
            "• Rest and stay hydrated\n"
            "• Monitor your temperature if you have a fever\n"
            "• Book an appointment with a doctor if symptoms persist beyond 2 days\n"
            "• You can use the 'Schedule Appointment' button below to book one\n\n"
            "⚠️ VitalAI is an AI assistant and not a substitute for professional medical advice."
        )

    if any(w in p for w in ["appointment", "book", "schedule", "doctor", "clinic", "hospital"]):
        return (
            "📅 I can help you schedule an appointment!\n\n"
            "Click the 'Schedule Appointment' button below to choose a department, date, and time.\n\n"
            "Available departments include General Practice, Cardiology, Paediatrics, and more."
        )

    # General / unclear symptoms
    return (
        "🟢 LOW concern based on your description.\n\n"
        f"I've noted your message: \"{prompt}\"\n\n"
        "General advice:\n"
        "• Rest and drink plenty of fluids\n"
        "• Monitor your symptoms over the next 24 hours\n"
        "• If symptoms worsen or new ones appear, consult a healthcare professional\n\n"
        "💡 Tip: For a more accurate assessment, connect an AI API key in your settings.\n"
        "⚠️ VitalAI is an AI assistant and not a substitute for professional medical advice."
    )