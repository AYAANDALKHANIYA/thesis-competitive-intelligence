"""Health check endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.common import DBHealthResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
    )


@router.get("/health/db", response_model=DBHealthResponse)
async def health_db(db: AsyncSession = Depends(get_db)):
    start = time.time()
    await db.execute(text("SELECT 1"))
    latency = (time.time() - start) * 1000
    return DBHealthResponse(status="connected", latency_ms=round(latency, 2))


@router.get("/health/sources")
async def health_sources(db: AsyncSession = Depends(get_db)):
    from app.repositories.sources import SourceRepository
    repo = SourceRepository(db)
    sources, _ = await repo.get_all(limit=100)
    return {
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "source_type": s.source_type,
                "enabled": s.enabled,
            }
            for s in sources
        ]
    }
