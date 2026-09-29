from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    source = Column(String(50), nullable=False) # e.g., 'G2', 'Capterra'
    rating = Column(Float, nullable=False)
    review_text = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    review_date = Column(DateTime, nullable=True)
    source_url = Column(String(2000), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
