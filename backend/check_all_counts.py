import asyncio
from app.db.session import async_session_factory
from sqlalchemy import text

async def check_all():
    async with async_session_factory() as session:
        # Get tables
        res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [r[0] for r in res.fetchall()]
        
        print("Database Table Row Counts:")
        for table in tables:
            res = await session.execute(text(f"SELECT count(*) FROM {table};"))
            count = res.scalar()
            print(f"- {table}: {count}")

asyncio.run(check_all())
