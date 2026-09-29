"""Unit tests for the rate limiter."""

import asyncio
import time

import pytest

from app.core.rate_limit import RateLimiter, _SourceBucket


class TestSourceBucket:
    """Tests for the internal _SourceBucket."""

    def test_refill_adds_tokens(self):
        bucket = _SourceBucket(requests_per_minute=60, tokens=0.0)
        bucket.last_refill = time.monotonic() - 1.0  # 1 second ago
        bucket.refill()
        # Should have gained ~1 token (60 rpm / 60 sec = 1 token/sec)
        assert bucket.tokens >= 0.9

    def test_refill_caps_at_max(self):
        bucket = _SourceBucket(requests_per_minute=10, tokens=10.0)
        bucket.last_refill = time.monotonic() - 100.0
        bucket.refill()
        assert bucket.tokens == 10.0  # Capped at requests_per_minute

    def test_report_success_resets_errors(self):
        bucket = _SourceBucket(requests_per_minute=60, error_count=5)
        bucket.report_success()
        assert bucket.error_count == 0

    def test_report_429_increments_errors(self):
        bucket = _SourceBucket(requests_per_minute=60)
        bucket.report_429()
        assert bucket.error_count == 1
        assert bucket.backoff_until > time.monotonic()

    def test_report_429_with_retry_after(self):
        bucket = _SourceBucket(requests_per_minute=60)
        bucket.report_429(retry_after=10.0)
        assert bucket.error_count == 1
        assert bucket.backoff_until >= time.monotonic() + 9

    def test_report_error_exponential_backoff(self):
        bucket = _SourceBucket(requests_per_minute=60)
        bucket.report_error()
        first_delay = bucket.backoff_until
        bucket.report_error()
        second_delay = bucket.backoff_until
        assert second_delay > first_delay

    def test_backoff_capped_at_120(self):
        bucket = _SourceBucket(requests_per_minute=60, error_count=100)
        bucket.report_error()
        assert bucket.backoff_until <= time.monotonic() + 121


class TestRateLimiter:
    """Tests for the RateLimiter manager."""

    def test_creates_bucket_on_first_use(self):
        limiter = RateLimiter()
        # Access internal bucket via _get_bucket
        bucket = limiter._get_bucket("test_source", 30, 5)
        assert bucket.requests_per_minute == 30

    def test_reuses_existing_bucket(self):
        limiter = RateLimiter()
        b1 = limiter._get_bucket("same_key")
        b2 = limiter._get_bucket("same_key")
        assert b1 is b2

    def test_separate_buckets_per_source(self):
        limiter = RateLimiter()
        b1 = limiter._get_bucket("source_a")
        b2 = limiter._get_bucket("source_b")
        assert b1 is not b2

    def test_report_success_on_missing_key_noop(self):
        limiter = RateLimiter()
        # Should not raise
        limiter.report_success("nonexistent")

    def test_report_429_on_missing_key_noop(self):
        limiter = RateLimiter()
        limiter.report_429("nonexistent")

    def test_report_error_on_missing_key_noop(self):
        limiter = RateLimiter()
        limiter.report_error("nonexistent")

    @pytest.mark.asyncio
    async def test_acquire_succeeds_with_tokens(self):
        limiter = RateLimiter()
        # High rate limit means tokens available immediately
        await asyncio.wait_for(
            limiter.acquire("fast_source", requests_per_minute=600),
            timeout=2.0,
        )
