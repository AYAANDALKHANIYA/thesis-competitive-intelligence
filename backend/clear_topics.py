import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.begin() as conn:
        await conn.execute(text('DELETE FROM document_topics'))
        await conn.execute(text('DELETE FROM topics'))
        print('Topics cleared')

if __name__ == "__main__":
    asyncio.run(main())
