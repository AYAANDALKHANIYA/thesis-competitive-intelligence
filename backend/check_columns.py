import asyncio
import sys
sys.path.insert(0, '.')
from app.db.session import async_session_factory
from sqlalchemy import text

async def check():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'market_metrics'"))
        print('market_metrics:', [r[0] for r in res.fetchall()])
        res2 = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'insights'"))
        print('insights:', [r[0] for r in res2.fetchall()])
        res3 = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'topics'"))
        print('topics:', [r[0] for r in res3.fetchall()])

asyncio.run(check())
