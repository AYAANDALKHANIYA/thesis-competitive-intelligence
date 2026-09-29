"""Insight Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InsightGenerateRequest(BaseModel):
    insight_types: List[str] = Field(
        default=["competitive", "sentiment", "trend", "market_overview"],
        description="Types of insights to generate",
    )
    force: bool = Field(
        False, description="Force regeneration even if cached insight exists"
    )


class InsightResponse(BaseModel):
    id: int
    company_id: int
    insight_type: str
    title: str
    summary: str
    severity: Optional[str] = None
    confidence: Optional[float] = None
    generated_at: datetime
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class IngestionRunResponse(BaseModel):
    id: int
    company_id: int
    source_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    documents_found: int
    documents_new: int
    documents_changed: int
    documents_skipped: int
    requests_made: int
    errors: int

    model_config = {"from_attributes": True}


class IngestionTriggerRequest(BaseModel):
    company_id: int
    source_types: Optional[List[str]] = None  # None = all enabled sources


class SystemStatsResponse(BaseModel):
    total_companies: int
    total_documents: int
    total_processed: int
    total_sources: int
    total_ingestion_runs: int
    total_predictions: int
    total_insights: int
    total_sentiment_results: int
    total_topics: int
    total_entities: int
