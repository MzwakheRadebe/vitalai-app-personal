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
        # OpenAI/external AI failed or not configured — try the local trained ML model
        ml_reply = await _call_ml_model(p, settings)
        if ml_reply:
            logger.info("/api/chat ml-model-response ip=%s reply_len=%d", ip, len(ml_reply))
            return ChatResponse(reply=ml_reply)

        # ML model also unavailable — return a structured keyword-based fallback
        reply = _keyword_triage(p)
        logger.warning("/api/chat keyword-fallback ip=%s reply_len=%d", ip, len(reply))
        return ChatResponse(reply=reply)


async def _call_ml_model(prompt: str, settings) -> str | None:
    """Call the team's trained ML triage model at /predict.

    The ML model (ai_and_nlp/non_final_draft.py) runs separately on port 5000
    and returns { predicted_severity, confidence }.
    We format that into a user-friendly reply.
    """
    ml_url = getattr(settings, "ml_model_url", None) or "http://localhost:5000"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{ml_url}/predict", json={"text": prompt})
            r.raise_for_status()
            data = r.json()

        severity = str(data.get("predicted_severity", "")).upper()
        confidence = data.get("confidence", 0)
        conf_pct = int(confidence * 100)

        severity_map = {
            "LOW": (
                "🟢 LOW severity",
                "Your symptoms appear mild. Monitor at home and rest.",
                "• Rest and stay hydrated\n• Monitor symptoms over the next 24–48 hours\n• Visit a clinic if symptoms worsen or persist"
            ),
            "MEDIUM": (
                "🟡 MEDIUM severity",
                "Your symptoms may need medical attention.",
                "• Book an appointment with a doctor soon\n• Use the 'Schedule Appointment' button below\n• Avoid strenuous activity until reviewed"
            ),
            "HIGH": (
                "🟠 HIGH severity",
                "Your symptoms suggest you need urgent medical attention.",
                "• Visit your nearest clinic or hospital today\n• Do not delay — bring your ID and any current medication\n• Call a friend or family member to accompany you"
            ),
            "CRITICAL": (
                "🔴 CRITICAL — Medical Emergency",
                "Your symptoms indicate a potentially life-threatening condition.",
                "• Call emergency services immediately: 10177 or 112\n• Do not drive yourself\n• Stay calm and wait for emergency responders"
            ),
        }

        if severity not in severity_map:
            return None

        label, summary, steps = severity_map[severity]
        return (
            f"{label} (confidence: {conf_pct}%)\n\n"
            f"{summary}\n\n"
            f"Recommended steps:\n{steps}\n\n"
            "⚠️ VitalAI is an AI-powered assistant and does not replace professional medical advice. "
            "Always consult a qualified healthcare provider for diagnosis and treatment."
        )
    except Exception:
        return None


def _keyword_triage(prompt: str) -> str:
    """Last-resort keyword fallback when both AI and ML model are unavailable."""
    p = prompt.lower()

    if any(w in p for w in ["chest pain", "heart attack", "can't breathe", "stroke", "unconscious", "faint"]):
        return (
            "🔴 CRITICAL — This sounds like a medical emergency.\n\n"
            "Please call emergency services (10177 or 112) immediately or go to your nearest emergency room.\n\n"
            "Do not drive yourself. Stay calm and wait for help.\n\n"
            "⚠️ VitalAI is an AI-powered assistant and does not replace professional medical advice."
        )
    if any(w in p for w in ["severe", "vomiting blood", "bleeding", "fracture", "seizure", "collapse"]):
        return (
            "🟠 HIGH severity detected.\n\n"
            "Your symptoms suggest you need urgent medical attention.\n\n"
            "• Visit your nearest clinic or hospital today\n"
            "• Do not wait if symptoms worsen\n"
            "• Bring your ID and any current medication\n\n"
            "⚠️ VitalAI is an AI-powered assistant and does not replace professional medical advice."
        )
    if any(w in p for w in ["fever", "headache", "pain", "sore throat", "cough", "nausea", "dizzy", "fatigue", "flu"]):
        return (
            "🟡 MEDIUM severity.\n\n"
            "Your symptoms are worth monitoring and may need medical attention.\n\n"
            "• Rest and stay hydrated\n"
            "• Monitor your temperature if you have a fever\n"
            "• Book a doctor's appointment if symptoms persist beyond 2 days\n"
            "• Use the 'Schedule Appointment' button below to book\n\n"
            "⚠️ VitalAI is an AI-powered assistant and does not replace professional medical advice."
        )
    if any(w in p for w in ["appointment", "book", "schedule", "doctor", "clinic", "hospital"]):
        return (
            "📅 I can help you schedule an appointment!\n\n"
            "Click the 'Schedule Appointment' button below to choose a department, date, and time.\n\n"
            "Available departments include General Practice, Cardiology, Paediatrics, and more."
        )
    return (
        "🟢 LOW concern based on your description.\n\n"
        "General advice:\n"
        "• Rest and drink plenty of fluids\n"
        "• Monitor your symptoms over the next 24 hours\n"
        "• Consult a healthcare professional if symptoms worsen\n\n"
        "⚠️ VitalAI is an AI-powered assistant and does not replace professional medical advice."
    )