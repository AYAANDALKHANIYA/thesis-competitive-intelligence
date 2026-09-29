"""Topic and DocumentTopic ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document import Document


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic_key: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    coherence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    document_topics: Mapped[List["DocumentTopic"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_topics_model_version", "model_version"),
        Index("ix_topics_topic_key", "topic_key"),
    )


class DocumentTopic(Base):
    __tablename__ = "document_topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    probability: Mapped[float] = mapped_column(Float, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="document_topics")
    topic: Mapped["Topic"] = relationship(back_populates="document_topics")

    __table_args__ = (
        Index("ix_document_topics_document_id", "document_id"),
        Index("ix_document_topics_topic_id", "topic_id"),
    )
