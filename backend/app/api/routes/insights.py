"""Insight endpoints."""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.companies import CompanyRepository
from app.repositories.insights import InsightRepository
from app.schemas.common import PaginatedResponse
from app.schemas.insight import InsightGenerateRequest, InsightResponse
from app.services.llm.insight_generator import InsightGenerator

router = APIRouter(prefix="/api/v1/insights", tags=["Insights"])


@router.get("", response_model=PaginatedResponse[InsightResponse])
async def list_insights(
    company_id: int | None = None,
    insight_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    start_date: datetime | None = Query(None, description="Start date for filtering (inclusive)"),
    end_date: datetime | None = Query(None, description="End date for filtering (inclusive)"),
    db: AsyncSession = Depends(get_db),
):
    repo = InsightRepository(db)
    offset = (page - 1) * page_size
    insights, total = await repo.get_all(
        company_id=company_id, insight_type=insight_type, offset=offset, limit=page_size,
        start_date=start_date, end_date=end_date,
    )
    return PaginatedResponse(
        items=[InsightResponse.model_validate(i) for i in insights],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(insight_id: int, db: AsyncSession = Depends(get_db)):
    repo = InsightRepository(db)
    insight = await repo.get_by_id(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return InsightResponse.model_validate(insight)


@router.post("/generate")
async def generate_insight(
    company_id: int = Query(...),
    request: InsightGenerateRequest = InsightGenerateRequest(),
    db: AsyncSession = Depends(get_db),
):
    company_repo = CompanyRepository(db)
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    generator = InsightGenerator(db)
    results = []
    for insight_type in request.insight_types:
        result = await generator.generate_insight(
            company_id=company.id,
            company_name=company.name,
            insight_type=insight_type,
            force=request.force,
        )
        results.append(result)

    return {"insights": results}
