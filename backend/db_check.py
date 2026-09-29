import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def check_db():
    async with async_session_maker() as session:
        res = await session.execute(text('SELECT count(*) FROM companies;'))
        print('Companies:', res.scalar())
        res = await session.execute(text('SELECT count(*) FROM competitors;'))
        print('Competitors:', res.scalar())
        res = await session.execute(text('SELECT count(*) FROM documents;'))
        print('Documents:', res.scalar())

asyncio.run(check_db())
