"""Application configuration

Centralized settings loaded from environment variables via pydantic-settings.
We keep types simple (e.g., `allowed_origins` as a string) to reduce friction
in local development where values may be comma-separated or JSON.
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # General app info and environment
    app_name: str = Field(default="VitalAI")
    env: str = Field(default="development")
    port: int = Field(default=8000)
    tz: str = Field(default="Africa/Johannesburg")

    # Data backends (optional in early scaffolding)
    mysql_url: str = Field(default="mysql+pymysql://user:password@localhost:3306/hospital_db")
    mongo_url: str = Field(default="mongodb://localhost:27017/hospital_logs")
    sqlite_path: str = Field(default="./local_offline.db")

    # Security and CORS
    jwt_secret: str = Field(default="change_me")
    encryption_key: str = Field(default="change_me_base64_32bytes")
    allowed_origins: str = Field(default="")  # e.g., "*" or comma-separated list

    # AI service integration (managed defaults for beginner teams)
    # If you prefer local backends, override these in `.env`.
    ai_service_url: str = Field(default="https://api.openai.com/v1")
    ai_model: str = Field(default="gpt-4o-mini")  # used for OpenAI-style endpoints
    ai_api_key: str = Field(default="")  # optional; adds Authorization header if set

    class Config:
        # `.env` file support for local development
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Avoids re-reading environment on every request and provides fast access
    to configuration throughout the app.
    """
    return Settings()