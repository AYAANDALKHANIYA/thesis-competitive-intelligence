"""Document Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    company_id: int
    source_id: int
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: datetime
    language: Optional[str] = None
    document_type: Optional[str] = None
    word_count: Optional[int] = None
    is_processed: bool = False
    metadata_: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentSummary(BaseModel):
    """Lightweight document representation for lists."""
    id: int
    company_id: int
    source_id: int
    url: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: datetime
    language: Optional[str] = None
    document_type: Optional[str] = None
    word_count: Optional[int] = None
    is_processed: bool = False

    model_config = {"from_attributes": True}
