"""
Emerging signal detection — identifies accelerating topics and unusual activity.

Uses configurable minimum thresholds to prevent noise.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.document import Document
from app.models.entity import Entity
from app.models.sentiment import SentimentResult
from app.models.topic import DocumentTopic, Topic

logger = get_logger(__name__)


class EmergingSignalService:
    """Detects emerging signals: accelerating topics, sentiment shifts, unusual activity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    async def detect_signals(
        self, company_id: int
    ) -> List[Dict[str, Any]]:
        """Detect all types of emerging signals for a company."""
        signals: List[Dict[str, Any]] = []

        topic_signals = await self._detect_topic_signals(company_id)
        signals.extend(topic_signals)

        entity_signals = await self._detect_entity_signals(company_id)
        signals.extend(entity_signals)

        sentiment_signals = await self._detect_sentiment_shifts(company_id)
        signals.extend(sentiment_signals)

        # Sort by growth rate / confidence
        signals.sort(key=lambda s: s.get("growth_rate", 0), reverse=True)
        return signals

    async def _detect_topic_signals(
        self, company_id: int
    ) -> List[Dict[str, Any]]:
        """Detect topics with accelerating mention volume."""
        lookback = self.settings.SIGNAL_LOOKBACK_DAYS
        min_mentions = self.settings.SIGNAL_MIN_MENTIONS
        growth_threshold = self.settings.SIGNAL_GROWTH_THRESHOLD

        now = datetime.now(timezone.utc)
        recent_start = now - timedelta(days=lookback // 2)
        historical_start = now - timedelta(days=lookback)

        # Recent topic counts
        recent = await self.db.execute(
            select(
                Topic.id, Topic.name,
                func.count(DocumentTopic.id).label("count"),
            )
            .join(DocumentTopic, Topic.id == DocumentTopic.topic_id)
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= recent_start,
            )
            .group_by(Topic.id, Topic.name)
        )
        recent_data = {row.id: {"name": row.name, "count": row.count} for row in recent.all()}

        # Historical topic counts
        historical = await self.db.execute(
            select(
                Topic.id,
                func.count(DocumentTopic.id).label("count"),
            )
            .join(DocumentTopic, Topic.id == DocumentTopic.topic_id)
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= historical_start,
                Document.collected_at < recent_start,
            )
            .group_by(Topic.id)
        )
        historical_data = {row.id: row.count for row in historical.all()}

        signals = []
        for topic_id, data in recent_data.items():
            recent_count = data["count"]
            hist_count = historical_data.get(topic_id, 0)

            if recent_count < min_mentions:
                continue

            if hist_count > 0:
                growth_rate = (recent_count - hist_count) / hist_count
            elif recent_count >= min_mentions:
                growth_rate = 2.0  # New topic with significant activity
            else:
                continue

            if growth_rate >= growth_threshold:
                confidence = min(1.0, recent_count / (min_mentions * 3))
                signals.append({
                    "signal_type": "topic_acceleration",
                    "topic": data["name"],
                    "entity": None,
                    "current_mentions": recent_count,
                    "previous_mentions": hist_count,
                    "growth_rate": round(growth_rate, 4),
                    "sentiment_shift": None,
                    "confidence": round(confidence, 4),
                    "evidence": [],
                    "detected_at": now.isoformat(),
                })

        return signals

    async def _detect_entity_signals(
        self, company_id: int
    ) -> List[Dict[str, Any]]:
        """Detect entities with rapidly increasing mentions."""
        lookback = self.settings.SIGNAL_LOOKBACK_DAYS
        min_mentions = self.settings.SIGNAL_MIN_MENTIONS
        now = datetime.now(timezone.utc)
        recent_start = now - timedelta(days=lookback // 2)
        historical_start = now - timedelta(days=lookback)

        # Recent entity counts
        recent = await self.db.execute(
            select(
                Entity.entity_text,
                Entity.entity_type,
                func.count(Entity.id).label("count"),
            )
            .join(Document, Entity.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= recent_start,
                Entity.entity_type.in_(["ORG", "PRODUCT"]),
            )
            .group_by(Entity.entity_text, Entity.entity_type)
            .having(func.count(Entity.id) >= min_mentions)
        )
        recent_data = {
            (row.entity_text, row.entity_type): row.count for row in recent.all()
        }

        # Historical entity counts
        historical = await self.db.execute(
            select(
                Entity.entity_text,
                Entity.entity_type,
                func.count(Entity.id).label("count"),
            )
            .join(Document, Entity.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= historical_start,
                Document.collected_at < recent_start,
                Entity.entity_type.in_(["ORG", "PRODUCT"]),
            )
            .group_by(Entity.entity_text, Entity.entity_type)
        )
        historical_data = {
            (row.entity_text, row.entity_type): row.count for row in historical.all()
        }

        signals = []
        for (text, etype), recent_count in recent_data.items():
            hist_count = historical_data.get((text, etype), 0)
            if hist_count > 0:
                growth_rate = (recent_count - hist_count) / hist_count
            else:
                growth_rate = 2.0

            if growth_rate >= self.settings.SIGNAL_GROWTH_THRESHOLD:
                signals.append({
                    "signal_type": "entity_acceleration",
                    "topic": None,
                    "entity": f"{text} ({etype})",
                    "current_mentions": recent_count,
                    "previous_mentions": hist_count,
                    "growth_rate": round(growth_rate, 4),
                    "sentiment_shift": None,
                    "confidence": min(1.0, recent_count / (min_mentions * 3)),
                    "evidence": [],
                    "detected_at": now.isoformat(),
                })

        return signals

    async def _detect_sentiment_shifts(
        self, company_id: int
    ) -> List[Dict[str, Any]]:
        """Detect significant sentiment shifts."""
        lookback = self.settings.SIGNAL_LOOKBACK_DAYS
        now = datetime.now(timezone.utc)
        recent_start = now - timedelta(days=lookback // 2)
        historical_start = now - timedelta(days=lookback)

        # Recent avg sentiment
        recent_result = await self.db.execute(
            select(func.avg(SentimentResult.score), func.count(SentimentResult.id))
            .join(Document, SentimentResult.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= recent_start,
            )
        )
        recent_row = recent_result.one_or_none()
        recent_avg = float(recent_row[0] or 0) if recent_row else 0
        recent_count = int(recent_row[1] or 0) if recent_row else 0

        # Historical avg sentiment
        hist_result = await self.db.execute(
            select(func.avg(SentimentResult.score), func.count(SentimentResult.id))
            .join(Document, SentimentResult.document_id == Document.id)
            .where(
                Document.company_id == company_id,
                Document.collected_at >= historical_start,
                Document.collected_at < recent_start,
            )
        )
        hist_row = hist_result.one_or_none()
        hist_avg = float(hist_row[0] or 0) if hist_row else 0
        hist_count = int(hist_row[1] or 0) if hist_row else 0

        signals = []
        if recent_count >= self.settings.SIGNAL_MIN_MENTIONS and hist_count >= self.settings.SIGNAL_MIN_MENTIONS:
            shift = recent_avg - hist_avg
            if abs(shift) >= 0.15:  # Significant shift threshold
                signals.append({
                    "signal_type": "sentiment_shift",
                    "topic": None,
                    "entity": None,
                    "current_mentions": recent_count,
                    "previous_mentions": hist_count,
                    "growth_rate": 0,
                    "sentiment_shift": round(shift, 4),
                    "confidence": min(1.0, min(recent_count, hist_count) / 20),
                    "evidence": [],
                    "detected_at": now.isoformat(),
                })

        return signals
