"""
Centralized app configuration.

All settings are read from environment variables (with a `.env` file as a
convenience for local dev). Nothing here should be hardcoded elsewhere in
the app -- import `settings` instead.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://scholarlink:scholarlink@localhost:5432/scholarlink"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-real-environments"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # File storage (used starting Phase 2)
    UPLOAD_DIR: str = "./uploads"

    # Groq
    GROQ_API_KEY: str = ""

    # App
    ENVIRONMENT: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
