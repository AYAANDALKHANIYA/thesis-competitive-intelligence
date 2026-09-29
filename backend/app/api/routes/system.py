"""System configuration endpoints."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.session import get_db
from app.models.company import Company
from app.models.competitor import Competitor
from app.schemas.company import CompanyResponse

router = APIRouter(prefix="/api/v1/system", tags=["System"])


class CompetitorConfig(BaseModel):
    name: str
    domain: Optional[str] = None


class SetupRequest(BaseModel):
    company_name: str
    company_domain: str
    industry: Optional[str] = None
    competitors: List[CompetitorConfig] = []


class SystemConfiguration(BaseModel):
    configured: bool
    primary_company: Optional[CompanyResponse] = None


def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith('www.'):
        domain = domain[4:]
    # Remove trailing slash
    if domain.endswith('/'):
        domain = domain[:-1]
    return domain


@router.get("/configuration", response_model=SystemConfiguration)
async def get_configuration(db: AsyncSession = Depends(get_db)):
    """Get the current system configuration."""
    stmt = select(Company).where(Company.is_primary == True).limit(1)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    
    if company:
        return SystemConfiguration(
            configured=True,
            primary_company=CompanyResponse.model_validate(company)
        )
    return SystemConfiguration(configured=False, primary_company=None)


@router.post("/setup", response_model=SystemConfiguration)
async def setup_system(data: SetupRequest, db: AsyncSession = Depends(get_db)):
    """Configure the single primary intelligence profile."""
    # Ensure there are no other primary companies
    await db.execute(update(Company).values(is_primary=False))
    
    company_domain = normalize_domain(data.company_domain)
    
    # Check if primary company exists
    stmt = select(Company).where(Company.domain == company_domain).limit(1)
    result = await db.execute(stmt)
    primary = result.scalar_one_or_none()
    
    if primary:
        primary.name = data.company_name
        primary.industry = data.industry
        primary.is_primary = True
    else:
        primary = Company(
            name=data.company_name,
            domain=company_domain,
            industry=data.industry,
            is_primary=True
        )
        db.add(primary)
    
    await db.flush()
    
    # Handle competitors
    # First, get existing competitors
    stmt = select(Competitor).where(Competitor.company_id == primary.id)
    existing_comps = (await db.execute(stmt)).scalars().all()
    for c in existing_comps:
        await db.delete(c)
        
    await db.flush()
    
    for comp_data in data.competitors:
        comp_domain = normalize_domain(comp_data.domain)
        # Find or create competitor company
        stmt = select(Company).where(Company.domain == comp_domain).limit(1)
        comp_company = (await db.execute(stmt)).scalar_one_or_none()
        if not comp_company:
            comp_company = Company(
                name=comp_data.name,
                domain=comp_domain,
                is_primary=False
            )
            db.add(comp_company)
            await db.flush()
            
        # Create relation
        relation = Competitor(company_id=primary.id, competitor_id=comp_company.id)
        db.add(relation)
        
    await db.commit()
    await db.refresh(primary)
    
    return SystemConfiguration(
        configured=True,
        primary_company=CompanyResponse.model_validate(primary)
    )
