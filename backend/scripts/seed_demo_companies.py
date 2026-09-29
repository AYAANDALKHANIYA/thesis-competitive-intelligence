"""Seed demo companies — clearly marked as example data."""

import asyncio
import sys
sys.path.insert(0, ".")

from app.db.session import async_session_factory
from app.models.company import Company


DEMO_COMPANIES = [
    {
        "name": "Microsoft",
        "domain": "microsoft.com",
        "industry": "Technology",
        "description": "Demo: Global technology company",
        "country": "US",
        "ticker": "MSFT",
        "sec_cik": "789019",
    },
    {
        "name": "Apple",
        "domain": "apple.com",
        "industry": "Technology",
        "description": "Demo: Consumer electronics and software company",
        "country": "US",
        "ticker": "AAPL",
        "sec_cik": "320193",
    },
    {
        "name": "Google",
        "domain": "google.com",
        "industry": "Technology",
        "description": "Demo: Internet services and AI company",
        "country": "US",
        "ticker": "GOOGL",
        "sec_cik": "1652044",
    },
]


async def seed():
    async with async_session_factory() as session:
        for company_data in DEMO_COMPANIES:
            company = Company(**company_data)
            session.add(company)
        await session.commit()
        print(f"Seeded {len(DEMO_COMPANIES)} demo companies.")


if __name__ == "__main__":
    asyncio.run(seed())
