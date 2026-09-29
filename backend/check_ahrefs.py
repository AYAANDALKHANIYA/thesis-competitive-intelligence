import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from pprint import pprint

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT content, title FROM documents WHERE company_id = (SELECT id FROM companies WHERE name = 'Ahrefs')"))
        docs = res.fetchall()
        for d in docs:
            c = (d.content or '').lower()
            if 'marketing pros' in c:
                idx = c.find('marketing pros')
                print("FOUND marketing pros at", idx)
                print("CONTEXT:", repr(c[max(0, idx-10):idx+20]))
            if '000' in c:
                idx = c.find('000')
                print("FOUND 000 at", idx)
                print("CONTEXT:", repr(c[max(0, idx-10):idx+20]))

if __name__ == "__main__":
    asyncio.run(main())
