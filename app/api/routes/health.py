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

    # Quick database connectivity check
    db_status = {"status": "not_checked", "error": None}
    try:
        from app.db_adapter import get_db
        async with get_db() as db:
            await db.fetchone("SELECT 1", ())
            db_status["status"] = "ok"
    except Exception as e:
        db_status["status"] = "error"
        db_status["error"] = str(e)[:300]

    # Scan Supabase pooler regions for the correct one (diagnostic)
    if db_status["status"] == "error" and settings.supabase_url:
        import asyncio
        from functools import partial
        ref = settings.supabase_url.replace("https://", "").split(".")[0]
        import urllib.parse
        parsed = urllib.parse.urlparse(settings.database_url)
        pw = urllib.parse.unquote(parsed.password or "")

        regions = [
            "aws-0-us-east-1", "aws-0-us-east-2", "aws-0-us-west-1", "aws-0-us-west-2",
            "aws-0-eu-west-1", "aws-0-eu-west-2", "aws-0-eu-central-1",
            "aws-0-ap-southeast-1", "aws-0-ap-northeast-1", "aws-0-sa-east-1",
        ]
        pooler_results = {}
        def _try_pooler(region):
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=f"{region}.pooler.supabase.com", port=6543,
                    user=f"postgres.{ref}", password=pw,
                    dbname="postgres", sslmode="require", connect_timeout=5,
                )
                conn.close()
                return "ok"
            except Exception as ex:
                return str(ex).strip()  # full error, no truncation

        loop = asyncio.get_event_loop()
        tasks = {r: loop.run_in_executor(None, partial(_try_pooler, r)) for r in regions}
        for region, task in tasks.items():
            pooler_results[region] = await task

        db_status["pooler_scan"] = pooler_results

    return {"status": "ok", "env": settings.env, "ai_backend": ai_status, "db": db_status}