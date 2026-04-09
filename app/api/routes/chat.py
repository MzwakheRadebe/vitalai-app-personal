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

    Returns a symptom-aware, severity-specific response built from
    the ML model's predicted_severity + the user's actual symptoms.
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

        if severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            return None

        return _build_response(prompt, severity, conf_pct)
    except Exception:
        return None


def _build_response(prompt: str, severity: str, conf_pct: int = 0) -> str:
    """Build a symptom-aware, human-sounding triage response.

    Detects the symptom type from the user's message and tailors
    the advice to match — so headache advice differs from chest pain advice.
    """
    p = prompt.lower()

    # -- Detect symptom category --
    is_head    = any(w in p for w in ["headache", "migraine", "head", "forehead", "temple"])
    is_chest   = any(w in p for w in ["chest", "heart", "palpitation", "breathing", "breath", "inhale", "exhale"])
    is_fever   = any(w in p for w in ["fever", "temperature", "chills", "sweating", "hot"])
    is_stomach = any(w in p for w in ["stomach", "nausea", "vomit", "diarrhea", "abdomen", "bloat", "cramp", "bowel"])
    is_throat  = any(w in p for w in ["throat", "swallow", "tonsil", "hoarse", "voice"])
    is_cough   = any(w in p for w in ["cough", "wheeze", "phlegm", "mucus", "congestion"])
    is_injury  = any(w in p for w in ["cut", "wound", "burn", "fracture", "broken", "bleeding", "fall", "injury", "swollen"])
    is_mental  = any(w in p for w in ["anxiety", "panic", "stress", "depression", "suicide", "self-harm", "mental"])
    is_appt    = any(w in p for w in ["appointment", "book", "schedule", "doctor", "clinic", "hospital"])

    conf_str = f" (model confidence: {conf_pct}%)" if conf_pct else ""

    # -- Appointment request (any severity) --
    if is_appt:
        return (
            "📅 I can help you book an appointment.\n\n"
            "Click the **Schedule Appointment** button below to choose your preferred department, date, and time slot.\n\n"
            "Departments available: General Practice · Cardiology · Paediatrics · ENT · Orthopaedics · Mental Health · Gynaecology\n\n"
            "If this is an emergency, please call **10177** or **112** instead of booking."
        )

    # -- Mental health (handle sensitively regardless of severity) --
    if is_mental:
        return (
            "💙 I hear you, and I want you to know your feelings are valid.\n\n"
            f"Severity assessment: **{severity}**{conf_str}\n\n"
            "Please reach out for support:\n"
            "• **SADAG Helpline:** 0800 456 789 (free, 24/7)\n"
            "• **Lifeline SA:** 0861 322 322\n"
            "• Talk to a trusted person — a friend, family member, or counsellor\n"
            "• Book a session with a mental health professional via the Schedule Appointment button\n\n"
            "You are not alone. ⚠️ VitalAI does not replace professional mental health care."
        )

    # -- CRITICAL --
    if severity == "CRITICAL":
        if is_chest:
            detail = "Chest-related symptoms at this severity level could indicate a heart attack, pulmonary embolism, or severe respiratory failure."
        elif is_head:
            detail = "Severe head symptoms can signal a stroke, brain bleed, or dangerous spike in blood pressure."
        elif is_injury:
            detail = "The injury you've described may involve serious blood loss or internal damage."
        else:
            detail = "Your symptoms suggest a potentially life-threatening condition that needs immediate evaluation."

        return (
            f"🔴 CRITICAL — Seek Emergency Care Now{conf_str}\n\n"
            f"{detail}\n\n"
            "**Do this right now:**\n"
            "• Call **10177** (ambulance) or **112** (emergency) immediately\n"
            "• Do NOT drive yourself — call someone or wait for emergency services\n"
            "• If you are alone, unlock your front door so paramedics can enter\n"
            "• Stay as calm and still as possible\n\n"
            "⚠️ VitalAI is an AI-powered assistant. This is not a substitute for emergency medical care."
        )

    # -- HIGH --
    if severity == "HIGH":
        if is_chest:
            advice = (
                "Chest tightness, pressure, or pain — especially with shortness of breath — needs same-day evaluation.\n\n"
                "• Go to your nearest hospital or emergency clinic today\n"
                "• Do not ignore this or wait to see if it passes\n"
                "• Avoid physical exertion until you've been assessed\n"
                "• If pain intensifies or spreads to your arm or jaw, call 10177 immediately"
            )
        elif is_head:
            advice = (
                "A severe or rapidly worsening headache — especially with vision changes, vomiting, or stiff neck — is a red flag.\n\n"
                "• Visit a hospital or urgent care clinic today\n"
                "• Note when the headache started and how fast it came on\n"
                "• Avoid bright lights and loud environments\n"
                "• Do not take more than the recommended dose of pain medication"
            )
        elif is_fever:
            advice = (
                "A high fever can lead to dehydration, febrile seizures, or indicate a serious infection.\n\n"
                "• Go to a clinic or hospital today — do not wait\n"
                "• Keep taking fluids — water, oral rehydration solution (ORS), or broth\n"
                "• Take paracetamol/ibuprofen to manage temperature if not allergic\n"
                "• Bring your temperature readings and any medication you've taken"
            )
        elif is_injury:
            advice = (
                "Your injury sounds serious and needs proper medical assessment.\n\n"
                "• Go to the nearest emergency room or trauma clinic\n"
                "• If bleeding: apply firm pressure with a clean cloth\n"
                "• Do not attempt to realign bones or remove embedded objects\n"
                "• Keep the injured area as still as possible while travelling"
            )
        elif is_stomach:
            advice = (
                "Severe abdominal symptoms can indicate appendicitis, bowel obstruction, or internal bleeding.\n\n"
                "• Go to a hospital or urgent clinic today\n"
                "• Avoid eating or drinking until evaluated (in case surgery is needed)\n"
                "• Note the exact location of the pain and when it started\n"
                "• Tell the doctor if you have any blood in your stool or vomit"
            )
        else:
            advice = (
                "Your symptoms are serious enough to need same-day medical attention.\n\n"
                "• Visit your nearest clinic or hospital today\n"
                "• Bring your ID, medical aid card, and a list of any current medications\n"
                "• Try to have someone accompany you\n"
                "• Do not delay — early care leads to better outcomes"
            )
        return (
            f"🟠 HIGH Severity{conf_str}\n\n"
            f"{advice}\n\n"
            "⚠️ VitalAI is an AI-powered assistant. Always follow advice from a qualified healthcare professional."
        )

    # -- MEDIUM --
    if severity == "MEDIUM":
        if is_head:
            advice = (
                "A persistent or worsening headache that doesn't respond to over-the-counter pain relief needs a doctor's attention.\n\n"
                "• Book a doctor's appointment within the next 1–2 days\n"
                "• Track how often headaches occur and what triggers them\n"
                "• Avoid screens and bright light if they worsen the pain\n"
                "• Try paracetamol or ibuprofen if you have no contraindications"
            )
        elif is_fever:
            advice = (
                "A moderate fever suggests your body is fighting an infection. Monitor it closely.\n\n"
                "• Keep taking fluids throughout the day\n"
                "• Take paracetamol to bring the fever down if above 38.5°C\n"
                "• Book a clinic visit if the fever lasts more than 2 days or rises above 39°C\n"
                "• Avoid contact with vulnerable people (elderly, infants) while unwell"
            )
        elif is_throat or is_cough:
            advice = (
                "Throat and cough symptoms at this level may be a respiratory infection that needs treatment.\n\n"
                "• See a doctor within the next day or two — you may need antibiotics or antivirals\n"
                "• Gargle with warm salt water for throat pain\n"
                "• Stay away from work or school to avoid spreading illness\n"
                "• Avoid smoking or second-hand smoke while recovering"
            )
        elif is_stomach:
            advice = (
                "Stomach-related symptoms that persist need to be checked by a doctor.\n\n"
                "• Stick to bland foods — toast, rice, bananas, boiled potatoes\n"
                "• Keep drinking fluids, especially oral rehydration solution if you're vomiting\n"
                "• Book a clinic visit if symptoms don't improve within 48 hours\n"
                "• Avoid dairy, caffeine, and spicy food until you feel better"
            )
        elif is_injury:
            advice = (
                "Your injury should be properly assessed by a healthcare professional.\n\n"
                "• Visit a clinic or GP within the next 24 hours\n"
                "• Keep the area clean and covered with a sterile bandage\n"
                "• Elevate the injured area to reduce swelling if possible\n"
                "• Watch for signs of infection: increasing redness, warmth, or discharge"
            )
        else:
            advice = (
                "Your symptoms are worth having checked — don't leave them unaddressed.\n\n"
                "• Book an appointment with a doctor within the next 1–2 days\n"
                "• Use the Schedule Appointment button below to book at your nearest clinic\n"
                "• Take note of when symptoms started and anything that makes them better or worse\n"
                "• Avoid strenuous activity until you've been assessed"
            )
        return (
            f"🟡 MEDIUM Severity{conf_str}\n\n"
            f"{advice}\n\n"
            "⚠️ VitalAI is an AI-powered assistant. Always consult a qualified healthcare provider for diagnosis."
        )

    # -- LOW --
    if is_head:
        advice = (
            "A mild headache is usually nothing serious.\n\n"
            "• Take paracetamol or ibuprofen if needed\n"
            "• Drink a glass of water — dehydration is a very common trigger\n"
            "• Step away from screens and rest your eyes for 20–30 minutes\n"
            "• If the headache keeps coming back, keep a headache diary to share with your doctor"
        )
    elif is_fever:
        advice = (
            "A low-grade fever means your immune system is active — that's a good sign.\n\n"
            "• Keep drinking fluids — water, warm tea, or soup\n"
            "• Rest and avoid strenuous activity\n"
            "• Take paracetamol if you feel uncomfortable\n"
            "• See a doctor if the fever rises above 38.5°C or lasts more than 3 days"
        )
    elif is_cough or is_throat:
        advice = (
            "Mild throat or cough symptoms are common and usually self-limiting.\n\n"
            "• Gargle with warm salt water a few times a day\n"
            "• Sip warm fluids — honey and lemon tea can soothe a sore throat\n"
            "• Avoid talking loudly or in cold air\n"
            "• See a doctor if symptoms persist beyond 5–7 days or you develop a fever"
        )
    elif is_stomach:
        advice = (
            "Mild stomach discomfort is usually short-lived.\n\n"
            "• Avoid rich, greasy, or spicy food for the rest of the day\n"
            "• Peppermint tea or ginger tea can help ease nausea\n"
            "• Stay upright for at least 30 minutes after eating\n"
            "• See a doctor if you notice blood in your stool or vomit, or pain that intensifies"
        )
    elif is_injury:
        advice = (
            "Minor cuts, scrapes, and bruises can be managed at home.\n\n"
            "• Clean the area with clean water and mild soap\n"
            "• Apply an antiseptic and cover with a clean plaster or bandage\n"
            "• Change the dressing once a day and keep it dry\n"
            "• See a doctor if the wound shows signs of infection or doesn't heal within a week"
        )
    else:
        advice = (
            "Based on what you've described, this doesn't seem urgent right now.\n\n"
            "• Pay attention to how you feel over the next day or two\n"
            "• If any new symptoms appear or existing ones worsen, come back and describe them\n"
            "• Maintaining a healthy routine — sleep, nutrition, movement — supports recovery\n"
            "• If you're unsure, it's always okay to book a check-up"
        )

    return (
        f"🟢 LOW Severity{conf_str}\n\n"
        f"{advice}\n\n"
        "⚠️ VitalAI is an AI-powered assistant. If you're ever in doubt, consult a healthcare professional."
    )


def _keyword_triage(prompt: str) -> str:
    """Last-resort fallback when both OpenAI and ML model are unavailable."""
    p = prompt.lower()
    if any(w in p for w in ["chest pain", "heart attack", "can't breathe", "stroke", "unconscious"]):
        return _build_response(prompt, "CRITICAL")
    if any(w in p for w in ["severe", "vomiting blood", "bleeding heavily", "fracture", "seizure", "collapse"]):
        return _build_response(prompt, "HIGH")
    if any(w in p for w in ["fever", "headache", "pain", "sore throat", "cough", "nausea", "dizzy", "fatigue"]):
        return _build_response(prompt, "MEDIUM")
    if any(w in p for w in ["appointment", "book", "schedule", "doctor", "clinic"]):
        return _build_response(prompt, "LOW")
    return _build_response(prompt, "LOW")