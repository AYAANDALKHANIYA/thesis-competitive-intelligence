"""Seed default data sources."""

import asyncio
import sys
sys.path.insert(0, ".")

from app.db.session import async_session_factory
from app.models.source import Source


DEFAULT_SOURCES = [
    {
        "name": "Company Websites",
        "source_type": "website",
        "base_url": None,
        "enabled": True,
        "rate_limit_per_minute": 30,
        "crawl_delay_seconds": 2.0,
    },
    {
        "name": "RSS Feeds",
        "source_type": "rss",
        "base_url": None,
        "enabled": True,
        "rate_limit_per_minute": 60,
        "crawl_delay_seconds": 1.0,
    },
    {
        "name": "GDELT News",
        "source_type": "gdelt",
        "base_url": "https://api.gdeltproject.org/api/v2/doc/doc",
        "enabled": True,
        "rate_limit_per_minute": 60,
        "crawl_delay_seconds": 1.0,
    },
    {
        "name": "SEC EDGAR",
        "source_type": "sec",
        "base_url": "https://data.sec.gov",
        "enabled": True,
        "rate_limit_per_minute": 10,
        "crawl_delay_seconds": 0.5,
    },
]


async def seed():
    async with async_session_factory() as session:
        for source_data in DEFAULT_SOURCES:
            source = Source(**source_data)
            session.add(source)
        await session.commit()
        print(f"Seeded {len(DEFAULT_SOURCES)} sources.")


if __name__ == "__main__":
    asyncio.run(seed())
