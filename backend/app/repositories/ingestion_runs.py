"""Ingestion run repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_run import IngestionRun


class IngestionRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> IngestionRun:
        run = IngestionRun(**kwargs)
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def update(self, run: IngestionRun, **kwargs) -> IngestionRun:
        for key, value in kwargs.items():
            setattr(run, key, value)
        await self.db.flush()
        return run

    async def complete(self, run: IngestionRun, status: str = "completed", **stats) -> IngestionRun:
        run.status = status
        run.completed_at = datetime.now(timezone.utc)
        for key, value in stats.items():
            if hasattr(run, key):
                setattr(run, key, value)
        await self.db.flush()
        return run

    async def get_by_id(self, run_id: int) -> Optional[IngestionRun]:
        result = await self.db.execute(
            select(IngestionRun).where(IngestionRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        company_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[List[IngestionRun], int]:
        query = select(IngestionRun)
        count_query = select(func.count(IngestionRun.id))
        if company_id:
            query = query.where(IngestionRun.company_id == company_id)
            count_query = count_query.where(IngestionRun.company_id == company_id)
        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(IngestionRun.started_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(IngestionRun.id)))
        return result.scalar() or 0
