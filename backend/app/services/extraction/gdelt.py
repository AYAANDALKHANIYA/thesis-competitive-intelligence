"""
GDELT extractor — uses GDELT DOC 2.0 API for targeted news discovery.

Queries are company/topic-specific to minimise unnecessary requests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from app.core.logging import get_logger
from app.services.extraction.base import BaseExtractor, ExtractionResult, normalise_url

logger = get_logger(__name__)

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


class GDELTExtractor(BaseExtractor):
    """Extracts news articles via the GDELT DOC 2.0 API."""

    source_type = "gdelt"

    async def extract(
        self,
        company_name: str,
        company_domain: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExtractionResult]:
        config = config or {}
        query = config.get("query", company_name)
        max_records = config.get("max_records", 50)
        timespan = config.get("timespan", "7d")  # Last 7 days
        source_key = "gdelt"
        rate_limit = config.get("rate_limit", self.settings.GDELT_RATE_LIMIT)

        params = {
            "query": query,
            "mode": "ArtList",
            "maxrecords": str(max_records),
            "timespan": timespan,
            "format": "json",
            "sort": "DateDesc",
        }

        url = f"{GDELT_DOC_API}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}"

        response = await self.fetch_url(url, source_key, rate_limit)
        if not response or response.status_code != 200:
            logger.warning("gdelt_fetch_failed", company=company_name)
            raise Exception("GDELT fetch failed")

        try:
            data = response.json()
        except Exception:
            logger.warning("gdelt_json_parse_error", company=company_name)
            raise Exception("GDELT json parse error")

        articles = data.get("articles", [])
        results: List[ExtractionResult] = []

        for article in articles:
            article_url = article.get("url", "")
            if not article_url:
                continue

            title = article.get("title", "")
            # GDELT provides article snippets, not full text
            content = article.get("seendate", "")
            # Build content from available fields
            body_parts = []
            if title:
                body_parts.append(title)
            if article.get("sourcecountry"):
                body_parts.append(f"Source country: {article['sourcecountry']}")
            if article.get("domain"):
                body_parts.append(f"Source: {article['domain']}")
            if article.get("language"):
                body_parts.append(f"Language: {article['language']}")

            content = "\n".join(body_parts) if body_parts else title

            published_at = None
            seen_date = article.get("seendate", "")
            if seen_date:
                try:
                    published_at = datetime.strptime(
                        seen_date[:14], "%Y%m%dT%H%M%S"
                    ).replace(tzinfo=timezone.utc)
                except (ValueError, IndexError):
                    pass

            results.append(
                ExtractionResult(
                    url=normalise_url(article_url),
                    title=title,
                    content=content,
                    published_at=published_at,
                    language=article.get("language", "English"),
                    document_type="news_article",
                    source_type="gdelt",
                    metadata={
                        "gdelt_domain": article.get("domain", ""),
                        "gdelt_country": article.get("sourcecountry", ""),
                        "gdelt_tone": article.get("tone", 0),
                        "gdelt_socialimage": article.get("socialimage", ""),
                    },
                )
            )

        logger.info(
            "gdelt_extraction_complete",
            company=company_name,
            articles=len(results),
        )
        return results
