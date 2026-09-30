"""pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Override settings before anything else
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["OPENAI_API_KEY"] = "test-key-not-real"
os.environ["GROQ_API_KEY"] = "test-groq-key"

# ── SQLite compatibility adapters ──────────────────────────────────────────
# Register compilers for PostgreSQL-specific types so SQLite can create tables.
from sqlalchemy.ext.compiler import compiles

# JSONB → JSON on SQLite
from sqlalchemy.dialects.postgresql import JSONB
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

# ARRAY → TEXT on SQLite
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
@compiles(PG_ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

# pgvector Vector → TEXT on SQLite
try:
    from pgvector.sqlalchemy import Vector
    @compiles(Vector, "sqlite")
    def compile_vector_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass

# ── End SQLite adapters ───────────────────────────────────────────────────

from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    # Create tables using SQLite for testing (no Postgres needed)
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.db.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    from app.db.session import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    # Remove test DB file
    import pathlib
    db_file = pathlib.Path("./test.db")
    if db_file.exists():
        db_file.unlink()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.db.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///./test.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with test_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
