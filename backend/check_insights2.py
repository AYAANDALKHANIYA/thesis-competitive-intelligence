import asyncio
import os
import sys

# Add the backend dir to sys.path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.session import async_session_factory
from app.models.insight import Insight
from sqlalchemy import select

async def main():
    async with async_session_factory() as session:
        res = await session.execute(select(Insight))
        insights = res.scalars().all()
        for i in insights:
            print(f"ID: {i.id}, Type: {i.insight_type}, Company: {i.company_id}, Analysis: {i.analysis_id}")
            print(f"Summary: {i.summary[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
