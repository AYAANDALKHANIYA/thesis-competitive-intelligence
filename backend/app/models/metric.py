"""Market metric ORM model."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.analysis import AnalysisRun


class MarketMetric(Base):
    __tablename__ = "market_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    components: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    company: Mapped["Company"] = relationship(back_populates="market_metrics")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship()

    __table_args__ = (
        Index("ix_market_metrics_company_date", "company_id", "metric_date"),
        Index("ix_market_metrics_name", "metric_name"),
    )
