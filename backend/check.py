import asyncio
import sys
sys.path.insert(0, '.')
from app.db.session import async_session_factory
from sqlalchemy import text

async def test():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT name FROM companies WHERE name IN ('Semrush', 'Ahrefs', 'Moz')"))
        print([row[0] for row in res.fetchall()])

asyncio.run(test())
