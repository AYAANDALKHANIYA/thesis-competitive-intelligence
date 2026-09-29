"""
Content cleaner — HTML removal, boilerplate stripping, normalisation.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentCleaner:
    """Cleans and normalises raw document content."""

    # Tags that typically contain non-content elements
    REMOVE_TAGS = [
        "script", "style", "nav", "footer", "header", "aside",
        "iframe", "noscript", "form", "button", "input", "select",
        "textarea", "menu", "menuitem",
    ]

    # Patterns for boilerplate text
    BOILERPLATE_PATTERNS = [
        re.compile(r"cookie\s*(policy|notice|consent)", re.IGNORECASE),
        re.compile(r"subscribe\s*to\s*(our|the)\s*newsletter", re.IGNORECASE),
        re.compile(r"©\s*\d{4}", re.IGNORECASE),
        re.compile(r"all\s*rights\s*reserved", re.IGNORECASE),
        re.compile(r"privacy\s*policy", re.IGNORECASE),
        re.compile(r"terms\s*(of|and)\s*(service|use|conditions)", re.IGNORECASE),
    ]

    def clean(self, raw_content: str, is_html: bool = True) -> Optional[str]:
        """Clean raw content and return normalised text or None if insufficient."""
        if not raw_content or not raw_content.strip():
            return None

        if is_html and "<" in raw_content:
            text = self._extract_from_html(raw_content)
        else:
            text = raw_content

        text = self._normalise_unicode(text)
        text = self._normalise_whitespace(text)
        text = self._remove_boilerplate_lines(text)

        if not self._has_sufficient_content(text):
            return None

        return text

    def _extract_from_html(self, html: str) -> str:
        """Extract meaningful text from HTML."""
        soup = BeautifulSoup(html, "lxml")

        # Remove non-content tags
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Prefer main content areas
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            return main.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    def _normalise_unicode(self, text: str) -> str:
        """NFC-normalise Unicode and replace problematic characters."""
        text = unicodedata.normalize("NFC", text)
        # Replace common Unicode whitespace/dash variants
        text = text.replace("\u2019", "'")
        text = text.replace("\u2018", "'")
        text = text.replace("\u201c", '"')
        text = text.replace("\u201d", '"')
        text = text.replace("\u2014", " — ")
        text = text.replace("\u2013", " – ")
        text = text.replace("\xa0", " ")
        return text

    def _normalise_whitespace(self, text: str) -> str:
        """Collapse excessive whitespace while preserving paragraph breaks."""
        # Replace tabs and multiple spaces with single space
        text = re.sub(r"[^\S\n]+", " ", text)
        # Collapse 3+ newlines into double newlines (paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove leading/trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def _remove_boilerplate_lines(self, text: str) -> str:
        """Remove lines that match common boilerplate patterns."""
        lines = text.split("\n")
        filtered = []
        for line in lines:
            if any(pat.search(line) for pat in self.BOILERPLATE_PATTERNS):
                continue
            filtered.append(line)
        return "\n".join(filtered)

    def _has_sufficient_content(self, text: str, min_words: int = 20) -> bool:
        """Check if cleaned text has enough meaningful content."""
        words = text.split()
        return len(words) >= min_words
