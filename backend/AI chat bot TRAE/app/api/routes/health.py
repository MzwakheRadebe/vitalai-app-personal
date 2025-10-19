"""Health route

Provides a simple service health check and (optionally) reports connectivity to
the configured AI backend. This helps diagnose why `/api/chat` might be
returning stub responses.
"""

from fastapi import APIRouter
import httpx
from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health():
    settings = get_settings()

    # Default AI status when no service is configured
    ai_status = {
        "configured": bool(settings.ai_service_url),
        "status": "not_checked",
        "url": settings.ai_service_url,
    }

    # Quick connectivity probe to the AI backend (non-fatal)
    try:
        base = settings.ai_service_url.rstrip("/")
        use_openai = base.endswith("/v1") or "/v1" in base or base.endswith("/v1/chat/completions")
        if use_openai:
            models_url = base if base.endswith("/v1") else base.split("/v1")[0] + "/v1/models"
            target = models_url
        else:
            # For simple backends, try hitting the root or `/health` if available
            target = base

        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(target)
            ai_status["status"] = "ok" if r.status_code < 500 else "unreachable"
    except Exception:
        ai_status["status"] = "unreachable"

    return {"status": "ok", "env": settings.env, "ai_backend": ai_status}