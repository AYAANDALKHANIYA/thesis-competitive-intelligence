import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.review import Review
from app.models.company import Company
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

class ReviewResponse(BaseModel):
    id: int
    company_id: int
    source: str
    rating: float
    review_text: Optional[str] = None
    category: Optional[str] = None
    source_url: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True

@router.get("/{company_id}", response_model=List[ReviewResponse])
async def get_reviews(company_id: int, db: AsyncSession = Depends(get_db)):
    """Get all reviews for a company."""
    result = await db.execute(select(Review).where(Review.company_id == company_id))
    return result.scalars().all()

@router.post("/import/{company_id}")
async def import_reviews(
    company_id: int, 
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import permitted research data for reviews (CSV or JSON)."""
    # Verify company exists
    res = await db.execute(select(Company).where(Company.id == company_id))
    if not res.scalars().first():
        raise HTTPException(status_code=404, detail="Company not found")
        
    content = await file.read()
    filename = file.filename.lower()
    
    reviews_to_add = []
    
    try:
        if filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            for item in data:
                reviews_to_add.append(Review(
                    company_id=company_id,
                    source=item.get("source", "Imported"),
                    rating=float(item.get("rating", 0.0)),
                    review_text=item.get("review_text"),
                    category=item.get("category"),
                    source_url=item.get("source_url")
                ))
        elif filename.endswith(".csv"):
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                reviews_to_add.append(Review(
                    company_id=company_id,
                    source=row.get("source", "Imported"),
                    rating=float(row.get("rating", 0.0)),
                    review_text=row.get("review_text"),
                    category=row.get("category"),
                    source_url=row.get("source_url")
                ))
        else:
            raise HTTPException(status_code=400, detail="Only JSON and CSV files are supported")
            
        if reviews_to_add:
            db.add_all(reviews_to_add)
            await db.commit()
            
        return {"status": "success", "imported_count": len(reviews_to_add)}
        
    except Exception as e:
        logger.error(f"Failed to import reviews: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse or import data: {str(e)}")
