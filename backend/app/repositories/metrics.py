"""Metrics repository — MarketMetric CRUD."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric import MarketMetric


class MetricsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> MarketMetric:
        m = MarketMetric(**kwargs)
        self.db.add(m)
        await self.db.flush()
        return m

    async def get_by_company(
        self,
        company_id: int,
        metric_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 365,
    ) -> List[MarketMetric]:
        query = select(MarketMetric).where(MarketMetric.company_id == company_id)
        if metric_name:
            query = query.where(MarketMetric.metric_name == metric_name)
        if start_date:
            query = query.where(MarketMetric.metric_date >= start_date)
        if end_date:
            query = query.where(MarketMetric.metric_date <= end_date)
        result = await self.db.execute(
            query.order_by(MarketMetric.metric_date.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest(
        self, company_id: int, metric_name: str
    ) -> Optional[MarketMetric]:
        result = await self.db.execute(
            select(MarketMetric)
            .where(
                MarketMetric.company_id == company_id,
                MarketMetric.metric_name == metric_name,
            )
            .order_by(MarketMetric.metric_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        company_id: int,
        metric_name: str,
        metric_date: date,
        metric_value: Optional[float],
        components: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> MarketMetric:
        """Create or update a metric for a specific date."""
        result = await self.db.execute(
            select(MarketMetric).where(
                MarketMetric.company_id == company_id,
                MarketMetric.metric_name == metric_name,
                MarketMetric.metric_date == metric_date,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.metric_value = metric_value
            existing.components = components
            existing.metadata_ = metadata
            await self.db.flush()
            return existing
        return await self.create(
            company_id=company_id,
            metric_name=metric_name,
            metric_date=metric_date,
            metric_value=metric_value,
            components=components,
            metadata_=metadata,
        )
