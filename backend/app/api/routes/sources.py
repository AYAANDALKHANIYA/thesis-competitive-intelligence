"""Source management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.sources import SourceRepository
from app.schemas.common import PaginatedResponse
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/api/v1/sources", tags=["Sources"])


@router.get("", response_model=PaginatedResponse[SourceResponse])
async def list_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    source_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepository(db)
    offset = (page - 1) * page_size
    sources, total = await repo.get_all(offset=offset, limit=page_size, source_type=source_type)
    return PaginatedResponse(
        items=[SourceResponse.model_validate(s) for s in sources],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    source = await repo.create(data)
    return SourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: int, data: SourceUpdate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    source = await repo.update(source_id, data)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.model_validate(source)
