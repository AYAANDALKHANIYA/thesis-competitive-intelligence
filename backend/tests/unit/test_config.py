"""Unit tests for application configuration."""

import os
import pytest


class TestSettings:
    """Tests for the Settings class (not the cached singleton)."""

    def _make_settings(self, **overrides):
        """Create a fresh Settings instance with overrides applied via env."""
        env = {
            "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
            "OPENAI_API_KEY": "test-key",
            "GROQ_API_KEY": "test-groq-key",
            "ENVIRONMENT": "testing",
            **{k.upper(): str(v) for k, v in overrides.items()},
        }
        for k, v in env.items():
            os.environ[k] = v

        # Import inside to pick up fresh env
        from app.core.config import Settings
        return Settings()

    # ── DATABASE_URL normalisation ──────────────────────────────────────

    def test_normalise_postgres_url(self):
        s = self._make_settings(DATABASE_URL="postgres://u:p@host/db")
        assert s.DATABASE_URL.startswith("postgresql+asyncpg://")

    def test_normalise_postgresql_url(self):
        s = self._make_settings(DATABASE_URL="postgresql://u:p@host/db")
        assert "+asyncpg" in s.DATABASE_URL

    def test_already_correct_url_unchanged(self):
        url = "postgresql+asyncpg://u:p@host/db"
        s = self._make_settings(DATABASE_URL=url)
        assert s.DATABASE_URL == url

    # ── Computed properties ─────────────────────────────────────────────

    def test_cors_origins_list(self):
        s = self._make_settings(CORS_ORIGINS="http://a.com, http://b.com")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_cors_origins_list_empty(self):
        s = self._make_settings(CORS_ORIGINS="")
        assert s.cors_origins_list == []

    def test_is_production_true(self):
        s = self._make_settings(ENVIRONMENT="production")
        assert s.is_production is True

    def test_is_production_false(self):
        s = self._make_settings(ENVIRONMENT="development")
        assert s.is_production is False

    def test_database_url_sync(self):
        s = self._make_settings(DATABASE_URL="postgresql+asyncpg://u:p@host/db")
        assert "+asyncpg" not in s.database_url_sync
        assert s.database_url_sync == "postgresql://u:p@host/db"

    # ── Defaults ────────────────────────────────────────────────────────

    def test_default_log_level(self):
        s = self._make_settings()
        assert s.LOG_LEVEL in ("INFO", "DEBUG", "WARNING")

    def test_default_nlp_batch_size(self):
        s = self._make_settings()
        assert s.NLP_BATCH_SIZE == 32

    def test_signal_defaults(self):
        s = self._make_settings()
        assert s.SIGNAL_MIN_MENTIONS == 5
        assert s.SIGNAL_GROWTH_THRESHOLD == 1.5
        assert s.SIGNAL_LOOKBACK_DAYS == 30

    def test_mai_weights_sum_to_one(self):
        s = self._make_settings()
        total = (
            s.MAI_WEIGHT_NEWS_VOLUME
            + s.MAI_WEIGHT_SENTIMENT
            + s.MAI_WEIGHT_TOPIC_MOMENTUM
            + s.MAI_WEIGHT_COMPETITOR_ACTIVITY
            + s.MAI_WEIGHT_CONTENT_ACTIVITY
        )
        assert abs(total - 1.0) < 0.01
