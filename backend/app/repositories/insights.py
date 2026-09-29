"""Insights repository."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight


class InsightRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> Insight:
        insight = Insight(**kwargs)
        self.db.add(insight)
        await self.db.flush()
        await self.db.refresh(insight)
        return insight

    async def get_all(
        self,
        company_id: Optional[int] = None,
        insight_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[Insight], int]:
        query = select(Insight)
        count_query = select(func.count(Insight.id))

        if company_id:
            query = query.where(Insight.company_id == company_id)
            count_query = count_query.where(Insight.company_id == company_id)
        if insight_type:
            query = query.where(Insight.insight_type == insight_type)
            count_query = count_query.where(Insight.insight_type == insight_type)
        if start_date is not None:
            query = query.where(Insight.generated_at >= start_date)
            count_query = count_query.where(Insight.generated_at >= start_date)
        if end_date is not None:
            query = query.where(Insight.generated_at <= end_date)
            count_query = count_query.where(Insight.generated_at <= end_date)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(Insight.generated_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, insight_id: int) -> Optional[Insight]:
        result = await self.db.execute(
            select(Insight).where(Insight.id == insight_id)
        )
        return result.scalar_one_or_none()

    async def get_by_input_hash(
        self, company_id: int, input_hash: str
    ) -> Optional[Insight]:
        result = await self.db.execute(
            select(Insight).where(
                Insight.company_id == company_id,
                Insight.input_hash == input_hash,
            )
            .order_by(Insight.generated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Insight.id)))
        return result.scalar() or 0
