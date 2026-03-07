from pydantic_settings import BaseSettings
from functools import lru_cache


# Default model chain — tried left-to-right on any failure / rate-limit.
# Override via GEMINI_MODEL_CHAIN in .env — no code change needed.
#
# Exact API strings accepted by google.generativeai (June 2025):
#   "gemini-2.5-flash-preview-05-20" is the API name Google uses for what
#   their marketing calls "Gemini 2.5 Flash Preview" / "gemini-3-flash-preview".
#   "gemma-3-27b-it" / "gemma-3-12b-it" are the instruction-tuned Gemma 3 variants.
_DEFAULT_MODEL_CHAIN = (
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemma-3-27b-it",
    "gemma-3-12b-it"
)


class Settings(BaseSettings):
    # ── Redis ─────────────────────────────────────────────────────────────
    upstash_redis_rest_url:   str = ""
    upstash_redis_rest_token: str = ""

    # ── TursoDB (Phase 3) ─────────────────────────────────────────────────
    turso_database_url: str = ""
    turso_auth_token:   str = ""

    # ── Gemini ────────────────────────────────────────────────────────────
    gemini_api_key: str = ""

    # Comma-separated model names tried in order on any error / rate-limit.
    # Each name must be the exact string the Gemini API accepts.
    # Edit in .env and restart — no code changes ever needed.
    #
    # Example .env override (use your own priority order):
    #   GEMINI_MODEL_CHAIN=gemini-2.5-flash-preview-05-20,gemini-2.0-flash,gemma-3-12b-it
    gemini_model_chain: str = _DEFAULT_MODEL_CHAIN

    # Seconds before timing out one model and moving to the next.
    gemini_model_timeout: int = 20

    # How many times to retry the SAME model on a 429 before moving on.
    # Backoff: GEMINI_RATE_LIMIT_BACKOFF * 2^attempt  (attempt 0 → 1.5s, 1 → 3s)
    gemini_rate_limit_retries: int = 2
    gemini_rate_limit_backoff: float = 1.5

    # ── App ───────────────────────────────────────────────────────────────
    cors_origin: str = "http://localhost:5173"
    port:        int = 8000
    env:         str = "development"

    @property
    def model_chain(self) -> list[str]:
        """
        Parses GEMINI_MODEL_CHAIN into an ordered, deduplicated list.
        Called fresh on each access so a restart picks up .env changes.
        """
        seen: set[str] = set()
        result: list[str] = []
        for raw in self.gemini_model_chain.split(","):
            name = raw.strip()
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        extra             = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
