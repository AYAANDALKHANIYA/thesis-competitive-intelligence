"""Source Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    base_url: Optional[str] = None
    enabled: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    crawl_delay_seconds: Optional[float] = Field(None, ge=0)
    config: Optional[Dict[str, Any]] = None


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(..., pattern=r"^(website|rss|gdelt|sec)$")
    base_url: Optional[str] = None
    enabled: bool = True
    rate_limit_per_minute: int = Field(30, ge=1)
    crawl_delay_seconds: float = Field(2.0, ge=0)
    config: Optional[Dict[str, Any]] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    base_url: Optional[str] = None
    enabled: bool
    rate_limit_per_minute: int
    crawl_delay_seconds: float
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
