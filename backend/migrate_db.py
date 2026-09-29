import asyncio
import sys
sys.path.insert(0, '.')
from app.db.session import async_session_factory
from sqlalchemy import text

async def apply_migrations():
    async with async_session_factory() as session:
        try:
            # Check if columns exist first
            # market_metrics
            await session.execute(text("ALTER TABLE market_metrics ADD COLUMN IF NOT EXISTS analysis_id INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE"))
            # insights
            await session.execute(text("ALTER TABLE insights ADD COLUMN IF NOT EXISTS analysis_id INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE"))
            # sentiment_results
            await session.execute(text("ALTER TABLE sentiment_results ADD COLUMN IF NOT EXISTS analysis_id INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE"))
            
            await session.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
            await session.rollback()

asyncio.run(apply_migrations())
