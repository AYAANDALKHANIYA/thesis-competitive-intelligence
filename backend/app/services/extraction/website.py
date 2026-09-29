"""
Website extractor — targeted crawling of company public pages.

Respects robots.txt, configurable URL patterns, page limits, and crawl delays.
Includes SSRF protection: blocks requests to private/internal IP ranges.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.services.extraction.base import BaseExtractor, ExtractionResult, normalise_url

logger = get_logger(__name__)


def _is_safe_url(url: str) -> bool:
    """Block requests to private/internal IP ranges (SSRF protection)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False

    # Block obviously private hostnames
    if hostname in ("localhost", "0.0.0.0"):
        return False
    if hostname.endswith(".local") or hostname.endswith(".internal"):
        return False

    try:
        # Resolve hostname and check if IP is private
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        for family, _, _, _, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                logger.warning("ssrf_blocked", url=url, ip=str(ip))
                return False
    except (socket.gaierror, ValueError):
        # Cannot resolve — allow the request (httpx will fail gracefully)
        pass

    return True

# Default patterns for pages worth crawling
DEFAULT_URL_PATTERNS: List[str] = [
    r"/$",
    r"/about",
    r"/product",
    r"/service",
    r"/pricing",
    r"/feature",
    r"/blog",
    r"/news",
    r"/press",
    r"/release",
    r"/announcement",
    r"/update",
    r"/solution",
    r"/resource",
    r"/case",
    r"/insight",
]

# Patterns to exclude
EXCLUDE_PATTERNS: List[str] = [
    r"\.(pdf|zip|png|jpg|jpeg|gif|svg|mp4|mp3|ico|css|js|woff|ttf|eot)$",
    r"/login",
    r"/signup",
    r"/register",
    r"/cart",
    r"/checkout",
    r"/account",
    r"/admin",
    r"/api/",
    r"/feed",
    r"#",
    r"\?.*page=",
]


class WebsiteExtractor(BaseExtractor):
    """Extracts content from company public website pages."""

    source_type = "website"

    async def extract(
        self,
        company_name: str,
        company_domain: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExtractionResult]:
        if not company_domain:
            logger.warning("website_extract_no_domain", company=company_name)
            return []

        config = config or {}
        max_pages = config.get("max_pages", 20)
        crawl_delay = config.get("crawl_delay", self.settings.DEFAULT_CRAWL_DELAY)
        url_patterns = config.get("url_patterns", DEFAULT_URL_PATTERNS)

        base_url = f"https://{company_domain}"

        # SSRF protection: block private/internal IP ranges
        if not _is_safe_url(base_url):
            logger.warning("website_ssrf_blocked", domain=company_domain)
            return []

        source_key = f"website:{company_domain}"
        rate_limit = config.get("rate_limit", self.settings.DEFAULT_RATE_LIMIT)

        # Discover URLs from the homepage
        discovered_urls = await self._discover_urls(
            base_url, company_domain, url_patterns, max_pages, source_key, rate_limit
        )

        results: List[ExtractionResult] = []
        for url in discovered_urls[:max_pages]:
            await asyncio.sleep(crawl_delay)
            result = await self._extract_page(url, source_key, rate_limit)
            if result:
                results.append(result)

        logger.info(
            "website_extraction_complete",
            company=company_name,
            domain=company_domain,
            pages_extracted=len(results),
        )
        return results

    async def _discover_urls(
        self,
        base_url: str,
        domain: str,
        patterns: List[str],
        max_urls: int,
        source_key: str,
        rate_limit: int,
    ) -> List[str]:
        """Discover relevant URLs from the homepage."""
        urls = {normalise_url(base_url)}

        response = await self.fetch_url(base_url, source_key, rate_limit)
        if not response or response.status_code != 200:
            return list(urls)

        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Only same domain
            if parsed.netloc.lower().replace("www.", "") != domain.lower().replace("www.", ""):
                continue

            # Check against exclude patterns
            if any(re.search(pat, full_url, re.IGNORECASE) for pat in EXCLUDE_PATTERNS):
                continue

            # Check against include patterns
            if any(re.search(pat, parsed.path, re.IGNORECASE) for pat in patterns):
                urls.add(normalise_url(full_url))

            if len(urls) >= max_urls:
                break

        return list(urls)

    async def _extract_page(
        self, url: str, source_key: str, rate_limit: int
    ) -> Optional[ExtractionResult]:
        """Extract content from a single page."""
        response = await self.fetch_url(url, source_key, rate_limit)
        if not response or response.status_code != 200:
            return None

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # Extract title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract SEO tags
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = str(meta_tag["content"])

        h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all("h1")]
        h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]

        # Extract Canonical
        canonical = ""
        canonical_tag = soup.find("link", rel="canonical")
        if canonical_tag and canonical_tag.get("href"):
            canonical = str(canonical_tag["href"])

        # Schema (ld+json)
        has_schema = len(soup.find_all("script", type="application/ld+json")) > 0
            
        # Images with alt
        images = soup.find_all("img")
        images_count = len(images)
        images_with_alt = sum(1 for img in images if img.get("alt") and str(img.get("alt")).strip() != "")
        
        # Internal linking (very simple count of relative or same-domain links)
        internal_links = 0
        parsed_base = urlparse(url)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("/") or (parsed_base.netloc in href):
                internal_links += 1

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        # Get main content
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if not main:
            return None

        text = main.get_text(separator="\n", strip=True)

        # Minimum content check
        if len(text.split()) < 20:
            return None

        return ExtractionResult(
            url=normalise_url(url),
            title=title,
            content=text,
            document_type="webpage",
            source_type="website",
            metadata={
                "etag": response.headers.get("etag"),
                "last_modified": response.headers.get("last-modified"),
                "meta_description": meta_desc,
                "h1_tags": h1_tags,
                "h2_tags": h2_tags,
                "has_canonical": bool(canonical),
                "has_schema": has_schema,
                "images_count": images_count,
                "images_with_alt": images_with_alt,
                "internal_links": internal_links,
                "status_code": response.status_code,
            },
        )
