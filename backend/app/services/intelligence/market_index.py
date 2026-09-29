"""
Market Activity Index — configurable composite index.

Components: news_volume, sentiment, topic_momentum, competitor_activity, content_activity.
All normalised before combination. Weights are configurable.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.document import Document
from app.models.sentiment import SentimentResult
from app.models.topic import DocumentTopic
from app.repositories.metrics import MetricsRepository

logger = get_logger(__name__)


class MarketActivityIndexService:
    """Calculates and stores the Market Activity Index."""

    METRIC_NAME = "market_activity_index"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.metrics_repo = MetricsRepository(db)

    async def calculate(
        self, company_id: int, target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate the Market Activity Index for a company on a specific date."""
        target = target_date or date.today()
        period_days = 30

        weights = {
            "news_volume": self.settings.MAI_WEIGHT_NEWS_VOLUME,
            "sentiment": self.settings.MAI_WEIGHT_SENTIMENT,
            "topic_momentum": self.settings.MAI_WEIGHT_TOPIC_MOMENTUM,
            "competitor_activity": self.settings.MAI_WEIGHT_COMPETITOR_ACTIVITY,
            "content_activity": self.settings.MAI_WEIGHT_CONTENT_ACTIVITY,
        }

        components = {}

        # 1. News volume (normalised to 0-1)
        since = datetime.combine(
            target - timedelta(days=period_days), datetime.min.time()
        ).replace(tzinfo=timezone.utc)
        until = datetime.combine(target, datetime.max.time()).replace(tzinfo=timezone.utc)

        doc_count_result = await self.db.execute(
            select(func.count(Document.id)).where(
                Document.company_id == company_id,
                Document.collected_at >= since,
                Document.collected_at <= until,
            )
        )
        doc_count = doc_count_result.scalar() or 0
        components["news_volume"] = min(1.0, doc_count / max(period_days, 1))

        # 2. Sentiment (normalise: map [-1, 1] → [0, 1])
        sent_result = await self.db.execute(
            select(func.avg(SentimentResult.score))
            .join(Document, SentimentResult.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= since,
                Document.collected_at <= until,
            )
        )
        avg_sentiment = float(sent_result.scalar() or 0.5)
        components["sentiment"] = max(0.0, min(1.0, (avg_sentiment + 1) / 2))

        # 3. Topic momentum (proportion of topics growing)
        topic_result = await self.db.execute(
            select(func.count(DocumentTopic.id))
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= since,
                Document.collected_at <= until,
            )
        )
        topic_count = topic_result.scalar() or 0
        components["topic_momentum"] = min(1.0, topic_count / max(period_days * 2, 1))

        # 4. Review/Mention Activity (competitor mentions + news volume proxy)
        from app.models.competitor import Competitor
        comp_result = await self.db.execute(
            select(func.count(Document.id))
            .join(Competitor, Document.company_id == Competitor.competitor_id)
            .where(
                Competitor.company_id == company_id,
                Document.collected_at >= since,
                Document.collected_at <= until,
            )
        )
        comp_count = comp_result.scalar() or 0
        
        components["review_mention_activity"] = min(1.0, (doc_count + comp_count) / max(period_days, 1))

        # 5. Content activity (docs per day normalised)
        docs_per_day = doc_count / max(period_days, 1)
        components["content_activity"] = min(1.0, docs_per_day / 5.0)

        # Calculate weighted index
        # 30% Content Activity
        # 30% Review/Mention Activity
        # 20% Topic Momentum
        # 20% Sentiment
        weights = {
            "content_activity": 0.30,
            "review_mention_activity": 0.30,
            "topic_momentum": 0.20,
            "sentiment": 0.20,
        }
        
        valid_weight = 0.0
        index_value = 0.0
        for key, weight in weights.items():
            if components[key] > 0 or key in ["sentiment"]: # Sentiment is always somewhat valid if exists
                index_value += components[key] * weight
                valid_weight += weight
                
        if valid_weight >= 0.5:
            index_value = index_value / valid_weight # Scale up
            index_value = round(min(1.0, max(0.0, index_value)) * 100, 2)
            status = "available"
        else:
            index_value = None
            status = "insufficient_data"

        # Persist
        await self.metrics_repo.upsert(
            company_id=company_id,
            metric_name=self.METRIC_NAME,
            metric_date=target,
            metric_value=index_value,
            components={
                "raw_components": {k: round(v, 4) for k, v in components.items()},
                "weights": weights,
                "status": status,
                "valid_weight": valid_weight,
                "period_days": period_days,
                "document_count": doc_count,
            },
        )

        # Also store individual component metrics
        name_map = {
            "sentiment": "Sentiment",
            "topic_momentum": "Topic Momentum",
            "review_mention_activity": "Review/Mention Activity",
            "content_activity": "Content Activity"
        }
        for comp_name, comp_value in components.items():
            canonical_name = name_map.get(comp_name, f"mai_component_{comp_name}")
            await self.metrics_repo.upsert(
                company_id=company_id,
                metric_name=canonical_name,
                metric_date=target,
                metric_value=round(comp_value * 100, 2),
            )

        logger.info(
            "market_activity_index_calculated",
            company_id=company_id,
            date=target.isoformat(),
            index=index_value,
        )

        return {
            "company_id": company_id,
            "metric_date": target.isoformat(),
            "index_value": index_value,
            "components": {k: round(v, 4) for k, v in components.items()},
            "weights": weights,
        }
