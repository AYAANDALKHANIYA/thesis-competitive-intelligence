"""Common Pydantic schemas: pagination, error responses, timestamps."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str


class DBHealthResponse(BaseModel):
    status: str
    latency_ms: float


class SourceHealthItem(BaseModel):
    source_id: int
    source_name: str
    source_type: str
    enabled: bool
    last_checked: Optional[datetime] = None
    last_status: Optional[str] = None
    error_count: int = 0


class SourceHealthResponse(BaseModel):
    sources: List[SourceHealthItem]
