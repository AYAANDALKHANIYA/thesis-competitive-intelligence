"""Insight ORM model — LLM-generated intelligence with evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.analysis import AnalysisRun


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True
    )
    insight_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # competitive, sentiment, trend, emerging_signal, market_overview
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # low, medium, high, critical
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    input_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    company: Mapped["Company"] = relationship(back_populates="insights")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship()

    __table_args__ = (
        Index("ix_insights_company", "company_id"),
        Index("ix_insights_type", "insight_type"),
        Index("ix_insights_input_hash", "input_hash"),
    )
