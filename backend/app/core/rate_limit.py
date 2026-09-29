"""
Per-source rate limiter using asyncio semaphores and token-bucket logic.

Features:
- source-specific concurrency limits
- 429 back-off with Retry-After support
- configurable requests-per-minute
- exponential back-off on repeated failures
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class _SourceBucket:
    """Token bucket for a single source."""

    requests_per_minute: int
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)
    semaphore: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(5))
    error_count: int = 0
    backoff_until: float = 0.0

    def refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.requests_per_minute,
            self.tokens + elapsed * (self.requests_per_minute / 60.0),
        )
        self.last_refill = now

    async def acquire(self) -> None:
        """Wait until a token is available and concurrency slot is free."""
        # Back-off period after repeated errors
        now = time.monotonic()
        if now < self.backoff_until:
            wait = self.backoff_until - now
            logger.info("rate_limit_backoff", wait_seconds=round(wait, 1))
            await asyncio.sleep(wait)

        async with self.semaphore:
            while True:
                self.refill()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                await asyncio.sleep(0.5)

    def report_success(self) -> None:
        self.error_count = 0

    def report_429(self, retry_after: float | None = None) -> None:
        """Back off after receiving HTTP 429."""
        self.error_count += 1
        delay = retry_after or min(2 ** self.error_count, 300)
        self.backoff_until = time.monotonic() + delay
        logger.warning(
            "rate_limit_429",
            error_count=self.error_count,
            backoff_seconds=delay,
        )

    def report_error(self) -> None:
        """Exponential back-off for general errors."""
        self.error_count += 1
        delay = min(2 ** self.error_count, 120)
        self.backoff_until = time.monotonic() + delay


class RateLimiter:
    """Manages per-source rate limiting."""

    def __init__(self) -> None:
        self._buckets: dict[str, _SourceBucket] = {}

    def _get_bucket(
        self,
        source_key: str,
        requests_per_minute: int = 30,
        concurrency: int = 5,
    ) -> _SourceBucket:
        if source_key not in self._buckets:
            self._buckets[source_key] = _SourceBucket(
                requests_per_minute=requests_per_minute,
                tokens=float(requests_per_minute),
                semaphore=asyncio.Semaphore(concurrency),
            )
        return self._buckets[source_key]

    async def acquire(
        self,
        source_key: str,
        requests_per_minute: int = 30,
        concurrency: int = 5,
    ) -> None:
        bucket = self._get_bucket(source_key, requests_per_minute, concurrency)
        await bucket.acquire()

    def report_success(self, source_key: str) -> None:
        if source_key in self._buckets:
            self._buckets[source_key].report_success()

    def report_429(self, source_key: str, retry_after: float | None = None) -> None:
        if source_key in self._buckets:
            self._buckets[source_key].report_429(retry_after)

    def report_error(self, source_key: str) -> None:
        if source_key in self._buckets:
            self._buckets[source_key].report_error()


# Global singleton
rate_limiter = RateLimiter()
