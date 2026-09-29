# -*- coding: utf-8 -*-
"""
Test connection to Railway PostgreSQL.

Verifies:
1. DATABASE_URL is read from .env
2. URL is correctly normalised to postgresql+asyncpg://
3. TCP connection succeeds
4. Basic SQL query works
5. pgvector extension availability

Does NOT print credentials.
"""
import asyncio
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def check_connection():
    print("=" * 60)
    print("  Railway PostgreSQL Connection Test")
    print("=" * 60)

    # 1. Load config
    from app.core.config import get_settings
    settings = get_settings()

    url = settings.DATABASE_URL
    # Mask credentials for display
    from urllib.parse import urlparse
    parsed = urlparse(url)
    masked = f"{parsed.scheme}://{parsed.username}:****@{parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}"
    print(f"\n[1] DATABASE_URL (masked): {masked}")

    # 2. Check URL normalisation
    assert "+asyncpg" in url, f"URL not normalised: missing +asyncpg"
    assert url.startswith("postgresql+asyncpg://"), f"URL scheme incorrect"
    print(f"[2] URL normalisation: PASS (postgresql+asyncpg://)")

    # 3. Test connection
    print(f"[3] Connecting to {parsed.hostname}:{parsed.port}...")
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    try:
        async with engine.connect() as conn:
            # Basic connectivity
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("    SELECT 1: PASS")

            # PostgreSQL version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"    Version: {version[:80]}...")

            # pgvector extension
            result = await conn.execute(text(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
            ))
            row = result.fetchone()
            if row:
                print(f"    pgvector: INSTALLED (version {row[1]})")
            else:
                print("    pgvector: NOT INSTALLED")
                print("    Attempting to create extension...")
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.commit()
                result = await conn.execute(text(
                    "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
                ))
                row = result.fetchone()
                if row:
                    print(f"    pgvector: NOW INSTALLED (version {row[0]})")
                else:
                    print("    pgvector: FAILED TO INSTALL")
                    return 1

            # Check existing tables
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            ))
            tables = [r[0] for r in result.fetchall()]
            print(f"    Existing tables: {len(tables)}")
            if tables:
                for t in tables:
                    print(f"      - {t}")

        print(f"\n{'=' * 60}")
        print(f"  CONNECTION: SUCCESS")
        print(f"  Ready to run: alembic upgrade head")
        print(f"{'=' * 60}")
        return 0

    except Exception as e:
        print(f"\n  CONNECTION FAILED: {e}")
        return 1

    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(check_connection()))
