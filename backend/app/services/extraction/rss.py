"""
RSS/Atom feed extractor.

Low-cost source — preferred when available.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

import feedparser

from app.core.logging import get_logger
from app.services.extraction.base import BaseExtractor, ExtractionResult, normalise_url

logger = get_logger(__name__)


class RSSExtractor(BaseExtractor):
    """Extracts entries from RSS/Atom feeds."""

    source_type = "rss"

    async def extract(
        self,
        company_name: str,
        company_domain: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExtractionResult]:
        config = config or {}
        feed_urls = config.get("feed_urls", [])

        if not feed_urls and company_domain:
            # Auto-discover common feed paths
            feed_urls = [
                f"https://{company_domain}/feed",
                f"https://{company_domain}/rss",
                f"https://{company_domain}/blog/feed",
                f"https://{company_domain}/blog/rss.xml",
                f"https://{company_domain}/feed.xml",
                f"https://{company_domain}/rss.xml",
                f"https://{company_domain}/atom.xml",
            ]

        source_key = f"rss:{company_domain or company_name}"
        rate_limit = config.get("rate_limit", 60)
        max_entries = config.get("max_entries", 50)

        results: List[ExtractionResult] = []
        for feed_url in feed_urls:
            entries = await self._parse_feed(feed_url, source_key, rate_limit, max_entries)
            results.extend(entries)
            if results:
                break  # Stop at first successful feed

        logger.info(
            "rss_extraction_complete",
            company=company_name,
            entries=len(results),
        )
        return results

    async def _parse_feed(
        self, feed_url: str, source_key: str, rate_limit: int, max_entries: int
    ) -> List[ExtractionResult]:
        response = await self.fetch_url(feed_url, source_key, rate_limit)
        if not response or response.status_code != 200:
            return []

        feed = feedparser.parse(response.text)
        if not feed.entries:
            return []

        results: List[ExtractionResult] = []
        for entry in feed.entries[:max_entries]:
            url = entry.get("link", "")
            if not url:
                continue

            title = entry.get("title", "")
            content = ""
            if entry.get("content"):
                content = entry.content[0].get("value", "")
            elif entry.get("summary"):
                content = entry.summary

            # Strip HTML from content
            from bs4 import BeautifulSoup
            if "<" in content:
                soup = BeautifulSoup(content, "lxml")
                content = soup.get_text(separator="\n", strip=True)

            published_at = None
            if entry.get("published_parsed"):
                try:
                    from time import mktime
                    published_at = datetime.fromtimestamp(
                        mktime(entry.published_parsed), tz=timezone.utc
                    )
                except (TypeError, ValueError, OverflowError):
                    pass

            if not content or len(content.split()) < 10:
                continue

            results.append(
                ExtractionResult(
                    url=normalise_url(url),
                    title=title,
                    content=content,
                    author=entry.get("author"),
                    published_at=published_at,
                    document_type="rss_entry",
                    source_type="rss",
                    metadata={
                        "feed_url": feed_url,
                        "feed_title": feed.feed.get("title", ""),
                    },
                )
            )

        return results
