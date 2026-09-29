"""Ingestion freshness policies — configurable per source type."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import get_settings


class FreshnessPolicy:
    """Determines when a source should be re-checked."""

    # Default intervals per source type (seconds)
    DEFAULTS = {
        "rss": 3600,        # 1 hour
        "gdelt": 86400,     # 1 day
        "website": 86400,   # 1 day
        "sec": 604800,      # 1 week
    }

    def __init__(self) -> None:
        settings = get_settings()
        self.intervals = {
            "rss": settings.RSS_INTERVAL,
            "gdelt": settings.GDELT_INTERVAL,
            "website": settings.WEBSITE_INTERVAL,
            "sec": settings.SEC_INTERVAL,
        }

    def get_interval(self, source_type: str) -> int:
        """Get refresh interval in seconds for a source type."""
        return self.intervals.get(source_type, self.DEFAULTS.get(source_type, 86400))

    def is_fresh(
        self,
        source_type: str,
        last_checked_at: Optional[datetime] = None,
        next_check_at: Optional[datetime] = None,
    ) -> bool:
        """Check if a source is still fresh (no re-check needed)."""
        now = datetime.now(timezone.utc)

        if next_check_at and next_check_at > now:
            return True

        if last_checked_at:
            interval = timedelta(seconds=self.get_interval(source_type))
            return (now - last_checked_at) < interval

        return False

    def next_check_time(
        self,
        source_type: str,
        from_time: Optional[datetime] = None,
    ) -> datetime:
        """Calculate the next check time."""
        base = from_time or datetime.now(timezone.utc)
        interval = timedelta(seconds=self.get_interval(source_type))
        return base + interval
