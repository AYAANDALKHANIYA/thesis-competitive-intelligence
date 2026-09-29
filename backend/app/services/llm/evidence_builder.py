"""
Evidence builder — selects structured evidence from stored analytics.

Every evidence item contains enough information to trace back to the original source.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.document import Document
from app.models.company import Company
from app.models.source import Source
from app.models.entity import Entity
from app.models.metric import MarketMetric
from app.models.sentiment import SentimentResult
from app.models.topic import DocumentTopic, Topic

logger = get_logger(__name__)


class EvidenceBuilder:
    """Builds structured evidence context for LLM insight generation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def build_evidence(
        self, company_id: int, insight_type: str = "market_overview"
    ) -> Dict[str, Any]:
        """Build complete evidence package for a company.

        Returns a dict of categorised evidence items.
        """
        evidence: Dict[str, Any] = {
            "company_id": company_id,
            "insight_type": insight_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sentiment": await self._sentiment_evidence(company_id),
            "topics": await self._topic_evidence(company_id),
            "entities": await self._entity_evidence(company_id),
            "metrics": await self._metric_evidence(company_id),
            "recent_documents": await self._document_evidence(company_id),
        }

        return evidence

    def compute_evidence_hash(self, evidence: Dict) -> str:
        """Compute a hash of the full evidence package for caching."""
        # Remove volatile fields that don't represent meaningful data changes
        evidence_copy = dict(evidence)
        if "generated_at" in evidence_copy:
            del evidence_copy["generated_at"]
            
        key_data = json.dumps(evidence_copy, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def _sentiment_evidence(self, company_id: int) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=30)
        result = await self.db.execute(
            select(
                func.avg(SentimentResult.score).label("avg"),
                func.count(SentimentResult.id).label("count"),
                SentimentResult.label,
                func.count(SentimentResult.id).label("label_count"),
            )
            .join(Document, SentimentResult.document_id == Document.id)
            .where(Document.company_id == company_id, Document.collected_at >= since)
            .group_by(SentimentResult.label)
        )
        rows = result.all()

        distribution = {}
        total = 0
        weighted_sum = 0.0
        for row in rows:
            distribution[row.label] = row.label_count
            total += row.label_count

        avg_result = await self.db.execute(
            select(func.avg(SentimentResult.score))
            .join(Document, SentimentResult.document_id == Document.id)
            .where(Document.company_id == company_id, Document.collected_at >= since)
        )
        avg_score = float(avg_result.scalar() or 0)

        return {
            "average_score": round(avg_score, 4),
            "total_analysed": total,
            "distribution": distribution,
            "period_days": 30,
        }

    async def _topic_evidence(self, company_id: int) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(
                Topic.name,
                Topic.keywords,
                func.count(DocumentTopic.id).label("doc_count"),
            )
            .join(DocumentTopic, Topic.id == DocumentTopic.topic_id)
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(Document.company_id == company_id)
            .group_by(Topic.id, Topic.name, Topic.keywords)
            .order_by(func.count(DocumentTopic.id).desc())
            .limit(10)
        )
        return [
            {
                "topic": row.name,
                "keywords": row.keywords,
                "document_count": row.doc_count,
            }
            for row in result.all()
        ]

    async def _entity_evidence(self, company_id: int) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(
                Entity.entity_text,
                Entity.entity_type,
                func.count(Entity.id).label("count"),
            )
            .join(Document, Entity.document_id == Document.id)
            .where(Document.company_id == company_id)
            .group_by(Entity.entity_text, Entity.entity_type)
            .order_by(func.count(Entity.id).desc())
            .limit(20)
        )
        return [
            {"entity": row.entity_text, "type": row.entity_type, "mentions": row.count}
            for row in result.all()
        ]

    async def _metric_evidence(self, company_id: int) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(MarketMetric)
            .where(MarketMetric.company_id == company_id)
            .order_by(MarketMetric.metric_date.desc())
            .limit(10)
        )
        metrics = result.scalars().all()
        return [
            {
                "metric": m.metric_name,
                "value": m.metric_value,
                "date": m.metric_date.isoformat(),
                "components": m.components,
            }
            for m in metrics
        ]

    async def _document_evidence(self, company_id: int) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=30)
        result = await self.db.execute(
            select(Document, Company, Source)
            .join(Company, Document.company_id == Company.id)
            .join(Source, Document.source_id == Source.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= since,
            )
            .order_by(Document.collected_at.desc())
            .limit(10)
        )
        rows = result.all()
        return [
            {
                "company": r.Company.name,
                "title": r.Document.title or "Untitled",
                "url": r.Document.url,
                "source": r.Source.name,
                "publication_date": r.Document.published_at.isoformat() if r.Document.published_at else "Unknown",
                "text_excerpt": (r.Document.content[:300] + "...") if r.Document.content and len(r.Document.content) > 300 else (r.Document.content or ""),
                "collection_date": r.Document.collected_at.isoformat() if r.Document.collected_at else None,
                "evidence_type": r.Document.document_type or "web_page",
            }
            for r in rows
        ]
