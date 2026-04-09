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
from app.triage_conditions import CRITICAL_KEYWORDS, HIGH_KEYWORDS


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
    """Outgoing chat response — includes severity and confidence for the frontend badge."""
    reply: str
    severity: str = ""       # LOW | MEDIUM | HIGH | CRITICAL | ""
    confidence: int = 0      # 0–100 percentage


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
        result = await _call_ml_model(p, settings)
        if result:
            reply, severity, conf = result
            logger.info("/api/chat ml-model-response ip=%s reply_len=%d", ip, len(reply))
            return ChatResponse(reply=reply, severity=severity, confidence=conf)

        # ML model also unavailable — return a structured keyword-based fallback
        severity, reply = _keyword_triage(p)
        logger.warning("/api/chat keyword-fallback ip=%s reply_len=%d", ip, len(reply))
        return ChatResponse(reply=reply, severity=severity, confidence=0)


def _force_severity(prompt: str) -> str | None:
    """Override the ML model when it under-classifies clearly serious symptoms.

    Uses the comprehensive keyword lists from app.triage_conditions which cover
    150+ clinical scenarios across all major body systems.

    Priority: CRITICAL > HIGH > (None — ML model decides)
    """
    p = prompt.lower()

    if any(k in p for k in CRITICAL_KEYWORDS):
        return "CRITICAL"

    if any(k in p for k in HIGH_KEYWORDS):
        return "HIGH"

    return None  # Let the ML model decide


async def _call_ml_model(prompt: str, settings) -> tuple[str, str, int] | None:
    """Call the team's trained ML triage model at /predict.

    Returns (reply, severity, confidence_pct) or None if unavailable.
    Applies severity overrides for keywords the model may under-classify.
    """
    ml_url = getattr(settings, "ml_model_url", None) or "http://localhost:5000"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{ml_url}/predict", json={"text": prompt})
            r.raise_for_status()
            data = r.json()

        ml_severity = str(data.get("predicted_severity", "")).upper()
        confidence = data.get("confidence", 0)
        conf_pct = int(confidence * 100)

        if ml_severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            return None

        # Apply override — bump up if keywords demand it
        forced = _force_severity(prompt)
        severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        if forced and severity_rank.get(forced, 0) > severity_rank.get(ml_severity, 0):
            severity = forced
            conf_pct = 0  # override confidence not shown
        else:
            severity = ml_severity

        reply = _build_response(prompt, severity, conf_pct)
        return reply, severity, conf_pct
    except Exception:
        return None


