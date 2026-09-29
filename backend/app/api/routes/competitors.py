"""Competitor management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.companies import CompanyRepository
from app.repositories.competitors import CompetitorRepository
from app.schemas.competitor import CompetitorCreate, CompetitorResponse

router = APIRouter(prefix="/api/v1/companies/{company_id}/competitors", tags=["Competitors"])


@router.get("", response_model=list[CompetitorResponse])
async def list_competitors(company_id: int, db: AsyncSession = Depends(get_db)):
    repo = CompetitorRepository(db)
    competitors = await repo.get_by_company(company_id)
    return [CompetitorResponse.model_validate(c) for c in competitors]


@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def add_competitor(
    company_id: int, data: CompetitorCreate, db: AsyncSession = Depends(get_db)
):
    company_repo = CompanyRepository(db)
    if not await company_repo.get_by_id(company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    if not await company_repo.get_by_id(data.competitor_id):
        raise HTTPException(status_code=404, detail="Competitor company not found")
    if company_id == data.competitor_id:
        raise HTTPException(status_code=400, detail="Cannot add self as competitor")

    repo = CompetitorRepository(db)
    # Check if relationship already exists
    existing_competitors = await repo.get_by_company(company_id)
    comp = next((c for c in existing_competitors if c.competitor_id == data.competitor_id), None)
    
    if not comp:
        try:
            await repo.create(company_id, data.competitor_id, data.relationship_type or "direct")
        except Exception:
            raise HTTPException(status_code=409, detail="Competitor relationship already exists")
            
        # Re-fetch to get joined relationship loaded
        all_competitors = await repo.get_by_company(company_id)
        comp = next((c for c in all_competitors if c.competitor_id == data.competitor_id), None)
            
    return CompetitorResponse.model_validate(comp)


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_competitor(
    company_id: int, competitor_id: int, db: AsyncSession = Depends(get_db)
):
    repo = CompetitorRepository(db)
    deleted = await repo.delete(company_id, competitor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor relationship not found")
