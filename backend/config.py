from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Redis
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # TursoDB (Phase 3 — optional in Phase 1)
    turso_database_url: str = ""
    turso_auth_token: str = ""

    # Gemini (Phase 2 — optional in Phase 1)
    gemini_api_key: str = ""

    # App
    cors_origin: str = "http://localhost:5173"
    port: int = 8000
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
