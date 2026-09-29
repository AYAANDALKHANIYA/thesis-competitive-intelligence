"""Source ORM model — represents a data source type/configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.ingestion_run import IngestionRun
    from app.models.source_state import SourceState


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # website, rss, gdelt, sec
    base_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=30)
    crawl_delay_seconds: Mapped[float] = mapped_column(Float, default=2.0)
    config: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # JSONB for source-specific settings

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    source_states: Mapped[List["SourceState"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    ingestion_runs: Mapped[List["IngestionRun"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sources_source_type", "source_type"),
        Index("ix_sources_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id} name={self.name!r} type={self.source_type!r}>"
