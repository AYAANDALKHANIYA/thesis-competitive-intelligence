"""Source state repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_state import SourceState


class SourceStateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(
        self, source_id: int, company_id: int, url: str
    ) -> Optional[SourceState]:
        result = await self.db.execute(
            select(SourceState).where(
                SourceState.source_id == source_id,
                SourceState.company_id == company_id,
                SourceState.url == url,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        source_id: int,
        company_id: int,
        url: str,
        **kwargs,
    ) -> SourceState:
        state = await self.get(source_id, company_id, url)
        if state:
            for key, value in kwargs.items():
                setattr(state, key, value)
            await self.db.flush()
            return state
        state = SourceState(
            source_id=source_id, company_id=company_id, url=url, **kwargs
        )
        self.db.add(state)
        await self.db.flush()
        return state

    async def get_due_for_check(
        self, source_id: Optional[int] = None, limit: int = 100
    ) -> List[SourceState]:
        """Get URLs whose next_check_at has passed."""
        now = datetime.now(timezone.utc)
        query = select(SourceState).where(
            (SourceState.next_check_at <= now) | (SourceState.next_check_at.is_(None))
        )
        if source_id:
            query = query.where(SourceState.source_id == source_id)
        result = await self.db.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_by_company(self, company_id: int) -> List[SourceState]:
        result = await self.db.execute(
            select(SourceState).where(SourceState.company_id == company_id)
        )
        return list(result.scalars().all())
