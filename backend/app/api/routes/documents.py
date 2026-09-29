"""Document endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.session import get_db
from app.repositories.documents import DocumentRepository
from app.schemas.common import PaginatedResponse
from app.schemas.document import DocumentResponse, DocumentSummary

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.get("", response_model=PaginatedResponse[DocumentSummary])
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    company_id: int | None = None,
    source_id: int | None = None,
    is_processed: bool | None = None,
    start_date: datetime | None = Query(None, description="Start date for filtering (inclusive)"),
    end_date: datetime | None = Query(None, description="End date for filtering (inclusive)"),
    db: AsyncSession = Depends(get_db),
):
    repo = DocumentRepository(db)
    offset = (page - 1) * page_size
    docs, total = await repo.get_all(
        offset=offset, limit=page_size,
        company_id=company_id, source_id=source_id, is_processed=is_processed,
        start_date=start_date, end_date=end_date,
    )
    return PaginatedResponse(
        items=[DocumentSummary.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    doc = await repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)
