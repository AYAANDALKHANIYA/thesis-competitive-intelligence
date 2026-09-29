"""
Trend analysis service — topic momentum and time-series trend detection.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document
from app.models.metric import MarketMetric
from app.models.sentiment import SentimentResult
from app.models.topic import DocumentTopic, Topic

logger = get_logger(__name__)


class TrendService:
    """Analyses trends in topics, sentiment, and document activity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_topic_momentum(
        self, company_id: int, days: int = 60
    ) -> List[Dict[str, Any]]:
        """Calculate topic momentum: compare recent vs historical document counts per topic."""
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=days // 2)
        historical_cutoff = now - timedelta(days=days)

        # Get topic counts for recent and historical periods
        recent_result = await self.db.execute(
            select(
                Topic.id,
                Topic.name,
                func.count(DocumentTopic.id).label("count"),
            )
            .join(DocumentTopic, Topic.id == DocumentTopic.topic_id)
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= recent_cutoff,
            )
            .group_by(Topic.id, Topic.name)
        )
        recent_counts = {row.id: {"name": row.name, "count": row.count} for row in recent_result.all()}

        historical_result = await self.db.execute(
            select(
                Topic.id,
                func.count(DocumentTopic.id).label("count"),
            )
            .join(DocumentTopic, Topic.id == DocumentTopic.topic_id)
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= historical_cutoff,
                Document.collected_at < recent_cutoff,
            )
            .group_by(Topic.id)
        )
        historical_counts = {row.id: row.count for row in historical_result.all()}

        momentum = []
        all_topic_ids = set(recent_counts.keys()) | set(historical_counts.keys())
        for tid in all_topic_ids:
            recent_count = recent_counts.get(tid, {}).get("count", 0)
            hist_count = historical_counts.get(tid, 0)
            name = recent_counts.get(tid, {}).get("name", f"Topic_{tid}")

            if hist_count > 0:
                growth = (recent_count - hist_count) / hist_count
            elif recent_count > 0:
                growth = 1.0
            else:
                growth = 0.0

            momentum.append({
                "topic_id": tid,
                "topic_name": name,
                "recent_count": recent_count,
                "historical_count": hist_count,
                "growth_rate": round(growth, 4),
                "momentum": "accelerating" if growth > 0.2 else "declining" if growth < -0.2 else "stable",
            })

        momentum.sort(key=lambda x: x["growth_rate"], reverse=True)
        return momentum

    async def get_sentiment_trend(
        self, company_id: int, days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get daily average sentiment trend."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date_trunc("day", Document.collected_at).label("day"),
                func.avg(SentimentResult.score).label("avg_score"),
                func.count(SentimentResult.id).label("count"),
            )
            .join(Document, SentimentResult.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= since,
            )
            .group_by("day")
            .order_by("day")
        )

        return [
            {
                "date": row.day.date().isoformat() if row.day else None,
                "average_sentiment": round(float(row.avg_score or 0), 4),
                "document_count": int(row.count),
            }
            for row in result.all()
        ]

    async def get_activity_trend(
        self, company_id: int, days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get daily document count trend."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date_trunc("day", Document.collected_at).label("day"),
                func.count(Document.id).label("count"),
            )
            .where(
                Document.company_id == company_id,
                Document.collected_at >= since,
            )
            .group_by("day")
            .order_by("day")
        )

        return [
            {
                "date": row.day.date().isoformat() if row.day else None,
                "document_count": int(row.count),
            }
            for row in result.all()
        ]
