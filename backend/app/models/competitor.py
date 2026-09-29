"""Competitor association ORM model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    competitor_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[Optional[str]] = mapped_column(
        String(50), default="direct", nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    company: Mapped["Company"] = relationship(
        foreign_keys=[company_id], back_populates="competitors_as_primary"
    )
    competitor_company: Mapped["Company"] = relationship(
        foreign_keys=[competitor_id], back_populates="competitors_as_secondary"
    )

    __table_args__ = (
        UniqueConstraint("company_id", "competitor_id", name="uq_competitor_pair"),
    )
