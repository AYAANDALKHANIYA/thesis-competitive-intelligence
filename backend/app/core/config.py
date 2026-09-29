"""
Application configuration using pydantic-settings.

All configuration is read from environment variables. Defaults are
provided for development; production values come from Railway env vars.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ──────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "Competitive Intelligence Platform"
    APP_VERSION: str = "1.0.0"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/competitive_intel"

    # ── Security ─────────────────────────────────────────────────────────
    API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── External APIs ────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    
    PAGESPEED_API_KEY: str = ""

    # ── HTTP ─────────────────────────────────────────────────────────────
    USER_AGENT: str = "CompetitiveIntelPlatform/1.0 (Academic Research)"
    SEC_USER_AGENT: str = "CompetitiveIntelPlatform research@example.com"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    # ── Rate limits ──────────────────────────────────────────────────────
    GDELT_RATE_LIMIT: int = 60
    DEFAULT_RATE_LIMIT: int = 30
    DEFAULT_CRAWL_DELAY: float = 2.0

    # ── NLP ──────────────────────────────────────────────────────────────
    NLP_BATCH_SIZE: int = 32
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"

    # ── Topic modelling ──────────────────────────────────────────────────
    TOPIC_RETRAIN_THRESHOLD: int = 100
    TOPIC_MIN_DOCUMENTS: int = 20

    # ── Prediction ───────────────────────────────────────────────────────
    PREDICTION_MIN_SAMPLES: int = 30
    PREDICTION_HORIZON_DAYS: int = 30

    # ── Ingestion intervals (seconds) ────────────────────────────────────
    RSS_INTERVAL: int = 3600
    GDELT_INTERVAL: int = 86400
    WEBSITE_INTERVAL: int = 86400
    SEC_INTERVAL: int = 604800

    # ── LLM ──────────────────────────────────────────────────────────────
    LLM_CACHE_HOURS: int = 24

    # ── Intelligence weights (configurable) ──────────────────────────────
    MAI_WEIGHT_NEWS_VOLUME: float = 0.25
    MAI_WEIGHT_SENTIMENT: float = 0.20
    MAI_WEIGHT_TOPIC_MOMENTUM: float = 0.20
    MAI_WEIGHT_COMPETITOR_ACTIVITY: float = 0.20
    MAI_WEIGHT_CONTENT_ACTIVITY: float = 0.15

    # ── Emerging signals ─────────────────────────────────────────────────
    SIGNAL_MIN_MENTIONS: int = 5
    SIGNAL_GROWTH_THRESHOLD: float = 1.5
    SIGNAL_LOOKBACK_DAYS: int = 30

    # ── Computed ─────────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def database_url_sync(self) -> str:
        """Synchronous URL variant for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalise_database_url(cls, v: str) -> str:
        """Railway provides postgres:// but asyncpg needs postgresql+asyncpg://."""
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
