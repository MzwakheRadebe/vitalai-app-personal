"""Application configuration

Centralized settings loaded from environment variables via pydantic-settings.
Copy .env.example to .env and fill in your values for local development.
In production, set these as environment variables (e.g., on Render).
"""

import secrets
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # General app info and environment
    app_name: str = Field(default="VitalAI")
    env: str = Field(default="development")
    port: int = Field(default=8000)
    tz: str = Field(default="Africa/Johannesburg")

    # Database — Supabase PostgreSQL (primary)
    # Set DATABASE_URL in your .env or production environment variables
    database_url: str = Field(default="")
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")

    # SQLite fallback (local development only)
    sqlite_path: str = Field(default="./local_offline.db")

    # Security
    # IMPORTANT: Always set a strong random value in production.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    jwt_secret: str = Field(default="")
    encryption_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60)

    # CORS — set to your frontend URL in production (e.g., https://your-app.vercel.app)
    allowed_origins: str = Field(default="http://localhost:3000")

    # AI service integration
    ai_service_url: str = Field(default="https://api.openai.com/v1")
    ai_model: str = Field(default="gpt-4o-mini")
    ai_api_key: str = Field(default="")

    def get_effective_jwt_secret(self) -> str:
        """Return JWT secret, generating a temporary one for local dev if not set."""
        if self.jwt_secret:
            return self.jwt_secret
        if self.env == "development":
            # Safe for local dev — not suitable for production
            return secrets.token_hex(32)
        raise ValueError(
            "JWT_SECRET environment variable must be set in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
