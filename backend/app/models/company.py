"""Company ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Index, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.ingestion_run import IngestionRun
    from app.models.insight import Insight
    from app.models.metric import MarketMetric
    from app.models.prediction import Prediction

from app.models.competitor import Competitor


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sec_cik: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    competitors_as_primary: Mapped[List["Competitor"]] = relationship(
        primaryjoin="Company.id == Competitor.company_id",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    competitors_as_secondary: Mapped[List["Competitor"]] = relationship(
        primaryjoin="Company.id == Competitor.competitor_id",
        back_populates="competitor_company",
    )
    market_metrics: Mapped[List["MarketMetric"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    ingestion_runs: Mapped[List["IngestionRun"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    insights: Mapped[List["Insight"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_companies_domain", "domain"),
        Index("ix_companies_ticker", "ticker"),
        Index("ix_companies_name", "name"),
        Index("ix_companies_single_primary", "is_primary", unique=True, postgresql_where=(is_primary == True)),
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r}>"
