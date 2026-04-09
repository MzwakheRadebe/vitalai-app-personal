from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from .config import get_settings
from .db import init_db  # initialize SQLite tables on app startup


# Load app settings from `.env` via pydantic-settings. Cached by get_settings().
settings = get_settings()

# Instantiate the FastAPI app with a friendly title for Swagger UI.
app = FastAPI(title=settings.app_name)

# Basic logging configuration for local development and team visibility.
# Logs show time, level, logger name, and message (e.g., chat requests).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# CORS configuration
# Parse ALLOWED_ORIGINS from .env (supports *, comma-separated, or JSON list).
# We keep parsing here (instead of pydantic) to avoid strict type errors
# when ALLOWED_ORIGINS is missing or formatted loosely in local dev.
raw_origins = settings.allowed_origins
if isinstance(raw_origins, str):
    s = raw_origins.strip()
    if not s:
        allowed_origins = ["*"] if settings.env == "development" else []
    elif s == "*":
        allowed_origins = ["*"]
    elif s.startswith("["):
        import json
        try:
            parsed = json.loads(s)
            allowed_origins = parsed if isinstance(parsed, list) else []
        except Exception:
            allowed_origins = [item.strip() for item in s.split(",") if item.strip()]
    else:
        allowed_origins = [item.strip() for item in s.split(",") if item.strip()]
else:
    allowed_origins = ["*"] if settings.env == "development" else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ensure DB tables exist at startup (simple bootstrap for local dev)
@app.on_event("startup")
async def on_startup():
    """Create required SQLite tables if they don't exist yet.

    Keeps onboarding easy and avoids separate migration steps initially.
    """
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.env}


@app.get("/")
async def home():
    return {
        "name": settings.app_name,
        "env": settings.env,
        "status": "running",
        "docs_url": "/docs",
        "api_base": "/api",
    }


# Route registration
# All API routes live under `app.api.routes`. We include them on `/api` and
# keep a try/except so local development doesn’t crash if one module has a
# transient import error; the app still serves `/health` for quick checks.
try:
    from .api.routes import register_routes  # type: ignore
    register_routes(app)
except Exception:
    # If routes aren't ready yet, app still runs with health endpoint.
    pass


if __name__ == "__main__":
    # Dev entrypoint. Prefer `python -m uvicorn app.main:app --reload` in docs,
    # but keeping this for convenience when running the module directly.
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)