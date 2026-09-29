import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.connect() as conn:
        c_res = await conn.execute(text("SELECT id FROM companies WHERE name = 'Semrush'"))
        cid = c_res.scalar()
        doc_res = await conn.execute(text("SELECT id, url, length(content) FROM documents WHERE company_id = :cid"), {"cid": cid})
        for row in doc_res:
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
