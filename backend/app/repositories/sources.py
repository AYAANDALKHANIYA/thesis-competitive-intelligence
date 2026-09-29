"""Source repository — database access layer."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate


class SourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self, offset: int = 0, limit: int = 50, source_type: Optional[str] = None
    ) -> tuple[List[Source], int]:
        query = select(Source)
        count_query = select(func.count(Source.id))

        if source_type:
            query = query.where(Source.source_type == source_type)
            count_query = count_query.where(Source.source_type == source_type)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(Source.id).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, source_id: int) -> Optional[Source]:
        result = await self.db.execute(
            select(Source).where(Source.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_enabled(self, source_type: Optional[str] = None) -> List[Source]:
        query = select(Source).where(Source.enabled.is_(True))
        if source_type:
            query = query.where(Source.source_type == source_type)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: SourceCreate) -> Source:
        source = Source(**data.model_dump())
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def update(self, source_id: int, data: SourceUpdate) -> Optional[Source]:
        source = await self.get_by_id(source_id)
        if not source:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Source.id)))
        return result.scalar() or 0
