"""Embedding ORM model using pgvector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback: store as a plain array if pgvector is not installed
    from sqlalchemy.dialects.postgresql import ARRAY
    from sqlalchemy import Float as _Float

    def Vector(dim: int):  # noqa: N802
        return ARRAY(_Float)


if TYPE_CHECKING:
    from app.models.document import Document

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 dimension


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    document: Mapped["Document"] = relationship(back_populates="embeddings")

    __table_args__ = (Index("ix_embeddings_document_id", "document_id"),)
