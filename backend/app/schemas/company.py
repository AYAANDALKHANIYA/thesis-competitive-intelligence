"""Company Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    country: Optional[str] = Field(None, max_length=100)
    ticker: Optional[str] = Field(None, max_length=20)
    sec_cik: Optional[str] = Field(None, max_length=20)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    country: Optional[str] = Field(None, max_length=100)
    ticker: Optional[str] = Field(None, max_length=20)
    sec_cik: Optional[str] = Field(None, max_length=20)


class CompanyResponse(BaseModel):
    id: int
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    ticker: Optional[str] = None
    sec_cik: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
