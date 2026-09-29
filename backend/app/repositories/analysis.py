"""Analysis repository — sentiment, topics, entities, embeddings."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import Embedding
from app.models.entity import Entity
from app.models.sentiment import SentimentResult
from app.models.topic import DocumentTopic, Topic


class AnalysisRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Sentiment ────────────────────────────────────────────────────────

    async def create_sentiment(self, **kwargs) -> SentimentResult:
        result = SentimentResult(**kwargs)
        self.db.add(result)
        await self.db.flush()
        return result

    async def get_sentiment_by_document(self, document_id: int) -> Optional[SentimentResult]:
        result = await self.db.execute(
            select(SentimentResult)
            .where(SentimentResult.document_id == document_id)
            .order_by(SentimentResult.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_sentiments_by_company(
        self, company_id: int, limit: int = 500
    ) -> List[SentimentResult]:
        from app.models.document import Document

        result = await self.db.execute(
            select(SentimentResult)
            .join(Document, SentimentResult.document_id == Document.id)
            .where(Document.company_id == company_id)
            .order_by(SentimentResult.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_sentiments(self) -> int:
        result = await self.db.execute(select(func.count(SentimentResult.id)))
        return result.scalar() or 0

    # ── Topics ───────────────────────────────────────────────────────────

    async def create_topic(self, **kwargs) -> Topic:
        topic = Topic(**kwargs)
        self.db.add(topic)
        await self.db.flush()
        await self.db.refresh(topic)
        return topic

    async def create_document_topic(self, **kwargs) -> DocumentTopic:
        dt = DocumentTopic(**kwargs)
        self.db.add(dt)
        await self.db.flush()
        return dt

    async def get_topics(self, model_version: Optional[str] = None) -> List[Topic]:
        query = select(Topic)
        if model_version:
            query = query.where(Topic.model_version == model_version)
        result = await self.db.execute(query.order_by(Topic.document_count.desc()))
        return list(result.scalars().all())

    async def get_topics_by_company(
        self, company_id: int, limit: int = 50
    ) -> List[Topic]:
        from app.models.document import Document

        result = await self.db.execute(
            select(Topic)
            .join(DocumentTopic, Topic.id == DocumentTopic.topic_id)
            .join(Document, DocumentTopic.document_id == Document.id)
            .where(Document.company_id == company_id)
            .group_by(Topic.id)
            .order_by(func.count(DocumentTopic.id).desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_topic_by_key_and_version(
        self, topic_key: int, model_version: str
    ) -> Optional[Topic]:
        result = await self.db.execute(
            select(Topic).where(
                Topic.topic_key == topic_key,
                Topic.model_version == model_version,
            )
        )
        return result.scalar_one_or_none()

    async def count_topics(self) -> int:
        result = await self.db.execute(select(func.count(Topic.id)))
        return result.scalar() or 0

    # ── Entities ─────────────────────────────────────────────────────────

    async def create_entity(self, **kwargs) -> Entity:
        entity = Entity(**kwargs)
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_entities_by_document(self, document_id: int) -> List[Entity]:
        result = await self.db.execute(
            select(Entity).where(Entity.document_id == document_id)
        )
        return list(result.scalars().all())

    async def get_entities_by_company(
        self, company_id: int, entity_type: Optional[str] = None, limit: int = 100
    ) -> List[Entity]:
        from app.models.document import Document

        query = (
            select(Entity)
            .join(Document, Entity.document_id == Document.id)
            .where(Document.company_id == company_id)
        )
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)
        result = await self.db.execute(query.limit(limit))
        return list(result.scalars().all())

    async def get_entity_summary_by_company(
        self, company_id: int, limit: int = 50
    ) -> list:
        from app.models.document import Document

        result = await self.db.execute(
            select(
                Entity.entity_text,
                Entity.entity_type,
                func.count(Entity.id).label("mention_count"),
            )
            .join(Document, Entity.document_id == Document.id)
            .where(Document.company_id == company_id)
            .group_by(Entity.entity_text, Entity.entity_type)
            .order_by(func.count(Entity.id).desc())
            .limit(limit)
        )
        return list(result.all())

    async def count_entities(self) -> int:
        result = await self.db.execute(select(func.count(Entity.id)))
        return result.scalar() or 0

    # ── Embeddings ───────────────────────────────────────────────────────

    async def create_embedding(self, **kwargs) -> Embedding:
        emb = Embedding(**kwargs)
        self.db.add(emb)
        await self.db.flush()
        return emb

    async def get_embedding_by_document(self, document_id: int) -> Optional[Embedding]:
        result = await self.db.execute(
            select(Embedding).where(Embedding.document_id == document_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def has_embedding(self, document_id: int) -> bool:
        result = await self.db.execute(
            select(func.count(Embedding.id)).where(
                Embedding.document_id == document_id
            )
        )
        return (result.scalar() or 0) > 0
