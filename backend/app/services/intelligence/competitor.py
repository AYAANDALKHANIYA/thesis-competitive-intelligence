"""
Competitor intelligence service — activity scoring and comparison.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document
from app.models.sentiment import SentimentResult

logger = get_logger(__name__)


class CompetitorIntelligenceService:
    """Calculates competitor activity metrics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_activity_score(
        self, company_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Calculate activity score based on document volume and recency."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(func.count(Document.id)).where(
                Document.company_id == company_id,
                Document.collected_at >= since,
            )
        )
        doc_count = result.scalar() or 0

        # Weighted by recency: recent documents count more
        result = await self.db.execute(
            select(Document.collected_at).where(
                Document.company_id == company_id,
                Document.collected_at >= since,
            )
        )
        dates = result.scalars().all()

        recency_score = 0.0
        now = datetime.now(timezone.utc)
        for collected_at in dates:
            if collected_at.tzinfo is None:
                collected_at = collected_at.replace(tzinfo=timezone.utc)
            age_days = (now - collected_at).days
            weight = max(0.1, 1.0 - (age_days / days))
            recency_score += weight

        # Normalise to 0-100 scale
        normalised = min(100.0, (recency_score / max(days, 1)) * 100)

        return {
            "company_id": company_id,
            "document_count": doc_count,
            "raw_recency_score": round(recency_score, 2),
            "activity_score": round(normalised, 2),
            "period_days": days,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_sentiment_comparison(
        self, company_id: int, competitor_ids: List[int], days: int = 30
    ) -> Dict[str, Any]:
        """Compare sentiment scores between a company and its competitors."""
        all_ids = [company_id] + competitor_ids
        since = datetime.now(timezone.utc) - timedelta(days=days)

        results = {}
        for cid in all_ids:
            avg_result = await self.db.execute(
                select(
                    func.avg(SentimentResult.score).label("avg_score"),
                    func.count(SentimentResult.id).label("count"),
                )
                .join(Document, SentimentResult.document_id == Document.id)
                .where(
                    Document.company_id == cid,
                    Document.collected_at >= since,
                )
            )
            row = avg_result.one_or_none()
            results[cid] = {
                "average_sentiment": round(float(row.avg_score or 0), 4),
                "document_count": int(row.count or 0),
            }

        return {
            "company_id": company_id,
            "period_days": days,
            "scores": results,
        }
