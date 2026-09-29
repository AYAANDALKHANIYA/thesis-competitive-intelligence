"""Analysis run ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class AnalysisRun(Base, TimestampMixin):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="QUEUED"
    )  # QUEUED, RUNNING, COMPLETED, PARTIAL, FAILED
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    company: Mapped["Company"] = relationship()
    competitors: Mapped[List["AnalysisCompetitor"]] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_analysis_runs_company", "company_id"),
        Index("ix_analysis_runs_status", "status"),
    )


class AnalysisCompetitor(Base):
    __tablename__ = "analysis_competitors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False
    )
    competitor_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    analysis_run: Mapped["AnalysisRun"] = relationship(back_populates="competitors")
    competitor_company: Mapped["Company"] = relationship()

    __table_args__ = (
        Index("ix_analysis_competitors_run", "analysis_run_id"),
        Index("ix_analysis_competitors_company", "competitor_id"),
    )
