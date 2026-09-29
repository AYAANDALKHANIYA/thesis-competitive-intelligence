"""PageSpeed Insights API extractor."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

from app.core.config import get_settings

class PageSpeedExtractor:
    """Extracts performance metrics from Google PageSpeed Insights."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.PAGESPEED_API_KEY

    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch PageSpeed metrics for a given URL (desktop strategy)."""
        if not self.api_key:
            logger.info("pagespeed_api_key_missing")
            return None

        # Ensure the URL is valid
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": url,
            "key": self.api_key,
            "strategy": "desktop",
            "category": ["performance", "accessibility", "best-practices", "seo"]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                if response.status_code != 200:
                    logger.warning("pagespeed_api_error", url=url, status=response.status_code, text=response.text[:200])
                    return None

                data = response.json()
                lighthouse_res = data.get("lighthouseResult", {})
                categories = lighthouse_res.get("categories", {})
                
                # Multiply by 100 to get a 0-100 score instead of 0.0-1.0
                performance = categories.get("performance", {}).get("score", 0) * 100 if categories.get("performance", {}).get("score") is not None else None
                accessibility = categories.get("accessibility", {}).get("score", 0) * 100 if categories.get("accessibility", {}).get("score") is not None else None
                best_practices = categories.get("best-practices", {}).get("score", 0) * 100 if categories.get("best-practices", {}).get("score") is not None else None
                seo = categories.get("seo", {}).get("score", 0) * 100 if categories.get("seo", {}).get("score") is not None else None

                metrics = lighthouse_res.get("audits", {}).get("metrics", {}).get("details", {}).get("items", [{}])[0]
                core_web_vitals = {
                    "lcp": metrics.get("largestContentfulPaint"),
                    "fid": metrics.get("maxPotentialFID"), # Proxy for FID
                    "cls": metrics.get("cumulativeLayoutShift"),
                }

                if performance is None and accessibility is None:
                    return None

                return {
                    "performance": performance,
                    "accessibility": accessibility,
                    "best_practices": best_practices,
                    "seo": seo,
                    "core_web_vitals": core_web_vitals
                }
        except Exception as e:
            logger.error("pagespeed_extraction_failed", url=url, error=str(e))
            return None
