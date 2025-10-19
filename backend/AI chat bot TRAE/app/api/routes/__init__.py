from fastapi import APIRouter, FastAPI

from .health import router as health_router
from .faq import router as faq_router
from .chat import router as chat_router
from .auth import router as auth_router
from .appointments import router as appointments_router


def register_routes(app: FastAPI) -> None:
    api = APIRouter(prefix="/api")
    api.include_router(health_router, tags=["health"])
    api.include_router(faq_router, tags=["faq"])
    api.include_router(chat_router, tags=["chat"])
    api.include_router(auth_router, tags=["auth"])
    api.include_router(appointments_router, tags=["appointments"])
    app.include_router(api)