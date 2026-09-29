import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.services.nlp.topics import extract_deterministic_topics

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL)

async def main():
    async with engine.connect() as conn:
        c_res = await conn.execute(text("SELECT id FROM companies WHERE name = 'Semrush'"))
        cid = c_res.scalar()
        doc_res = await conn.execute(text("SELECT content FROM documents WHERE company_id = :cid"), {"cid": cid})
        documents = [row[0] for row in doc_res if row[0]]
        
        print(f"Found {len(documents)} documents with content.")
        res = extract_deterministic_topics(documents)
        print("Topic result:", res)

if __name__ == "__main__":
    asyncio.run(main())
