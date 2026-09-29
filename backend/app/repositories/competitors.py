"""Competitor repository."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.competitor import Competitor


class CompetitorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_company(self, company_id: int) -> List[Competitor]:
        result = await self.db.execute(
            select(Competitor)
            .options(joinedload(Competitor.competitor_company))
            .where(Competitor.company_id == company_id)
        )
        return list(result.scalars().all())

    async def create(
        self, company_id: int, competitor_id: int, relationship_type: str = "direct"
    ) -> Competitor:
        comp = Competitor(
            company_id=company_id,
            competitor_id=competitor_id,
            relationship_type=relationship_type,
        )
        self.db.add(comp)
        await self.db.flush()
        await self.db.refresh(comp)
        return comp

    async def delete(self, company_id: int, competitor_id: int) -> bool:
        result = await self.db.execute(
            select(Competitor).where(
                Competitor.company_id == company_id,
                Competitor.competitor_id == competitor_id,
            )
        )
        comp = result.scalar_one_or_none()
        if not comp:
            return False
        await self.db.delete(comp)
        await self.db.flush()
        return True
