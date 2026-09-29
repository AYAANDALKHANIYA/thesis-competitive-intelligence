"""Analysis Pydantic schemas — sentiment, topics, entities, trends, signals."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.insight import InsightResponse
from app.schemas.company import CompanyResponse


# ── Sentiment ────────────────────────────────────────────────────────────────

class SentimentResponse(BaseModel):
    id: int
    document_id: int
    label: str
    score: float
    confidence: float
    model_name: str
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SentimentSummary(BaseModel):
    company_id: int
    total_documents: int
    positive: int
    neutral: int
    negative: int
    average_score: float
    distribution: Dict[str, float]


# ── Topics ───────────────────────────────────────────────────────────────────

class TopicResponse(BaseModel):
    id: int
    topic_key: int
    name: str
    description: Optional[str] = None
    keywords: Optional[Dict[str, Any]] = None
    document_count: int
    model_version: str
    coherence_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentTopicResponse(BaseModel):
    topic: TopicResponse
    probability: float


# ── Entities ─────────────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    id: int
    document_id: int
    entity_text: str
    entity_type: str
    confidence: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EntitySummary(BaseModel):
    entity_text: str
    entity_type: str
    mention_count: int


# ── Trends ───────────────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    date: date
    value: float
    label: Optional[str] = None


class TrendResponse(BaseModel):
    metric_name: str
    company_id: int
    data_points: List[TrendPoint]
    period_start: date
    period_end: date


# ── Emerging Signals ─────────────────────────────────────────────────────────

class EmergingSignal(BaseModel):
    signal_type: str
    topic: Optional[str] = None
    entity: Optional[str] = None
    current_mentions: int
    previous_mentions: int
    growth_rate: float
    sentiment_shift: Optional[float] = None
    confidence: float
    evidence: List[Dict[str, Any]]
    detected_at: datetime


# ── Market Activity Index ────────────────────────────────────────────────────

class MarketIndexResponse(BaseModel):
    company_id: int
    metric_date: date
    index_value: float
    components: Dict[str, float]
    weights: Dict[str, float]


class MarketMetricResponse(BaseModel):
    id: int
    company_id: int
    metric_name: str
    metric_value: float
    metric_date: date
    components: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ────────────────────────────────────────────────────────────────

class AutomationStatus(BaseModel):
    last_intelligence_update: Optional[datetime] = None
    next_scheduled_collection: Optional[datetime] = None
    new_documents: int = 0
    sources_checked: int = 0


class DashboardResponse(BaseModel):
    company: Optional[CompanyResponse] = None
    market_activity: Optional[MarketIndexResponse] = None
    sentiment: Optional[SentimentSummary] = None
    signals: List[EmergingSignal] = []
    top_topics: List[Dict[str, Any]] = []
    recent_insights: List[InsightResponse] = []
    automation_status: Optional[AutomationStatus] = None
