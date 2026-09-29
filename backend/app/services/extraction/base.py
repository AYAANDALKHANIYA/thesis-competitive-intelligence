"""
Base extractor — abstract interface for all source adapters.

Every extractor returns a list of ExtractionResult objects rather than
directly coupling to database models.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.rate_limit import rate_limiter

logger = get_logger(__name__)


@dataclass
class ExtractionResult:
    """Normalised extraction result from any source adapter."""

    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_type: str = ""


def normalise_url(url: str) -> str:
    """Canonical URL normalisation: lowercase scheme/host, strip fragments."""
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/") or "/",
        parsed.params,
        parsed.query,
        "",  # strip fragment
    ))


def content_hash(text: str) -> str:
    """SHA-256 hash of normalised content."""
    normalised = " ".join(text.split())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


class BaseExtractor(ABC):
    """Abstract base for all source adapters."""

    source_type: str = ""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.REQUEST_TIMEOUT),
                headers={"User-Agent": self.settings.USER_AGENT},
                follow_redirects=True,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def extract(
        self,
        company_name: str,
        company_domain: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExtractionResult]:
        """Extract documents from the source."""
        ...

    async def fetch_url(
        self,
        url: str,
        source_key: str,
        rate_limit: int = 30,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> Optional[httpx.Response]:
        """Fetch a URL with rate limiting, conditional headers, and retry."""
        await rate_limiter.acquire(source_key, requests_per_minute=rate_limit)

        headers: Dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        client = await self._get_client()
        try:
            response = await self._do_fetch(client, url, headers)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else None
                rate_limiter.report_429(source_key, delay)
                logger.warning("http_429", url=url, retry_after=retry_after)
                return None
            if response.status_code == 304:
                logger.debug("http_304_not_modified", url=url)
                rate_limiter.report_success(source_key)
                return response
            if response.status_code == 403:
                logger.warning("http_403_forbidden", url=url)
                rate_limiter.report_error(source_key)
                raise RuntimeError(f"Access Denied (HTTP 403): The target server blocked the request, likely due to anti-bot protection (e.g. Cloudflare).")
            if response.status_code >= 400:
                logger.warning("http_error", url=url, status=response.status_code)
                rate_limiter.report_error(source_key)
                return None
            rate_limiter.report_success(source_key)
            return response
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning("http_fetch_error", url=url, error=str(exc))
            rate_limiter.report_error(source_key)
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def _do_fetch(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Dict[str, str],
    ) -> httpx.Response:
        return await client.get(url, headers=headers)
