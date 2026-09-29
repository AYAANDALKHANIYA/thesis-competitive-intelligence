"""
Content normaliser — language detection, metadata normalisation, date parsing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentNormalizer:
    """Normalises document metadata and detects language."""

    def detect_language(self, text: str) -> str:
        """Detect language of text content. Returns ISO 639-1 code."""
        if not text or len(text.split()) < 5:
            return "en"
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            return "en"

    def count_words(self, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())

    def normalise_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Attempt to parse various date formats."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        # Try email date parsing
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            pass

        return None

    def is_valid_content(self, text: str, min_words: int = 20) -> bool:
        """Check if content meets minimum quality bar."""
        if not text:
            return False
        words = text.split()
        if len(words) < min_words:
            return False
        # Check for excessive repetition (sign of nav-only content)
        unique_words = set(w.lower() for w in words)
        if len(unique_words) < len(words) * 0.2:
            return False
        return True
