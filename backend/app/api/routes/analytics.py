"""Analytics endpoints — sentiment, topics, entities, trends, signals, market index."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.repositories.analysis import AnalysisRepository
from app.schemas.analysis import (
    EntitySummary,
    MarketIndexResponse,
    SentimentResponse,
    SentimentSummary,
    TopicResponse,
    DashboardResponse,
)
from app.repositories.companies import CompanyRepository
from app.repositories.insights import InsightRepository
from app.models.company import Company
from app.models.competitor import Competitor
from app.services.intelligence.emerging_signals import EmergingSignalService
from app.services.intelligence.market_index import MarketActivityIndexService
from app.services.intelligence.trends import TrendService

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

async def get_authorized_company_id(db: AsyncSession, requested_id: int | None = None) -> int:
    stmt = select(Company).where(Company.is_primary == True).limit(1)
    primary = (await db.execute(stmt)).scalar_one_or_none()
    
    if not primary:
        raise HTTPException(status_code=400, detail="Intelligence profile not configured")
        
    if requested_id is None or requested_id == primary.id:
        return primary.id
        
    stmt = select(Competitor).where(
        Competitor.company_id == primary.id,
        Competitor.competitor_id == requested_id
    ).limit(1)
    is_competitor = (await db.execute(stmt)).scalar_one_or_none()
    
    if not is_competitor:
        raise HTTPException(status_code=403, detail="Requested company is not part of the active intelligence profile")
        
    return requested_id


@router.get("/sentiment")
async def get_sentiment(
    company_id: int | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    authorized_id = await get_authorized_company_id(db, company_id)
    repo = AnalysisRepository(db)
    results = await repo.get_sentiments_by_company(authorized_id, limit=limit)
    sentiments = [SentimentResponse.model_validate(r) for r in results]

    # Compute summary
    total = len(sentiments)
    dist = {"positive": 0, "neutral": 0, "negative": 0}
    score_sum = 0.0
    for s in sentiments:
        dist[s.label] = dist.get(s.label, 0) + 1
        score_sum += s.score

    return {
        "summary": {
            "company_id": authorized_id,
            "total_documents": total,
            "positive": dist.get("positive", 0),
            "neutral": dist.get("neutral", 0),
            "negative": dist.get("negative", 0),
            "average_score": round(score_sum / max(total, 1), 4),
            "distribution": {k: round(v / max(total, 1), 4) for k, v in dist.items()},
        },
        "results": sentiments[:limit],
    }


@router.get("/topics")
async def get_topics(
    company_id: int | None = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    authorized_id = await get_authorized_company_id(db, company_id)
    repo = AnalysisRepository(db)
    topics = await repo.get_topics_by_company(authorized_id, limit=limit)
    return [TopicResponse.model_validate(t) for t in topics]


@router.get("/entities")
async def get_entities(
    company_id: int | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    authorized_id = await get_authorized_company_id(db, company_id)
    repo = AnalysisRepository(db)
    entity_rows = await repo.get_entity_summary_by_company(authorized_id, limit=limit)
    return [
        EntitySummary(
            entity_text=row.entity_text,
            entity_type=row.entity_type,
            mention_count=row.mention_count,
        )
        for row in entity_rows
    ]


@router.get("/trends")
async def get_trends(
    company_id: int | None = Query(None),
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    authorized_id = await get_authorized_company_id(db, company_id)
    trend_svc = TrendService(db)
    return {
        "topic_momentum": await trend_svc.get_topic_momentum(authorized_id, days=days),
        "sentiment_trend": await trend_svc.get_sentiment_trend(authorized_id, days=days),
        "activity_trend": await trend_svc.get_activity_trend(authorized_id, days=days),
    }


@router.get("/signals")
async def get_signals(
    company_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    authorized_id = await get_authorized_company_id(db, company_id)
    signal_svc = EmergingSignalService(db)
    signals = await signal_svc.detect_signals(authorized_id)
    return {"signals": signals, "count": len(signals)}


@router.get("/market-index")
async def get_market_index(
    company_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    authorized_id = await get_authorized_company_id(db, company_id)
    index_svc = MarketActivityIndexService(db)
    result = await index_svc.calculate(authorized_id)
    return result


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    company_id: int | None = Query(None, description="Filter dashboard by company ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated data for the Executive Overview dashboard."""
    authorized_id = await get_authorized_company_id(db, company_id)
    company = None
    company_repo = CompanyRepository(db)
    company_doc = await company_repo.get_by_id(authorized_id)
    if company_doc:
        company = company_doc
            
    # MAI
    index_svc = MarketActivityIndexService(db)
    mai_data = await index_svc.calculate(authorized_id)
        
    # Sentiment Summary (reuse logic from get_sentiment)
    analysis_repo = AnalysisRepository(db)
    results = await analysis_repo.get_sentiments_by_company(authorized_id, limit=200)
    total = len(results)
    dist = {"positive": 0, "neutral": 0, "negative": 0}
    score_sum = 0.0
    for s in results:
        dist[s.label] = dist.get(s.label, 0) + 1
        score_sum += s.score
            
    sentiment_data = {
        "company_id": authorized_id,
        "total_documents": total,
        "positive": dist.get("positive", 0),
        "neutral": dist.get("neutral", 0),
        "negative": dist.get("negative", 0),
        "average_score": round(score_sum / max(total, 1), 4),
        "distribution": {k: round(v / max(total, 1), 4) for k, v in dist.items()},
    }
        
    # Emerging Signals
    signal_svc = EmergingSignalService(db)
    signals = await signal_svc.detect_signals(authorized_id)
        
    # Top Topics
    topics = await analysis_repo.get_topics_by_company(authorized_id, limit=5)
    top_topics = [TopicResponse.model_validate(t).model_dump() for t in topics]
        
    # Recent Insights
    insight_repo = InsightRepository(db)
    docs, _ = await insight_repo.get_all(limit=5, company_id=authorized_id)
    recent_insights = docs
    
    # Automation Status
    from app.services.ingestion.scheduler import scheduler
    from app.models.ingestion_run import IngestionRun
    from sqlalchemy import func
    from datetime import datetime, timedelta, timezone
    
    automation_status = {
        "last_intelligence_update": recent_insights[0].generated_at if recent_insights else None,
        "next_scheduled_collection": None,
        "new_documents": 0,
        "sources_checked": 0
    }
    
    job = scheduler.get_job("scheduled_ingestion")
    if job and job.next_run_time:
        automation_status["next_scheduled_collection"] = job.next_run_time
        
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    run_stats = await db.execute(
        select(
            func.sum(IngestionRun.documents_new),
            func.count(IngestionRun.id)
        )
        .where(
            IngestionRun.company_id == authorized_id,
            IngestionRun.started_at >= last_24h
        )
    )
    row = run_stats.one_or_none()
    if row:
        automation_status["new_documents"] = int(row[0] or 0)
        automation_status["sources_checked"] = int(row[1] or 0)

    return {
        "company": company,
        "market_activity": mai_data,
        "sentiment": sentiment_data,
        "signals": signals[:5],
        "top_topics": top_topics,
        "recent_insights": recent_insights,
        "automation_status": automation_status,
    }
