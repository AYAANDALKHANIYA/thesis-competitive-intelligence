"""Ingestion trigger and status endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, async_session_factory
from app.repositories.companies import CompanyRepository
from app.repositories.ingestion_runs import IngestionRunRepository
from app.schemas.common import PaginatedResponse
from app.schemas.insight import IngestionRunResponse, IngestionTriggerRequest
from app.tasks.analysis_tasks import process_unprocessed_documents
from app.tasks.ingestion_tasks import run_company_ingestion

router = APIRouter(prefix="/api/v1/ingestion", tags=["Ingestion"])


@router.post("/run")
async def trigger_ingestion(
    request: IngestionTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger an ingestion run for a company.

    Runs in background so the API responds immediately.
    """
    company_repo = CompanyRepository(db)
    company = await company_repo.get_by_id(request.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Run ingestion + NLP in background
    async def _background_task():
        async with async_session_factory() as session:
            try:
                await run_company_ingestion(
                    session, request.company_id, request.source_types
                )
                await session.commit()

                # Process NLP on new documents
                await process_unprocessed_documents(session, request.company_id)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                import structlog
                structlog.get_logger().error("background_ingestion_error", error=str(exc))

    background_tasks.add_task(_background_task)

    return {
        "status": "started",
        "company_id": request.company_id,
        "message": "Ingestion started in background. Check /ingestion/runs for status.",
    }


@router.get("/runs", response_model=PaginatedResponse[IngestionRunResponse])
async def list_ingestion_runs(
    company_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    repo = IngestionRunRepository(db)
    offset = (page - 1) * page_size
    runs, total = await repo.get_all(company_id=company_id, offset=offset, limit=page_size)
    return PaginatedResponse(
        items=[IngestionRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/runs/{run_id}", response_model=IngestionRunResponse)
async def get_ingestion_run(run_id: int, db: AsyncSession = Depends(get_db)):
    repo = IngestionRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    return IngestionRunResponse.model_validate(run)
