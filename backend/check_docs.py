import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.session import async_session_factory
from app.models.document import Document
from app.models.company import Company
from sqlalchemy import select, func

async def main():
    async with async_session_factory() as session:
        # Get companies
        res = await session.execute(select(Company))
        companies = res.scalars().all()
        
        for comp in companies:
            if comp.id not in [22, 23, 24]:
                continue
            
            # Count total docs
            res = await session.execute(select(func.count()).select_from(Document).where(Document.company_id == comp.id))
            total_docs = res.scalar()
            
            # Count docs with published_at
            res = await session.execute(select(func.count()).select_from(Document).where(Document.company_id == comp.id, Document.published_at.isnot(None)))
            dated_docs = res.scalar()
            
            # Count historical docs (older than 7 days)
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            res = await session.execute(select(func.count()).select_from(Document).where(Document.company_id == comp.id, Document.published_at < seven_days_ago))
            hist_docs = res.scalar()
            
            # Count total docs older than 7 days (including None if they were crawled 7 days ago - wait, created_at?)
            res = await session.execute(select(func.count()).select_from(Document).where(Document.company_id == comp.id, Document.created_at < seven_days_ago))
            old_created_docs = res.scalar()
            
            print(f"Company {comp.name} ({comp.id}):")
            print(f"  Total docs: {total_docs}")
            print(f"  Docs with published_at: {dated_docs}")
            print(f"  Docs with published_at > 7 days ago: {hist_docs}")
            print(f"  Docs with created_at > 7 days ago: {old_created_docs}")

if __name__ == "__main__":
    asyncio.run(main())
