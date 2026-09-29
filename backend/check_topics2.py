import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.begin() as conn:
        res = await conn.execute(text('SELECT name FROM topics'))
        print([r[0] for r in res.fetchall()])

if __name__ == "__main__":
    asyncio.run(main())
