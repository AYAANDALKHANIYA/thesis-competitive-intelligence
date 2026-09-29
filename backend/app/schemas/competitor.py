"""Competitor Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.company import CompanyResponse


class CompetitorCreate(BaseModel):
    competitor_id: int
    relationship_type: Optional[str] = Field("direct", max_length=50)


class CompetitorResponse(BaseModel):
    id: int
    company_id: int
    competitor_id: int
    relationship_type: Optional[str] = None
    created_at: datetime
    competitor_company: Optional[CompanyResponse] = None

    model_config = {"from_attributes": True}
