# -*- coding: utf-8 -*-
"""
THESIS DATASET SEEDING SCRIPT

Seeds the PostgreSQL database with real B2B SaaS companies, sources, and
competitor relationships for thesis validation.

Usage: python scripts/seed_thesis_dataset.py

Requires:
- DATABASE_URL pointing to a real PostgreSQL instance
- Alembic migration already applied (alembic upgrade head)
"""
import asyncio
import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.source import Source


# ── Dataset Definition ────────────────────────────────────────────────
COMPANIES = [
    {
        "name": "Salesforce",
        "domain": "salesforce.com",
        "industry": "Enterprise SaaS",
        "country": "US",
        "ticker": "CRM",
        "sec_cik": "0001108524",
        "description": "Cloud-based CRM and enterprise software platform",
    },
    {
        "name": "HubSpot",
        "domain": "hubspot.com",
        "industry": "Marketing SaaS",
        "country": "US",
        "ticker": "HUBS",
        "sec_cik": "0001404655",
        "description": "Inbound marketing, sales, and CRM platform",
    },
    {
        "name": "ServiceNow",
        "domain": "servicenow.com",
        "industry": "IT Service Management",
        "country": "US",
        "ticker": "NOW",
        "sec_cik": "0001373715",
        "description": "Digital workflow and IT service management platform",
    },
    {
        "name": "Atlassian",
        "domain": "atlassian.com",
        "industry": "Collaboration SaaS",
        "country": "AU",
        "ticker": "TEAM",
        "sec_cik": "0001650372",
        "description": "Team collaboration and project management tools (Jira, Confluence)",
    },
    {
        "name": "Datadog",
        "domain": "datadoghq.com",
        "industry": "Observability SaaS",
        "country": "US",
        "ticker": "DDOG",
        "sec_cik": "0001561550",
        "description": "Cloud monitoring and analytics platform",
    },
    {
        "name": "Snowflake",
        "domain": "snowflake.com",
        "industry": "Data Cloud",
        "country": "US",
        "ticker": "SNOW",
        "sec_cik": "0001640147",
        "description": "Cloud-based data warehousing and analytics",
    },
    {
        "name": "CrowdStrike",
        "domain": "crowdstrike.com",
        "industry": "Cybersecurity SaaS",
        "country": "US",
        "ticker": "CRWD",
        "sec_cik": "0001535527",
        "description": "Cloud-native endpoint security platform",
    },
]

COMPETITOR_PAIRS = [
    ("Salesforce", "HubSpot"),
    ("Salesforce", "ServiceNow"),
    ("HubSpot", "Salesforce"),
    ("Atlassian", "ServiceNow"),
    ("Datadog", "CrowdStrike"),
    ("Snowflake", "Datadog"),
]

SOURCES = [
    {
        "name": "GDELT News",
        "source_type": "gdelt",
        "base_url": "https://api.gdeltproject.org/api/v2/doc/doc",
        "rate_limit_per_minute": 10,
        "crawl_delay_seconds": 5.0,
        "config": {"max_records": 10, "timespan": "7d"},
    },
    {
        "name": "SEC EDGAR Filings",
        "source_type": "sec",
        "base_url": "https://efts.sec.gov/LATEST/search-index",
        "rate_limit_per_minute": 10,
        "crawl_delay_seconds": 1.0,
        "config": {"form_types": ["10-K", "10-Q", "8-K"]},
    },
]


async def seed_companies(session: AsyncSession) -> dict:
    """Seed companies, returning name->id mapping."""
    company_map = {}
    for data in COMPANIES:
        # Check if exists
        result = await session.execute(
            select(Company).where(Company.name == data["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  [SKIP] Company already exists: {data['name']} (id={existing.id})")
            company_map[data["name"]] = existing.id
            continue

        company = Company(**data)
        session.add(company)
        await session.flush()
        company_map[data["name"]] = company.id
        print(f"  [CREATED] {data['name']} (id={company.id})")

    return company_map


async def seed_competitors(session: AsyncSession, company_map: dict):
    """Seed competitor relationships."""
    for company_name, competitor_name in COMPETITOR_PAIRS:
        company_id = company_map.get(company_name)
        competitor_id = company_map.get(competitor_name)
        if not company_id or not competitor_id:
            print(f"  [SKIP] Missing company for pair: {company_name} -> {competitor_name}")
            continue

        # Check if exists
        result = await session.execute(
            select(Competitor).where(
                Competitor.company_id == company_id,
                Competitor.competitor_id == competitor_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  [SKIP] Competitor pair exists: {company_name} -> {competitor_name}")
            continue

        comp = Competitor(
            company_id=company_id,
            competitor_id=competitor_id,
            relationship_type="direct",
        )
        session.add(comp)
        await session.flush()
        print(f"  [CREATED] {company_name} -> {competitor_name}")


async def seed_sources(session: AsyncSession):
    """Seed data sources."""
    for data in SOURCES:
        result = await session.execute(
            select(Source).where(Source.name == data["name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"  [SKIP] Source already exists: {data['name']} (id={existing.id})")
            continue

        source = Source(**data)
        session.add(source)
        await session.flush()
        print(f"  [CREATED] {data['name']} (id={source.id}, type={data['source_type']})")


async def verify_database(session: AsyncSession):
    """Verify database state after seeding."""
    print("\n  --- Database Verification ---")

    # Check pgvector extension
    try:
        result = await session.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
        row = result.fetchone()
        if row:
            print(f"  [OK] pgvector extension: version {row[0]}")
        else:
            print(f"  [WARN] pgvector extension not found -- run: CREATE EXTENSION IF NOT EXISTS vector")
    except Exception as e:
        print(f"  [INFO] pgvector check skipped (may not be PostgreSQL): {e}")

    # Count tables
    tables = ["companies", "competitors", "sources", "documents", "sentiment_results",
              "topics", "entities", "embeddings", "market_metrics", "predictions",
              "model_versions", "ingestion_runs", "source_states", "insights"]

    for table in tables:
        try:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count} rows")
        except Exception as e:
            print(f"  {table}: ERROR - {e}")


async def main():
    print("=" * 70)
    print("  THESIS DATASET SEEDING")
    print("=" * 70)

    async with async_session_factory() as session:
        try:
            # 1. Seed companies
            print("\n[1] Seeding companies...")
            company_map = await seed_companies(session)
            await session.commit()

            # 2. Seed competitors
            print("\n[2] Seeding competitor relationships...")
            await seed_competitors(session, company_map)
            await session.commit()

            # 3. Seed sources
            print("\n[3] Seeding data sources...")
            await seed_sources(session)
            await session.commit()

            # 4. Verify
            print("\n[4] Verifying database state...")
            await verify_database(session)

            print("\n" + "=" * 70)
            print("  SEEDING COMPLETE")
            print(f"  Companies: {len(COMPANIES)}")
            print(f"  Competitor pairs: {len(COMPETITOR_PAIRS)}")
            print(f"  Sources: {len(SOURCES)}")
            print("=" * 70)

        except Exception as e:
            await session.rollback()
            print(f"\n  [ERROR] Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
