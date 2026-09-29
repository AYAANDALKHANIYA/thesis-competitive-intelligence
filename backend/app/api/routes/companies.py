"""Company CRUD endpoints."""

from __future__ import annotations

from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.companies import CompanyRepository
from app.repositories.competitors import CompetitorRepository
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/api/v1/companies", tags=["Companies"])

def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain



@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    industry: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = CompanyRepository(db)
    offset = (page - 1) * page_size
    companies, total = await repo.get_all(offset=offset, limit=page_size, industry=industry)
    return PaginatedResponse(
        items=[CompanyResponse.model_validate(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db)):
    repo = CompanyRepository(db)
    
    if data.domain:
        data.domain = normalize_domain(data.domain)
        existing = await repo.get_by_domain(data.domain)
        if existing:
            return CompanyResponse.model_validate(existing)
            
    company = await repo.create(data)
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    repo = CompanyRepository(db)
    company = await repo.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int, data: CompanyUpdate, db: AsyncSession = Depends(get_db)
):
    repo = CompanyRepository(db)
    company = await repo.update(company_id, data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    repo = CompanyRepository(db)
    deleted = await repo.delete(company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")


@router.post("/{company_id}/collect", status_code=status.HTTP_200_OK)
async def run_initial_collection(company_id: int, db: AsyncSession = Depends(get_db)):
    """Run a synchronous bounded initial collection for the company and its competitors."""
    company_repo = CompanyRepository(db)
    comp_repo = CompetitorRepository(db)
    
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    if not company.is_primary:
        raise HTTPException(status_code=403, detail="Collection can only be initiated for the primary configured organization.")
        
    orchestrator = IngestionOrchestrator(db)
    
    results = {
        "company": company.name,
        "company_collection": None,
        "competitors_collection": []
    }
    
    # Run for primary company
    try:
        primary_stats = await orchestrator.run_ingestion(
            company_id=company.id,
            company_name=company.name,
            company_domain=company.domain,
            sec_cik=company.sec_cik
        )
        results["company_collection"] = primary_stats
        results["company_status"] = "success"
    except Exception as e:
        results["company_status"] = "error"
        results["company_error"] = str(e)
    
    # Run for competitors
    competitors = await comp_repo.get_by_company(company_id)
    for comp in competitors:
        comp_company = await company_repo.get_by_id(comp.competitor_id)
        if comp_company:
            try:
                comp_stats = await orchestrator.run_ingestion(
                    company_id=comp_company.id,
                    company_name=comp_company.name,
                    company_domain=comp_company.domain,
                    sec_cik=comp_company.sec_cik
                )
                results["competitors_collection"].append({
                    "name": comp_company.name,
                    "stats": comp_stats,
                    "status": "success"
                })
            except Exception as e:
                results["competitors_collection"].append({
                    "name": comp_company.name,
                    "status": "error",
                    "error": str(e)
                })
            
    return results
