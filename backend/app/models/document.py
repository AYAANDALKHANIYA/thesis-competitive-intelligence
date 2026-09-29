"""Document and DocumentVersion ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.embedding import Embedding
    from app.models.entity import Entity
    from app.models.sentiment import SentimentResult
    from app.models.source import Source
    from app.models.topic import DocumentTopic


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_processed: Mapped[bool] = mapped_column(default=False)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="documents")
    source: Mapped["Source"] = relationship(back_populates="documents")
    sentiment_results: Mapped[List["SentimentResult"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    entities: Mapped[List["Entity"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    document_topics: Mapped[List["DocumentTopic"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["Embedding"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    versions: Mapped[List["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("url", "company_id", name="uq_document_url_company"),
        Index("ix_documents_company_id", "company_id"),
        Index("ix_documents_source_id", "source_id"),
        Index("ix_documents_content_hash", "content_hash"),
        Index("ix_documents_published_at", "published_at"),
        Index("ix_documents_is_processed", "is_processed"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} url={self.url[:60]!r}>"


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    document: Mapped["Document"] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint(
            "document_id", "version_number", name="uq_doc_version_number"
        ),
    )
