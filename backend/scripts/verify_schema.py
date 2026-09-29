"""Verify the embedding column type on the Railway PostgreSQL database."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def verify():
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(get_settings().DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        # Check embedding column type
        result = await conn.execute(text("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_name = 'embeddings' AND column_name = 'embedding'
        """))
        row = result.fetchone()
        print(f"Column: {row[0]}")
        print(f"data_type: {row[1]}")
        print(f"udt_name: {row[2]}")
        if row[2] == "vector":
            print("RESULT: VECTOR type (pgvector) -- CORRECT")
        else:
            print(f"RESULT: {row[2]} -- INCORRECT (expected vector)")

        # Check alembic version
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        ver = result.scalar()
        print(f"\nalembic_version: {ver}")

        # Check pgvector extension
        result = await conn.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
        ext = result.scalar()
        print(f"pgvector extension: {ext}")

    await engine.dispose()

asyncio.run(verify())