def _build_response(prompt: str, severity: str, conf_pct: int = 0) -> str:
    """Build a symptom-aware, human-sounding triage response.

    Rules:
    - No specific medicine names — direct to pharmacy for OTC options
    - No severity label in the text (frontend badge handles that)
    - Ends with a relevant follow-up question so the AI drives the conversation
    """
    p = prompt.lower()

    # -- Detect symptom category --
    is_head    = any(w in p for w in ["headache", "migraine", "head", "forehead", "temple", "skull"])
    is_chest   = any(w in p for w in ["chest", "heart", "palpitation", "breathing", "breath", "lung", "pulmonary"])
    is_fever   = any(w in p for w in ["fever", "temperature", "chills", "sweating", "hot", "shivering"])
    is_stomach = any(w in p for w in [
        "stomach", "nausea", "vomit", "diarrhea", "diarrhoea", "abdomen", "abdominal",
        "bloat", "cramp", "bowel", "gut", "digestion", "indigestion", "appendix",
        "pancreas", "gallbladder",
    ])
    is_throat  = any(w in p for w in ["throat", "swallow", "tonsil", "hoarse", "voice", "larynx", "pharynx"])
    is_cough   = any(w in p for w in ["cough", "wheeze", "phlegm", "mucus", "congestion", "respiratory", "bronchitis"])
    is_injury  = any(w in p for w in [
        "cut", "wound", "burn", "fracture", "broken", "break", "dislocated",
        "dislocation", "torn", "tear", "separated", "separation", "bleeding",
        "fall", "fell", "injury", "swollen", "sprain", "snapped", "toe", "finger",
        "wrist", "ankle", "knee", "shoulder", "elbow", "bone", "bruise", "bleed",
        "laceration", "gash", "stab", "puncture",
    ])
    is_mental  = any(w in p for w in [
        "anxiety", "panic", "stress", "depression", "suicide", "self-harm", "mental",
        "mood", "sad", "hopeless", "worthless", "ptsd", "trauma", "phobia",
    ])
    is_skin    = any(w in p for w in [
        "rash", "skin", "itch", "eczema", "psoriasis", "hives", "urticaria",
        "blister", "abscess", "boil", "cellulitis", "dermatitis",
    ])
    is_eye     = any(w in p for w in [
        "eye", "vision", "sight", "blind", "blurry", "floater", "flash", "glaucoma",
        "conjunctivitis", "red eye",
    ])
    is_ear     = any(w in p for w in ["ear", "hearing", "tinnitus", "deaf", "otitis", "earache"])
    is_uro     = any(w in p for w in [
        "urinary", "urine", "bladder", "kidney", "pee", "painful urination",
        "burning urination", "frequent urination", "uti",
    ])
    is_appt    = any(w in p for w in ["appointment", "book", "schedule", "doctor", "clinic", "hospital"])

    # -- Appointment request --
    if is_appt:
        return (
            "I can help you book an appointment.\n\n"
            "Click the **Schedule Appointment** button below to choose your preferred department, date, and time.\n\n"
            "Departments available: General Practice · Cardiology · Paediatrics · ENT · Orthopaedics · Mental Health · Gynaecology\n\n"
            "If this is an emergency, please call **10177** or **112** instead of waiting for an appointment.\n\n"
            "Before you book — is there a specific department you need, or would you like me to suggest one based on your symptoms?"
        )

    # -- Mental health --
    if is_mental:
        return (
            "I hear you, and I want you to know your feelings are valid.\n\n"
            "Please reach out to one of these free services right now:\n"
            "• **SADAG Helpline:** 0800 456 789 — available 24/7, free call\n"
            "• **Lifeline SA:** 0861 322 322\n"
            "• **SMS support:** SMS 31393\n\n"
            "You can also use the Schedule Appointment button below to book a session with a mental health professional at your nearest clinic.\n\n"
            "You are not alone. Can you tell me a little more about what you're going through right now?\n\n"
            "⚠️ VitalAI does not replace professional mental health care."
        )

    # -- CRITICAL --
    if severity == "CRITICAL":
        if is_chest:
            detail = "Chest symptoms at this level can indicate a heart attack, pulmonary embolism, or acute respiratory failure — all of which require immediate emergency care."
        elif is_head:
            detail = "Sudden or severe head symptoms like these can be a sign of a stroke, brain bleed, or a dangerous spike in blood pressure."
        elif is_injury:
            detail = "This injury may involve severe blood loss, internal damage, or trauma that cannot be safely managed at home."
        else:
            detail = "Your symptoms suggest a potentially life-threatening condition that needs immediate professional evaluation."

        return (
            f"{detail}\n\n"
            "**Do this right now:**\n"
            "• Call **10177** (ambulance) or **112** immediately — do not wait\n"
            "• Do NOT drive yourself\n"
            "• If you are alone, unlock your front door so paramedics can reach you\n"
            "• Sit or lie down and stay as calm as possible\n"
            "• Do not eat or drink anything\n\n"
            "Is there someone with you right now who can help you call for assistance?\n\n"
            "⚠️ VitalAI is an AI-powered assistant. Call emergency services immediately — do not rely on this app in an emergency."
        )

    # -- HIGH --
    if severity == "HIGH":
        if is_injury:
            if any(w in p for w in ["broken", "fracture", "fractured", "dislocated", "dislocation", "torn", "separated", "snapped"]):
                advice = (
                    "A broken bone, dislocation, or torn tissue is a serious orthopaedic injury that needs professional treatment today — it cannot heal properly without medical assessment.\n\n"
                    "• Go to the nearest emergency room, trauma unit, or 24-hour clinic now\n"
                    "• **Do not try to straighten, pop back, or apply pressure to the injured area** — this can cause further damage\n"
                    "• Immobilise the area as best you can — use a makeshift splint if available (rolled magazine, stick)\n"
                    "• Apply ice wrapped in a cloth to reduce swelling — never ice directly on skin\n"
                    "• If there is an open wound or bone visible, cover it loosely with a clean cloth and go immediately"
                )
            elif any(w in p for w in ["burn", "burnt", "scalded"]):
                advice = (
                    "A serious burn requires hospital treatment.\n\n"
                    "• Run cool (not ice cold) water over the burn for at least 20 minutes\n"
                    "• Do not apply creams, butter, or toothpaste — this traps heat and causes infection\n"
                    "• Cover loosely with cling wrap or a clean non-fluffy cloth\n"
                    "• Go to the emergency room immediately — do not wait"
                )
            elif any(w in p for w in ["bleeding", "blood", "cut", "gash"]):
                advice = (
                    "Significant bleeding or a deep wound needs urgent medical attention.\n\n"
                    "• Apply firm, continuous pressure with a clean cloth — do not lift the cloth to check\n"
                    "• If blood soaks through, add more cloth on top and keep pressing\n"
                    "• Keep the injured area raised above the level of your heart if possible\n"
                    "• Go to an emergency room or trauma clinic now — you may need stitches or wound treatment"
                )
            else:
                advice = (
                    "This injury sounds serious and needs same-day professional assessment.\n\n"
                    "• Go to your nearest emergency room or urgent care clinic today\n"
                    "• Immobilise and protect the injured area during travel\n"
                    "• Do not eat or drink in case treatment or sedation is needed\n"
                    "• Bring a list of any chronic medication you take"
                )
        elif is_chest:
            advice = (
                "Chest symptoms at this level need same-day evaluation — do not ignore or wait.\n\n"
                "• Go to the nearest hospital emergency unit or 24-hour clinic today\n"
                "• Avoid any physical exertion until assessed by a doctor\n"
                "• If the pain spreads to your arm, neck, or jaw, or you feel faint — call **10177** immediately\n"
                "• Tell the doctor exactly where the pain is, when it started, and whether it comes and goes"
            )
        elif is_fever:
            advice = (
                "A high fever can become dangerous if not treated — especially in children, the elderly, or those with existing conditions.\n\n"
                "• Go to a clinic or hospital today\n"
                "• Keep taking fluids — water or oral rehydration solution\n"
                "• A pharmacist can advise on fever-reducing options available over the counter\n"
                "• Bring your temperature readings when you see the doctor"
            )
        elif is_head:
            advice = (
                "A severe or rapidly worsening headache — especially with nausea, vision changes, or a stiff neck — is a warning sign that needs urgent attention.\n\n"
                "• Visit a hospital or urgent care clinic today\n"
                "• Make a note of when the headache started, how quickly it came on, and its intensity (1–10)\n"
                "• Avoid bright lights and screens\n"
                "• Ask a pharmacist for over-the-counter relief while you arrange to be seen"
            )
        elif is_stomach:
            advice = (
                "Severe abdominal pain can indicate appendicitis, a bowel obstruction, or internal bleeding — do not wait.\n\n"
                "• Go to a hospital or urgent clinic today\n"
                "• Avoid eating or drinking until you've been assessed — you may need procedures that require an empty stomach\n"
                "• Note the exact location of the pain and when it started\n"
                "• Tell the doctor if you notice any blood in your stool or vomit"
            )
        else:
            advice = (
                "Your symptoms are serious enough to need attention today.\n\n"
                "• Visit your nearest clinic or hospital — do not leave it for tomorrow\n"
                "• Bring your ID, any chronic medication, and a note of how long you've had symptoms\n"
                "• Ask someone to go with you if possible\n"
                "• A pharmacist can advise on anything that helps manage discomfort in the meantime"
            )

        return (
            f"{advice}\n\n"
            "How long have you had these symptoms, and have they been getting worse or staying the same?\n\n"
            "⚠️ VitalAI is an AI-powered assistant. Always follow advice from a qualified healthcare professional."
        )

    # -- MEDIUM --
    if severity == "MEDIUM":
        if is_head:
            advice = (
                "A persistent or worsening headache that isn't improving on its own needs a doctor's attention within the next day or two.\n\n"
                "• Book an appointment with a doctor or clinic soon — use the Schedule Appointment button below\n"
                "• Keep track of when headaches happen, how long they last, and what you were doing\n"
                "• Reduce screen time and rest in a calm, darker room\n"
                "• A pharmacist can recommend something for relief over the counter — ask them what's suitable for your situation"
            )
        elif is_fever:
            advice = (
                "A moderate fever means your body is fighting something. Monitor it carefully over the next 24–48 hours.\n\n"
                "• Keep drinking fluids regularly throughout the day\n"
                "• A pharmacist can advise on over-the-counter fever relief that's appropriate for you\n"
                "• Book a clinic visit if the fever lasts more than 2 days, rises above 39°C, or is accompanied by a rash\n"
                "• Avoid close contact with elderly family members or young children while you're unwell"
            )
        elif is_throat or is_cough:
            advice = (
                "Persistent throat or cough symptoms at this level may be a respiratory infection that needs treatment.\n\n"
                "• See a doctor within the next 1–2 days — a pharmacist can also advise on what's available over the counter\n"
                "• Gargle with warm salt water a few times a day for throat discomfort\n"
                "• Stay away from work or school to avoid spreading the illness\n"
                "• Avoid smoking and cold air, which can irritate already-inflamed airways"
            )
        elif is_stomach:
            advice = (
                "Persistent stomach symptoms that don't resolve on their own should be checked by a doctor.\n\n"
                "• Stick to bland foods — plain toast, rice, boiled vegetables\n"
                "• Keep drinking fluids, especially if you've been vomiting or have diarrhoea\n"
                "• A pharmacist can suggest over-the-counter options for nausea or discomfort\n"
                "• Book a clinic visit if symptoms haven't improved in 48 hours"
            )
        elif is_injury:
            advice = (
                "Your injury should be properly assessed by a healthcare professional — some injuries look minor but need treatment to heal correctly.\n\n"
                "• Visit a clinic or GP within the next 24 hours\n"
                "• Keep the area clean and protected with a bandage or covering\n"
                "• Elevate the injured area to help reduce swelling\n"
                "• A pharmacist can advise on appropriate pain management and wound care products"
            )
        elif is_skin:
            advice = (
                "A skin condition that is spreading, infected, or not responding to home care needs medical attention.\n\n"
                "• Do not scratch or try to squeeze any infected areas\n"
                "• Keep the area clean and dry\n"
                "• Book an appointment with a doctor or clinic within 24–48 hours — some skin infections need antibiotics\n"
                "• A pharmacist can advise on interim options and whether it looks like something urgent"
            )
        elif is_eye:
            advice = (
                "Eye symptoms that persist or are affecting your vision need prompt assessment.\n\n"
                "• Avoid rubbing your eyes — this can worsen infection or injury\n"
                "• If there is discharge, gently wipe outward with a clean damp cloth\n"
                "• Book with a doctor or optometrist within 24 hours\n"
                "• Go to emergency immediately if vision becomes suddenly blurry, you see flashing lights, or there's significant pain"
            )
        elif is_ear:
            advice = (
                "Ear pain or hearing changes that aren't resolving on their own should be checked by a doctor.\n\n"
                "• Don't insert anything into the ear\n"
                "• Book with a doctor within 24–48 hours — ear infections can worsen quickly\n"
                "• A pharmacist can advise on pain management while you wait\n"
                "• Go to an emergency room if pain becomes severe, you develop a fever, or notice swelling behind the ear"
            )
        elif is_uro:
            advice = (
                "Urinary symptoms with fever or pain may indicate a kidney infection or a UTI that needs treatment.\n\n"
                "• Increase your fluid intake significantly\n"
                "• Book with a doctor within 24 hours — urinary infections often require a prescription\n"
                "• A pharmacist can test your urine with a dipstick and advise on next steps\n"
                "• Go to emergency if you have severe back/loin pain, high fever, or can't pass urine at all"
            )
        else:
            advice = (
                "Your symptoms are worth having checked — don't leave them unaddressed.\n\n"
                "• Book an appointment with a doctor within the next 1–2 days\n"
                "• Use the Schedule Appointment button below to book at your nearest clinic\n"
                "• Note when symptoms started and anything that makes them better or worse\n"
                "• A pharmacist can advise on over-the-counter options to manage discomfort in the meantime"
            )

        return (
            f"{advice}\n\n"
            "Have your symptoms been getting worse since they started, or staying about the same?\n\n"
            "⚠️ VitalAI is an AI-powered assistant. Always consult a qualified healthcare provider for diagnosis."
        )

    # -- LOW --
    if is_head:
        advice = (
            "A mild headache is usually not a cause for concern.\n\n"
            "• Drink a full glass of water — dehydration is one of the most common headache triggers\n"
            "• Step away from screens and rest in a quiet room for 20–30 minutes\n"
            "• A pharmacist can recommend a suitable over-the-counter pain reliever if needed\n"
            "• If headaches keep returning regularly, mention it to your doctor at your next visit"
        )
    elif is_fever:
        advice = (
            "A mild fever usually means your immune system is doing its job.\n\n"
            "• Keep drinking fluids — warm water, soup, or herbal tea\n"
            "• Rest and avoid strenuous activity for the rest of the day\n"
            "• A pharmacist can suggest a suitable fever reducer if you're feeling very uncomfortable\n"
            "• See a doctor if the fever rises above 38.5°C or lasts more than 3 days"
        )
    elif is_cough or is_throat:
        advice = (
            "Mild throat and cough symptoms are common and usually clear up on their own.\n\n"
            "• Gargle with warm salt water a few times a day\n"
            "• Sip warm fluids — honey and lemon in warm water can be soothing\n"
            "• A pharmacist can recommend a suitable throat lozenge or cough syrup\n"
            "• See a doctor if symptoms persist beyond 5–7 days or a fever develops"
        )
    elif is_stomach:
        advice = (
            "Mild stomach discomfort is usually short-lived and manageable at home.\n\n"
            "• Avoid rich, greasy, or spicy food for today\n"
            "• Sip peppermint or ginger tea — both can help with nausea\n"
            "• Stay upright for at least 30 minutes after eating\n"
            "• A pharmacist can advise on suitable over-the-counter options\n"
            "• See a doctor if symptoms don't improve, or if you notice blood in your stool"
        )
    elif is_injury:
        advice = (
            "Minor cuts, scrapes, and bruises can usually be managed at home.\n\n"
            "• Clean the area thoroughly with clean water\n"
            "• Cover with a clean plaster or bandage\n"
            "• A pharmacist can advise on antiseptic creams and wound care supplies\n"
            "• See a doctor if the area becomes increasingly red, warm, swollen, or starts to discharge"
        )
    elif is_skin:
        advice = (
            "Mild skin conditions like rashes, dry skin, or minor irritation can often be managed at home.\n\n"
            "• Avoid scratching — this can cause infection\n"
            "• Keep the area clean and moisturised\n"
            "• A pharmacist can recommend suitable creams or antihistamines for itch relief\n"
            "• See a doctor if the rash spreads rapidly, is accompanied by fever, or doesn't improve in 48 hours"
        )
    elif is_eye:
        advice = (
            "Mild eye discomfort or irritation is often caused by dryness, dust, or eye strain.\n\n"
            "• Rinse the eye gently with clean water if something is in it\n"
            "• Rest your eyes from screens regularly — the 20-20-20 rule (every 20 min, look 20 feet away for 20 seconds)\n"
            "• A pharmacist can recommend lubricating eye drops\n"
            "• See a doctor immediately if you have sudden vision loss, eye pain, or an eye injury"
        )
    elif is_ear:
        advice = (
            "Mild ear discomfort or blocked ears are common and often resolve on their own.\n\n"
            "• Avoid inserting anything into the ear canal — no cotton buds\n"
            "• Try swallowing, yawning, or chewing to help equalise pressure\n"
            "• A pharmacist can advise on eardrops for mild blockage or discomfort\n"
            "• See a doctor if pain is severe, you have hearing loss, or symptoms last more than 48 hours"
        )
    elif is_uro:
        advice = (
            "Mild urinary symptoms like slight frequency or mild discomfort can be early signs of a UTI or dehydration.\n\n"
            "• Drink at least 2 litres of water today\n"
            "• Avoid caffeine and alcohol which irritate the bladder\n"
            "• A pharmacist can advise on UTI testing strips and available over-the-counter options\n"
            "• See a doctor if you have fever, back pain, blood in urine, or symptoms don't improve in 24 hours"
        )
    else:
        advice = (
            "Based on what you've described, this doesn't seem urgent right now.\n\n"
            "• Monitor how you feel over the next 24–48 hours\n"
            "• If any new symptoms appear or existing ones worsen, describe them to me again\n"
            "• A pharmacist is a good first stop if you need something to manage discomfort\n"
            "• If you're still unsure, booking a routine check-up with a GP is always a sensible step"
        )

    return (
        f"{advice}\n\n"
        "Is there anything else you'd like to tell me about how you're feeling, or have you noticed any other symptoms?\n\n"
        "⚠️ VitalAI is an AI-powered assistant. When in doubt, always consult a healthcare professional."
    )


def _keyword_triage(prompt: str) -> tuple[str, str]:
    """Last-resort fallback — returns (severity, reply)."""
    forced = _force_severity(prompt)
    if forced:
        return forced, _build_response(prompt, forced)
    p = prompt.lower()
    if any(w in p for w in ["fever", "headache", "pain", "sore throat", "cough", "nausea", "dizzy", "fatigue"]):
        return "MEDIUM", _build_response(prompt, "MEDIUM")
    return "LOW", _build_response(prompt, "LOW")