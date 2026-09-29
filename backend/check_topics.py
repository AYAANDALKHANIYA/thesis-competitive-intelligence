import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text('SELECT COUNT(*) FROM topics'))
        print('Topics count:', res.scalar())
        res = await conn.execute(text('SELECT COUNT(*) FROM document_topics'))
        print('DocTopics count:', res.scalar())

if __name__ == "__main__":
    asyncio.run(main())
