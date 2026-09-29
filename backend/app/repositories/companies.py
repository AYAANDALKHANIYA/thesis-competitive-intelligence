"""Company repository — database access layer."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self, offset: int = 0, limit: int = 50, industry: Optional[str] = None
    ) -> tuple[List[Company], int]:
        query = select(Company)
        count_query = select(func.count(Company.id))

        if industry:
            query = query.where(Company.industry == industry)
            count_query = count_query.where(Company.industry == industry)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(Company.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, company_id: int) -> Optional[Company]:
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Optional[Company]:
        result = await self.db.execute(
            select(Company).where(Company.domain == domain)
        )
        return result.scalar_one_or_none()

    async def create(self, data: CompanyCreate) -> Company:
        company = Company(**data.model_dump())
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def update(self, company_id: int, data: CompanyUpdate) -> Optional[Company]:
        company = await self.get_by_id(company_id)
        if not company:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def delete(self, company_id: int) -> bool:
        company = await self.get_by_id(company_id)
        if not company:
            return False
        await self.db.delete(company)
        await self.db.flush()
        return True

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Company.id)))
        return result.scalar() or 0
