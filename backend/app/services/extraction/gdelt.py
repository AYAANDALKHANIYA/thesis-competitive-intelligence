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
        
        # If GDELT is rate-limited (common on Railway IPs), we fallback to DuckDuckGo News
        if not response or response.status_code != 200:
            logger.warning("gdelt_fetch_failed_using_fallback", company=company_name)
            return await self._fallback_ddg(query, max_records)

        try:
            data = response.json()
        except Exception:
            logger.warning("gdelt_json_parse_error_using_fallback", company=company_name)
            return await self._fallback_ddg(query, max_records)

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

    async def _fallback_ddg(self, query: str, max_records: int) -> List[ExtractionResult]:
        """Fallback to DuckDuckGo News when GDELT is rate limited or blocked."""
        import asyncio
        results: List[ExtractionResult] = []
        try:
            from duckduckgo_search import DDGS
            # DDGS is synchronous, so we run it in a thread
            def fetch_ddg():
                return list(DDGS().news(query, max_results=max_records))
            
            loop = asyncio.get_running_loop()
            news_items = await loop.run_in_executor(None, fetch_ddg)
            
            for item in news_items:
                url = item.get("url", "")
                if not url:
                    continue
                
                title = item.get("title", "")
                content = item.get("body", "")
                source = item.get("source", "")
                date_str = item.get("date", "")
                
                published_at = None
                if date_str:
                    try:
                        # e.g., "2026-09-30T07:00:00+00:00"
                        published_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                
                results.append(
                    ExtractionResult(
                        url=normalise_url(url),
                        title=title,
                        content=content,
                        published_at=published_at,
                        language="English",
                        document_type="news_article",
                        source_type="ddg_news",
                        metadata={
                            "ddg_source": source,
                            "ddg_image": item.get("image", "")
                        }
                    )
                )
            logger.info("ddg_fallback_extraction_complete", query=query, articles=len(results))
        except ImportError:
            logger.error("duckduckgo_search not installed, cannot use fallback")
        except Exception as e:
            logger.error(f"DDG fallback failed: {e}")
            
        return results
